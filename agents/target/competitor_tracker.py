"""Competitor Tracker agent — monitors competitors' influencer marketing activities.

Read-only: uses GDELT news, YouTube channel stats, Tavily search, and HN
search connectors to gather competitive intelligence.
"""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_TARGET_COMPETITOR
from llm_client import get_fireworks_llm

from tools.connectors.gdelt_tools import gdelt_news_mentions
from tools.connectors.youtube_tools import youtube_channel_stats
from tools.connectors.tavily_tools import tavily_search
from tools.connectors.hn_tools import hn_search


# ---------------------------------------------------------------------------


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_competitor_tracker_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "competitor_tracker_prompt.txt")


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_competitor_tracker_agent() -> Agent:
    """Return a CrewAI Agent for tracking competitor influencer marketing."""
    prompt = _load_competitor_tracker_prompt()

    return Agent(
        role=prompt.get("Role") or "Competitor Intelligence Specialist",
        goal=prompt.get("Goal")
        or "Track competitors' influencer marketing activities and surface gaps",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_TARGET_COMPETITOR),
        tools=[
            gdelt_news_mentions,
            youtube_channel_stats,
            tavily_search,
            hn_search,
        ],
        verbose=True,
        allow_delegation=False,
    )


def get_competitor_tracker_task(
    brand: str,
    competitors: list[str],
    agent: Agent,
) -> Task:
    """Return a CrewAI Task that produces a competitive intelligence report.

    Args:
        brand: Your brand name to benchmark.
        competitors: List of competitor brand names to track.
        agent: The competitor tracker agent (from get_competitor_tracker_agent).

    Returns:
        A CrewAI Task configured to output a competitive intelligence report JSON.
    """
    competitors_str = "\n".join(f"- {c}" for c in competitors)

    return Task(
        description=(
            f"Your brand: {brand}\n\n"
            f"Competitors to track:\n{competitors_str}\n\n"
            "Research each competitor's influencer marketing activities. "
            "Use GDELT for news mentions, YouTube for channel stats, "
            "Tavily for web search, and HN for community discussions. "
            "Produce a structured competitive intelligence report "
            "with partnership rosters, campaign analysis, content strategy, "
            "estimated performance, a side-by-side comparison, "
            "and at least 3 ranked opportunity gaps."
        ),
        expected_output=(
            "A valid JSON object with these top-level keys:\n"
            "- competitive_set: array of competitors with platforms and focus areas\n"
            "- partnership_rosters: per-competitor array of creator partnerships\n"
            "- campaigns: per-competitor array of campaign details\n"
            "- comparison: side-by-side table string\n"
            "- opportunities: array of ranked opportunities with rationale\n"
            "- summary: executive summary string\n"
            "Return only the JSON object, no commentary."
        ),
        agent=agent,
    )
