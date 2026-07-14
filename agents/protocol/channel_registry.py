"""Channel Registry agent — canonical brand-owned channel authority.

Read-only utility agent: queries channel handle, state, governance, cadence,
voice, and UGC permission facts via registry tools. Does NOT export
get_*_task().
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
    path = _PROMPTS_DIR / "channel_registry_prompt.txt"
    return path.read_text(encoding="utf-8")


def get_channel_registry_agent() -> Agent:
    """Return a CrewAI Agent for channel registry operations.

    This is a utility agent — it queries and proposes channel facts
    (handle, state, governance, cadence, voice adaptation, UGC permission,
    advocate opt-in) through the NDJSON event protocol.
    """
    prompt = _load_prompt()

    return Agent(
        role=prompt,
        goal="Manage canonical brand-owned channel records: query projected "
        "state, submit propose events for channel observations, and verify "
        "channels stream integrity.",
        backstory=(
            "I am the channel-registry principal operating under host-capability "
            "authority. I curate channel handle, state, governance, cadence, "
            "per-platform voice-adaptation, UGC-permission, and advocate facts "
            "with provenance. I never fabricate permission from a public post "
            "or tag. Only the host-capability owner may accept/reject "
            "proposals or upsert/transition channel state."
        ),
        llm=get_fireworks_llm(MODEL_PROTOCOL_REGISTRY),
        tools=[registry_get, registry_propose, registry_verify],
        verbose=True,
        allow_delegation=False,
    )
