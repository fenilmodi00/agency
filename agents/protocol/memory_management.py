"""Memory Management agent — project working memory across HOT/WARM/COLD.

Read-only utility agent: queries registry projections and manages working
memory notes. Does NOT export get_*_task().
"""

from pathlib import Path

from agents._base import Agent, load_prompt

from config import MODEL_PROTOCOL_REGISTRY
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get, registry_propose, registry_verify

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def get_memory_management_agent() -> Agent:
    """Return a CrewAI Agent for project memory management operations.

    This is a utility agent — it queries registry projections, initializes
    runtime memory, archives stale notes, consolidates non-canonical records,
    and manages HOT/WARM/COLD working memory. It never accepts registry
    proposals or writes canonical facts on behalf of an owner.
    """
    prompt = load_prompt(_PROMPTS_DIR, "memory_management_prompt.txt")

    return Agent(
        role=prompt.get("Role") or "Memory Management — Project Working Memory Authority",
        goal=prompt.get("Goal") or (
            "Manage authorized working memory: initialize runtime directories, "
            "query registry projections, consolidate non-canonical notes, and "
            "demote/archive stale entries — all without writing canonical facts."
        ),
        backstory=prompt.get("Backstory") or (
            "I am the memory-management principal. I manage the project's "
            "authorized working memory across HOT/WARM/COLD tiers. The seven "
            "registry event streams remain canonical — I never accept proposals "
            "or write canonical facts on behalf of an owner. I can tombstone "
            "or erase under explicit host-capability authority. When sources "
            "conflict, I follow the authority order: live consent suppression, "
            "accepted registry projection, user-approved decisions, then dated "
            "evidence artifacts."
        ),
        llm=get_fireworks_llm(MODEL_PROTOCOL_REGISTRY),
        tools=[registry_get, registry_propose, registry_verify],
        verbose=True,
        allow_delegation=False,
    )
