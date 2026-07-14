"""Narrative Registry agent — L1 strategy authority for brand narrative canon.

Read-only utility agent: queries brand canon, version, message hierarchy,
and proof/claim pointer facts via registry tools. Does NOT export
get_*_task().
"""

from pathlib import Path

from agents._base import Agent, load_prompt

from config import MODEL_PROTOCOL_REGISTRY
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get, registry_propose, registry_verify

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def get_narrative_registry_agent() -> Agent:
    """Return a CrewAI Agent for narrative canon registry operations.

    This is a utility agent — it queries and proposes brand narrative
    canon facts (positioning, message hierarchy, voice/naming rules,
    proof/claim pointers) through the NDJSON event protocol.
    """
    prompt = load_prompt(_PROMPTS_DIR, "narrative_registry_prompt.txt")

    return Agent(
        role=prompt.get("Role") or "Narrative Registry — L1 Strategy Authority for Brand Narrative Canon",
        goal=prompt.get("Goal") or (
            "Manage canonical brand narrative canon: query projected state, "
            "submit propose events for complete canon versions, and verify "
            "narrative stream integrity."
        ),
        backstory=prompt.get("Backstory") or (
            "I am the narrative-registry principal operating under host-capability "
            "authority. I maintain the L1 strategy authority: one complete, "
            "versioned narrative canon per brand. Every SEO/GEO, social, email, "
            "paid, influencer, and launch builder derives messages from this "
            "canon and accepted claims. Channel adaptations cannot redefine L1 "
            "brand truth. Only the host-capability owner may accept/reject "
            "complete canon-version proposals."
        ),
        llm=get_fireworks_llm(MODEL_PROTOCOL_REGISTRY),
        tools=[registry_get, registry_propose, registry_verify],
        verbose=True,
        allow_delegation=False,
    )
