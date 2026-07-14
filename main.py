"""CLI entry point for the vernacular-creator-agents pipeline.

Usage:
    python main.py "brief text" [--send] [--approve-each] [--max-creators N] [--dry-run]

Default is dry-run. Pass ``--send`` to actually dispatch DMs.
"""

from __future__ import annotations

import argparse
import json
import sys

from loguru import logger

from config import AGENTS_DB_PATH, LOG_LEVEL
from database import Database


# ── Argument parsing ──────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build and parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Vernacular Creator Agents — automated influencer campaign pipeline.",
    )

    parser.add_argument(
        "brief",
        type=str,
        help="Brand brief text describing the campaign requirements.",
    )

    parser.add_argument(
        "--send",
        action="store_true",
        default=False,
        help="Actually dispatch DMs (default: dry-run, no DMs sent).",
    )

    parser.add_argument(
        "--approve-each",
        action="store_true",
        default=False,
        help="Prompt for approval before each DM (only meaningful with --send).",
    )

    parser.add_argument(
        "--max-creators",
        type=int,
        default=10,
        help="Maximum number of creators to process (default: 10).",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Explicit dry-run flag (default behaviour without --send).",
    )

    return parser.parse_args(argv)


# ── Logging ───────────────────────────────────────────────────────────────────


def setup_logging() -> None:
    """Configure loguru: stderr + ``data/run.log``, level from ``LOG_LEVEL``."""
    logger.remove()  # remove default stderr handler

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


# ── Entry point ───────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> None:
    """Parse args, init DB, optionally init Instagram, run crew, print summary."""
    args = parse_args(argv)
    setup_logging()

    logger.info("Starting vernacular-creator-agents pipeline")
    logger.info("Brief: {}", args.brief)
    logger.info("Send mode: {}", args.send)
    logger.info("Approve each: {}", args.approve_each)
    logger.info("Max creators: {}", args.max_creators)

    # ── Database ──────────────────────────────────────────────────────────
    db = Database(AGENTS_DB_PATH)
    db.init_db()
    logger.info("Database initialised at {}", AGENTS_DB_PATH)

    # ── Instagram client (only when --send is set) ────────────────────────
    if args.send:
        from ig_client import get_ig_client

        client = get_ig_client()
        client.login()
        logger.info("Instagram client initialised and logged in")
    else:
        logger.info("Dry-run mode — Instagram client not initialised")

    # ── Pipeline ──────────────────────────────────────────────────────────
    from crew import InfluencerCampaignCrew

    crew = InfluencerCampaignCrew()
    summary = crew.kickoff(
        brief_text=args.brief,
        send=args.send,
        approve_each=args.approve_each,
        max_creators=args.max_creators,
    )

    # ── Summary output ────────────────────────────────────────────────────
    summary_json = json.dumps(summary, indent=2, default=str)
    logger.info("=" * 60)
    logger.info("CAMPAIGN SUMMARY")
    logger.info("=" * 60)
    logger.info("\n{}", summary_json)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
