#!/usr/bin/env python3
"""Check for new replies in Instagram DM threads and process them.

Scheduled task that:
  1. Queries conversations with status in (outreach_sent, replied) that have
     a thread_id or last_message_count > 0.
  2. Reads the actual thread messages via Instagram API.
  3. If new messages exist (count > last_message_count), runs the Negotiator
     agent to decide the next action (accept / counter / wait / escalate).
  4. If action='accept', runs the Contract agent to generate and save a contract.
  5. Logs received messages to the dm_log table.

Usage:
    python check_replies.py [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from loguru import logger

from config import AGENTS_DB_PATH, LOG_LEVEL
from database import Database
from tools.database_tools import set_database

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build and parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Check for new replies in Instagram DM threads and process them "
            "via the Negotiator and Contract agents."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Do not call Instagram APIs; use last-known data only.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of conversations to check (default: no limit).",
    )

    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def setup_logging() -> None:
    """Configure loguru: stderr + ``data/run.log``, level from ``LOG_LEVEL``."""
    logger.remove()

    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    logger.add(
        "data/run.log",
        level=LOG_LEVEL,
        rotation="10 MB",
        retention="1 week",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def get_candidate_conversations(
    db: Database, limit: Optional[int] = None
) -> list[dict]:
    """Fetch conversations with status in (outreach_sent, replied) that have
    a thread_id or last_message_count > 0."""
    all_convos = db.get_conversations_by_statuses(("outreach_sent", "replied"))

    candidates = [
        c
        for c in all_convos
        if c.get("thread_id") or (c.get("last_message_count") or 0) > 0
    ]

    if limit is not None and limit > 0:
        candidates = candidates[:limit]

    return candidates


def check_for_new_replies(conversation: dict, dry_run: bool) -> int:
    """Return the current message count for a conversation's thread.

    In dry-run mode the Instagram API is never called and the stored
    ``last_message_count`` is returned as-is.
    """
    if dry_run:
        return conversation.get("last_message_count", 0)

    thread_id = conversation.get("thread_id")
    if not thread_id:
        return conversation.get("last_message_count", 0)

    from tools.instagram_tools import read_thread_messages

    messages = read_thread_messages(thread_id=thread_id, amount=50)
    return len(messages)


def check_dm_quota_before_send() -> bool:
    """Return True if the DM quota allows sending another message today."""
    from tools.database_tools import check_dm_quota

    sent_today, max_daily = check_dm_quota()
    return sent_today < max_daily


def run_negotiator(conversation: dict, dry_run: bool) -> dict:
    """Run the Negotiator agent on a conversation and return its decision.

    Expected return shape::

        {
            "action": "accept | counter | wait | escalate | give_up",
            "response": "<message in creator's language or null>",
            "agreed_rate": <number or null>,
            "round_number": <int>,
            "status": "open | accepted | escalated | closed | give_up"
        }
    """
    if dry_run:
        return {
            "action": "wait",
            "response": None,
            "agreed_rate": None,
            "round_number": conversation.get("last_message_count", 0) + 1,
            "status": "open",
        }

    # Respect DM quota before sending any counter-offer
    if not check_dm_quota_before_send():
        logger.warning("  DM quota exhausted — negotiator will not send messages")

    from crewai import Crew, Process, Task
    from agents.activate.outreach_manager import get_outreach_manager_agent as get_negotiator_agent

    agent = get_negotiator_agent()

    task = Task(
        description=(
            f"Review the conversation with creator @{conversation['creator_username']} "
            f"(conversation_id={conversation['id']}). "
            f"Read the thread messages and decide on the next action. "
            f"Current status: {conversation.get('status', 'unknown')}. "
            f"Return JSON with action, response, agreed_rate, round_number, status."
        ),
        expected_output=(
            "JSON object with keys: action (accept|counter|wait|escalate|give_up), "
            "response (message text or null), agreed_rate (number or null), "
            "round_number (int), status (open|accepted|escalated|closed|give_up)"
        ),
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    raw = getattr(result, "raw", "{}")

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse negotiator output: %s", raw)
        return {
            "action": "wait",
            "response": None,
            "agreed_rate": None,
            "round_number": 0,
            "status": "open",
        }


def run_contract_agent(
    conversation: dict, agreed_rate: float, dry_run: bool
) -> Optional[int]:
    """Run the Contract agent to generate and save a contract.

    Returns the contract_id or None.
    """
    if dry_run:
        return None

    from crewai import Crew, Process, Task
    from agents.activate.contract_helper import get_contract_helper_agent as get_contract_agent

    agent = get_contract_agent()

    task = Task(
        description=(
            f"Generate a collaboration contract for creator "
            f"@{conversation['creator_username']} "
            f"(conversation_id={conversation['id']}). "
            f"Agreed rate: {agreed_rate}. "
            f"Save the contract and return the contract_id."
        ),
        expected_output="JSON with contract_id and contract details.",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    raw = getattr(result, "raw", "{}")

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(raw)
        return data.get("contract_id")
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse contract output: %s", raw)
        return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Parse args, init DB + Instagram, check replies, print summary."""
    args = parse_args(argv)
    setup_logging()

    logger.info("Starting check_replies")
    logger.info("Dry-run: {}", args.dry_run)
    logger.info("Limit: {}", args.limit)

    # -- Database -----------------------------------------------------------
    db = Database(AGENTS_DB_PATH)
    db.init_db()
    set_database(db)
    logger.info("Database initialised at {}", AGENTS_DB_PATH)

    # -- Instagram client (only when not dry-run) ---------------------------
    if not args.dry_run:
        from ig_client import get_ig_client

        client = get_ig_client()
        client.login()
        logger.info("Instagram client initialised and logged in")

    # -- Get candidate conversations ----------------------------------------
    candidates = get_candidate_conversations(db, limit=args.limit)
    logger.info("Found {} candidate conversations to check", len(candidates))

    # -- Process each conversation ------------------------------------------
    checked = 0
    new_replies = 0
    counter_offers_sent = 0
    accepted = 0
    contracts_generated = 0

    for conv in candidates:
        checked += 1
        conv_id = conv["id"]
        username = conv["creator_username"]
        logger.info(
            "[{}/{}] Checking conversation {} (@{})",
            checked,
            len(candidates),
            conv_id,
            username,
        )

        # Check for new replies
        current_count = check_for_new_replies(conv, dry_run=args.dry_run)
        last_count = conv.get("last_message_count", 0)

        if current_count <= last_count:
            logger.info(
                "  No new replies (count: {} <= {})", current_count, last_count
            )
            continue

        new_replies += 1
        logger.info(
            "  New reply detected! (count: {} > {})", current_count, last_count
        )

        # Run Negotiator
        logger.info("  Running Negotiator agent...")
        negotiator_result = run_negotiator(conv, dry_run=args.dry_run)
        action = negotiator_result.get("action", "wait")
        logger.info("  Negotiator action: {}", action)

        # Update conversation negotiation state
        from tools.database_tools import update_conversation_negotiation

        negotiation_history = json.dumps(negotiator_result)
        update_conversation_negotiation(
            conversation_id=conv_id,
            negotiation_history=negotiation_history,
            last_message_count=current_count,
        )

        # Handle action
        if action == "accept":
            accepted += 1
            agreed_rate = negotiator_result.get("agreed_rate")
            logger.info("  Deal accepted! Rate: {}", agreed_rate)

            # Run Contract agent
            logger.info("  Running Contract agent...")
            contract_id = run_contract_agent(
                conv, agreed_rate, dry_run=args.dry_run
            )
            if contract_id:
                contracts_generated += 1
                logger.info("  Contract generated: id={}", contract_id)

            # Update conversation status to accepted
            from tools.database_tools import update_conversation_status

            update_conversation_status(
                conversation_id=conv_id,
                status="accepted",
                agreed_rate=agreed_rate,
            )

        elif action == "counter":
            counter_offers_sent += 1
            logger.info("  Counter-offer sent")

        # Log received messages (only in live mode)
        if not args.dry_run:
            from tools.database_tools import log_dm

            thread_id = conv.get("thread_id", "")
            log_dm(
                creator_username=username,
                thread_id=thread_id,
                message_text=f"<{current_count - last_count} new message(s)>",
                direction="received",
            )

    # -- Summary output -----------------------------------------------------
    summary = {
        "checked": checked,
        "new_replies": new_replies,
        "counter_offers_sent": counter_offers_sent,
        "accepted": accepted,
        "contracts_generated": contracts_generated,
    }

    summary_json = json.dumps(summary, indent=2, default=str)
    logger.info("=" * 60)
    logger.info("CHECK REPLIES SUMMARY")
    logger.info("=" * 60)
    logger.info("\n{}", summary_json)
    logger.info("=" * 60)

    logger.info("Check replies complete: {}", summary)


if __name__ == "__main__":
    main()
