"""Trend Spotter agent — identifies trending topics, formats, and cultural moments.

Scout-phase agent that monitors social conversations, emerging topics, viral content
formats, and cultural moments to inform influencer campaign timing and strategy.
"""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_SCOUT_TREND
from llm_client import get_fireworks_llm

from tools.connectors.tavily_tools import tavily_search
from tools.connectors.pageviews_tools import wikipedia_pageviews
from tools.connectors.gdelt_tools import gdelt_news_mentions


# ---------------------------------------------------------------------------


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_trend_spotter_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "trend_spotter_prompt.txt")


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_trend_spotter_agent() -> Agent:
    """Return a CrewAI Agent for trend spotting and cultural moment analysis."""
    prompt = _load_trend_spotter_prompt()

    return Agent(
        role=prompt.get("Role") or "Trend Spotter Specialist",
        goal=prompt.get("Goal") or (
            "Identify and analyse trending topics, hashtags, sounds, content formats, "
            "and cultural moments to recommend timing and themes for influencer campaigns."
        ),
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_SCOUT_TREND),
        tools=[tavily_search, wikipedia_pageviews, gdelt_news_mentions],
        verbose=True,
        allow_delegation=False,
    )


def get_trend_spotter_task(brief_text: str, agent: Agent) -> Task:
    """Return a CrewAI Task for trend analysis.

    Args:
        brief_text: The brand brief or industry context to analyse trends against.
        agent: The trend spotter agent (from get_trend_spotter_agent).

    Returns:
        A CrewAI Task configured to output a ranked trend report as JSON.
    """
    return Task(
        description=(
            f"Brand or industry context:\n{brief_text}\n\n"
            "Search for current trending topics, hashtags, sounds, and content formats. "
            "Identify relevant cultural moments and assess each trend for brand fit. "
            "Return a ranked trend report with brand-fit scores, format calls "
            "(rising/peak/declining), a cultural calendar, and go/skip recommendations."
        ),
        expected_output=(
            "A structured JSON trend report containing: ranked trends with brand-fit "
            "scores (X/25), format lifecycle calls (rising/peak/declining), cultural "
            "calendar with timing windows, go / caution / skip recommendations, "
            "top 3 trends to act on now, a watch list, and an avoid list."
        ),
        agent=agent,
    )
