"""Autonomous campaign runner — continuous loop for DMs, replies, and reminders.

Usage:
    python run.py                    # live autonomous loop
    python run.py --dry-run          # simulate without Instagram API calls
    python run.py --once             # run one cycle then exit
    python run.py --interval 300     # loop every 5 minutes (default: 300)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import AGENTS_DB_PATH, LOG_LEVEL, MAX_DMS_PER_DAY
from database import Database
from tools.database_tools import set_database


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )
    logger.add(
        "data/run.log",
        level=LOG_LEVEL,
        rotation="10 MB",
        retention="1 week",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


REMINDER_MESSAGES = [
    "Hey! Just following up on our collaboration offer. Let us know if you're interested!",
    "Hi! We'd love to hear back from you about the paid collab. No pressure — just checking in!",
    "Hey there! Our offer is still open if you're interested. Feel free to ask any questions!",
]


def send_reminders(db: Database, dry_run: bool = False) -> dict:
    """Send follow-up reminders to stale conversations."""
    stale = db.get_stale_conversations(days=3, max_reminders=2)
    logger.info("Found {} stale conversations needing reminders", len(stale))

    sent = 0
    failed = 0

    for conv in stale:
        conv_id = conv["id"]
        username = conv["creator_username"]
        thread_id = conv.get("thread_id")
        reminder_idx = conv.get("reminder_count", 0)

        if not thread_id:
            logger.warning("  Skipping @{} — no thread_id", username)
            continue

        message = REMINDER_MESSAGES[min(reminder_idx, len(REMINDER_MESSAGES) - 1)]

        if dry_run:
            logger.info("  [DRY-RUN] Would send reminder #{} to @{}: {}",
                        reminder_idx + 1, username, message[:50] + "...")
            db.increment_reminder_count(conv_id)
            sent += 1
            continue

        from ig_client import get_ig_client
        from tools.database_tools import log_dm

        ig_client = get_ig_client()
        result = ig_client.send_dm_to_thread(thread_id, message)

        if result.get("success"):
            logger.info("  Reminder #{} sent to @{}", reminder_idx + 1, username)
            log_dm(
                creator_username=username,
                thread_id=thread_id,
                message_text=message,
                direction="sent",
            )
            db.increment_reminder_count(conv_id)
            sent += 1
        else:
            logger.error("  Reminder FAILED for @{}: {}", username, result.get("error"))
            failed += 1

    return {"checked": len(stale), "sent": sent, "failed": failed}


def run_reply_cycle(db: Database, dry_run: bool = False) -> dict:
    """Run the check_replies cycle — reads new replies, processes with Negotiator."""
    from check_replies import get_candidate_conversations, check_for_new_replies, run_negotiator, run_contract_agent, check_dm_quota_before_send

    candidates = get_candidate_conversations(db)
    logger.info("Found {} candidate conversations to check for replies", len(candidates))

    checked = 0
    new_replies = 0
    counter_offers_sent = 0
    accepted = 0
    contracts_generated = 0

    for conv in candidates:
        checked += 1
        conv_id = conv["id"]
        username = conv["creator_username"]
        logger.info("  [{}/{}] Checking @{}", checked, len(candidates), username)

        current_count = check_for_new_replies(conv, dry_run=dry_run)
        last_count = conv.get("last_message_count", 0)

        if current_count <= last_count:
            continue

        new_replies += 1
        logger.info("    New reply from @{} ({} > {})", username, current_count, last_count)

        negotiator_result = run_negotiator(conv, dry_run=dry_run)
        action = negotiator_result.get("action", "wait")
        logger.info("    Negotiator: {} for @{}", action, username)

        from tools.database_tools import update_conversation_negotiation, update_conversation_status

        negotiation_history = json.dumps(negotiator_result)
        update_conversation_negotiation(
            conversation_id=conv_id,
            negotiation_history=negotiation_history,
            last_message_count=current_count,
        )

        if action == "accept":
            accepted += 1
            agreed_rate = negotiator_result.get("agreed_rate")
            logger.info("    Deal accepted! Rate: {}", agreed_rate)

            contract_id = run_contract_agent(conv, agreed_rate, dry_run=dry_run)
            if contract_id:
                contracts_generated += 1
                logger.info("    Contract generated: id={}", contract_id)

            update_conversation_status(
                conversation_id=conv_id,
                status="accepted",
                agreed_rate=agreed_rate,
            )

        elif action == "counter":
            counter_offers_sent += 1
            response_msg = negotiator_result.get("response")
            if response_msg and not dry_run:
                thread_id = conv.get("thread_id")
                if thread_id:
                    from ig_client import get_ig_client
                    from tools.database_tools import log_dm

                    ig_client = get_ig_client()
                    send_result = ig_client.send_dm_to_thread(thread_id, response_msg)
                    if send_result.get("success"):
                        logger.info("    Counter-offer sent to @{}", username)
                        log_dm(
                            creator_username=username,
                            thread_id=thread_id,
                            message_text=response_msg,
                            direction="sent",
                        )
                    else:
                        logger.error("    Counter-offer FAILED: {}", send_result.get("error"))
            else:
                logger.info("    Counter-offer queued (dry-run)")

        if not dry_run:
            from tools.database_tools import log_dm
            thread_id = conv.get("thread_id", "")
            log_dm(
                creator_username=username,
                thread_id=thread_id,
                message_text=f"<{current_count - last_count} new message(s)>",
                direction="received",
            )

    return {
        "checked": checked,
        "new_replies": new_replies,
        "counter_offers_sent": counter_offers_sent,
        "accepted": accepted,
        "contracts_generated": contracts_generated,
    }


def run_cycle(dry_run: bool = False) -> dict:
    """Run one full autonomous cycle: replies → reminders."""
    db = Database(AGENTS_DB_PATH)
    db.init_db()
    set_database(db)

    if not dry_run:
        from ig_client import get_ig_client
        client = get_ig_client()
        client.login()
        logger.info("Instagram client logged in")

    logger.info("─" * 40)
    logger.info("PHASE 1: Check replies & process negotiations")
    logger.info("─" * 40)
    reply_summary = run_reply_cycle(db, dry_run=dry_run)

    logger.info("─" * 40)
    logger.info("PHASE 2: Send reminders for stale conversations")
    logger.info("─" * 40)
    reminder_summary = send_reminders(db, dry_run=dry_run)

    cycle_summary = {
        "timestamp": datetime.now().isoformat(),
        "replies": reply_summary,
        "reminders": reminder_summary,
    }

    logger.info("─" * 40)
    logger.info("CYCLE COMPLETE: {}", json.dumps(cycle_summary, default=str))
    logger.info("─" * 40)

    return cycle_summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Autonomous campaign runner")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Simulate without Instagram API")
    parser.add_argument("--once", action="store_true", default=False, help="Run one cycle then exit")
    parser.add_argument("--interval", type=int, default=300, help="Loop interval in seconds (default: 300)")
    args = parser.parse_args(argv)

    setup_logging()

    logger.info("=" * 50)
    logger.info("Autonomous Campaign Runner")
    logger.info("Mode: {}", "DRY-RUN" if args.dry_run else "LIVE")
    logger.info("Interval: {}s", args.interval)
    logger.info("Run once: {}", args.once)
    logger.info("=" * 50)

    if args.once:
        run_cycle(dry_run=args.dry_run)
        return

    cycle_num = 0
    while True:
        cycle_num += 1
        logger.info("Starting cycle #{}", cycle_num)
        try:
            run_cycle(dry_run=args.dry_run)
        except Exception as exc:
            logger.error("Cycle #{} failed: {}", cycle_num, exc)

        logger.info("Sleeping {}s until next cycle...", args.interval)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
