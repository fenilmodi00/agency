"""Negotiator agent — handles rate negotiation with vernacular creators."""

from pathlib import Path

from crewai import Agent

from config import MODEL_NEGOTIATOR
from llm_client import get_fireworks_llm

# Tools for Instagram DMs
from tools.instagram_tools import (
    read_instagram_threads,
    read_thread_messages,
    send_instagram_dm,
)

# Database / state tools
from tools.database_tools import (
    check_dm_quota,
    get_brand_budget,
    get_conversation_history,
    log_dm,
    update_conversation_negotiation,
)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Read a prompt file from the prompts/ directory."""
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


def get_negotiator_agent() -> Agent:
    """Return a CrewAI Agent for rate negotiation.

    Expected task output JSON:
        {
            "action": "accept | counter | wait | escalate | give_up",
            "response": "<message in creator's language>",
            "agreed_rate": <number or null>,
            "round_number": <int>,
            "status": "open | accepted | escalated | closed | give_up"
        }
    """
    role_prompt = _load_prompt("negotiator_prompt.txt")

    return Agent(
        role="Rate Negotiator",
        goal=(
            "Negotiate compensation rates with vernacular creators. "
            "Keep rates within budget, escalate when necessary, and "
            "communicate in the creator's language (Gujarati or Hindi)."
        ),
        backstory=role_prompt,
        llm=get_fireworks_llm(MODEL_NEGOTIATOR),
        tools=[
            read_instagram_threads,
            read_thread_messages,
            send_instagram_dm,
            get_conversation_history,
            update_conversation_negotiation,
            get_brand_budget,
            check_dm_quota,
            log_dm,
        ],
        verbose=True,
        allow_delegation=False,
    )