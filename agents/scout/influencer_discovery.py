"""Influencer Discovery agent — builds candidate rosters across platforms.

Scout-phase agent that searches for creators across platforms, screens for audience
fit and authenticity, and builds a tiered candidate list ready for scoring.
"""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_SCOUT_DISCOVERY
from llm_client import get_fireworks_llm

from tools.scraper_tools import query_creators, get_creator_details
from tools.connectors.youtube_tools import youtube_channel_stats
from tools.connectors.bluesky_tools import bluesky_profile
from tools.connectors.tavily_tools import tavily_search
from tools.registry_tools import registry_get, registry_propose

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_influencer_discovery_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "influencer_discovery_prompt.txt")


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
