"""Offer Claims Registry agent — canonical marketing claims and offers authority.

Read-only utility agent: queries claim/offer facts and submits proposals
via registry tools. Does NOT export get_*_task().
"""

from pathlib import Path

from agents._base import Agent, load_prompt

from config import MODEL_PROTOCOL_REGISTRY
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get, registry_propose, registry_verify

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def get_offer_claims_registry_agent() -> Agent:
    """Return a CrewAI Agent for offer/claims registry operations.

    This is a utility agent — it queries and proposes marketing claim
    and offer records with exact wording, evidence provenance, disclosure
    requirements, and review dates through the NDJSON event protocol.
    """
    prompt = load_prompt(_PROMPTS_DIR, "offer_claims_registry_prompt.txt")

    return Agent(
        role=prompt.get("Role") or "Offer Claims Registry — Canonical Marketing Claims and Offers Authority",
        goal=prompt.get("Goal") or (
            "Manage canonical claim and offer records: query projected state, "
            "submit propose events for claim/offer observations with evidence "
            "provenance, and verify claims stream integrity."
        ),
        backstory=prompt.get("Backstory") or (
            "I am the offer-claims-registry principal operating under "
            "host-capability authority. I curate exact claim wording, "
            "evidence sources, disclosures, terms, review dates, and live "
            "offers. I never invent substantiation or legal conclusions. "
            "Claims and offer records are L4 truth consumed by Narrative "
            "and all channel builders."
        ),
        llm=get_fireworks_llm(MODEL_PROTOCOL_REGISTRY),
        tools=[registry_get, registry_propose, registry_verify],
        verbose=True,
        allow_delegation=False,
    )
