"""Entity Registry agent — canonical machine-facing entity authority.

Read-only utility agent: queries entity identity facts via registry tools,
submits proposals for new entity observations. Does NOT export get_*_task().
"""

from pathlib import Path

from agents._base import Agent, load_prompt

from config import MODEL_PROTOCOL_REGISTRY
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get, registry_propose, registry_verify

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def get_entity_registry_agent() -> Agent:
    """Return a CrewAI Agent for entity identity registry operations.

    This is a utility agent — it queries and proposes entity identity facts
    through the NDJSON event protocol. It does NOT own a task; tasks are
    built inline by orchestrator code.
    """
    prompt = load_prompt(_PROMPTS_DIR, "entity_registry_prompt.txt")

    return Agent(
        role=prompt.get("Role") or "Entity Registry — Canonical Machine-Facing Entity Authority",
        goal=prompt.get("Goal") or (
            "Manage canonical entity identity facts: query projected state, "
            "submit propose events for new observations, and verify entity "
            "stream integrity — all through the NDJSON registry protocol."
        ),
        backstory=prompt.get("Backstory") or (
            "I am the entity-registry principal operating under host-capability "
            "authority. I audit and maintain machine-facing identity records "
            "(canonical type, aliases, schema type, QID, sameAs, disambiguation "
            "evidence) with provenance. I never write canonical facts directly; "
            "all mutations go through operation: propose events. Only the "
            "host-capability owner may accept/reject proposals."
        ),
        llm=get_fireworks_llm(MODEL_PROTOCOL_REGISTRY),
        tools=[registry_get, registry_propose, registry_verify],
        verbose=True,
        allow_delegation=False,
    )
