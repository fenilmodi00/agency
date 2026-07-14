"""Creator Registry agent — canonical creator-roster authority.

Read-only utility agent: queries creator identity, rate, rights, and
exclusivity facts via registry tools. Does NOT export get_*_task().
"""

from pathlib import Path

try:
    from crewai import Agent
except ImportError:
    Agent = object  # type: ignore[misc,assignment]

from config import MODEL_PROTOCOL_REGISTRY
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get, registry_propose, registry_verify

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_prompt() -> str:
    path = _PROMPTS_DIR / "creator_registry_prompt.txt"
    return path.read_text(encoding="utf-8")


def get_creator_registry_agent() -> Agent:
    """Return a CrewAI Agent for creator roster registry operations.

    This is a utility agent — it queries and proposes creator facts
    (rate history, rights, exclusivity, compliance events, performance
    baselines) through the NDJSON event protocol.
    """
    prompt = _load_prompt()

    return Agent(
        role=prompt,
        goal="Manage canonical creator roster facts: query projected state, "
        "submit propose events for creator observations, and verify creator "
        "stream integrity — all through the NDJSON registry protocol.",
        backstory=(
            "I am the creator-registry principal operating under host-capability "
            "authority. I curate creator identity, rate, rights, exclusivity, "
            "compliance-event, and performance facts with provenance. I minimize "
            "personal data and use pseudonymous aggregate IDs. Only the "
            "host-capability owner may accept/reject proposals or upsert state."
        ),
        llm=get_fireworks_llm(MODEL_PROTOCOL_REGISTRY),
        tools=[registry_get, registry_propose, registry_verify],
        verbose=True,
        allow_delegation=False,
    )
