"""Influencer Discovery agent — builds candidate rosters across platforms.

Scout-phase agent that searches for creators across platforms, screens for audience
fit and authenticity, and builds a tiered candidate list ready for scoring.
"""

from functools import wraps
from pathlib import Path

from config import MODEL_SCOUT_DISCOVERY
from llm_client import get_fireworks_llm

from tools.scraper_tools import query_creators, get_creator_details
from tools.connectors.youtube_tools import youtube_channel_stats
from tools.connectors.bluesky_tools import bluesky_profile
from tools.connectors.tavily_tools import tavily_search
from tools.registry_tools import registry_get, registry_propose

try:
    from crewai import Agent, Task
except ImportError:
    # Minimal stubs so the module imports without crewai installed.
    class Agent:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Task:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

try:
    from crewai.tools import tool
except ImportError:

    def tool(fn):  # type: ignore[misc]
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper.name = fn.__name__
        return wrapper


# ---------------------------------------------------------------------------
# Prompt parsing — extracts ## Role / ## Goal / ## Backstory sections from
# a markdown prompt file.
# ---------------------------------------------------------------------------

_PROMPT_SECTIONS = ("Role", "Goal", "Backstory")


def _parse_prompt_sections(text: str) -> dict:
    """Return a dict mapping section name to content for ## Role/Goal/Backstory."""
    sections = {name: "" for name in _PROMPT_SECTIONS}
    current = None
    lines = []

    for line in text.splitlines():
        header = line.strip().removeprefix("## ").removeprefix("# ")
        if header in _PROMPT_SECTIONS:
            if current is not None:
                sections[current] = "\n".join(lines).strip()
                lines = []
            current = header
        elif current is not None:
            lines.append(line)

    if current is not None:
        sections[current] = "\n".join(lines).strip()

    return sections


def _load_influencer_discovery_prompt() -> dict:
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "prompts" / "influencer_discovery_prompt.txt"
    )
    text = path.read_text(encoding="utf-8")
    return _parse_prompt_sections(text)


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_influencer_discovery_agent() -> Agent:
    """Return a CrewAI Agent for discovering and screening influencers."""
    prompt = _load_influencer_discovery_prompt()

    return Agent(
        role=prompt.get("Role") or "Influencer Discovery Specialist",
        goal=prompt.get("Goal") or (
            "Search across platforms, screen for audience fit and authenticity, "
            "and build a tiered candidate list with per-influencer profiles "
            "ready for fit scoring."
        ),
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_SCOUT_DISCOVERY),
        tools=[
            query_creators,
            get_creator_details,
            youtube_channel_stats,
            bluesky_profile,
            tavily_search,
            registry_get,
            registry_propose,
        ],
        verbose=True,
        allow_delegation=False,
    )


def get_influencer_discovery_task(brief_text: str, agent: Agent) -> Task:
    """Return a CrewAI Task for influencer discovery.

    Args:
        brief_text: The brand brief or search criteria.
        agent: The influencer discovery agent (from get_influencer_discovery_agent).

    Returns:
        A CrewAI Task configured to output a tiered discovery report as JSON.
    """
    return Task(
        description=(
            f"Search criteria:\n{brief_text}\n\n"
            "Search across platforms, screen candidates on follower range, engagement, "
            "relevance, and brand safety. Build per-influencer profiles with metrics, "
            "audience read, and preliminary fit score. Compile a tiered shortlist "
            "(must-reach / strong / consider) with next-step pointers."
        ),
        expected_output=(
            "A structured JSON discovery report containing: search criteria summary, "
            "candidate pool stats, per-influencer profiles (basics, metrics, audience, "
            "content, partnership history), a three-tier shortlist with fit scores, "
            "platform/niche breakdown, and next-step recommendations."
        ),
        agent=agent,
    )
