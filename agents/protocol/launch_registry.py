"""Launch Registry agent — canonical launch-record authority.

Read-only utility agent: queries launch tier/type/stage/date/embargo facts
and submits proposals via registry tools. Does NOT export get_*_task().
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
    path = _PROMPTS_DIR / "launch_registry_prompt.txt"
    return path.read_text(encoding="utf-8")


def get_launch_registry_agent() -> Agent:
    """Return a CrewAI Agent for launch registry operations.

    This is a utility agent — it queries and proposes launch facts
    (tier, type, stage, date, embargo, submission events, manifest
    version, outcome snapshots) through the NDJSON event protocol.
    """
    prompt = _load_prompt()

    return Agent(
        role=prompt,
        goal="Manage canonical launch records: query projected state, "
        "submit propose events for launch observations, and verify "
        "launches stream integrity.",
        backstory=(
            "I am the launch-registry principal operating under host-capability "
            "authority. I record what was decided and observed about launches "
            "(tier, type, stage, date, embargo) with provenance. Stage "
            "transitions follow a valid forward path. I never plan a launch "
            "or issue a RAMP verdict."
        ),
        llm=get_fireworks_llm(MODEL_PROTOCOL_REGISTRY),
        tools=[registry_get, registry_propose, registry_verify],
        verbose=True,
        allow_delegation=False,
    )
