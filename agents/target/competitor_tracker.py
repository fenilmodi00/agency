"""Competitor Tracker agent — monitors competitors' influencer marketing activities.

Read-only: uses GDELT news, YouTube channel stats, Tavily search, and HN
search connectors to gather competitive intelligence.
"""

from functools import wraps
from pathlib import Path

from config import MODEL_TARGET_COMPETITOR
from llm_client import get_fireworks_llm

from tools.connectors.gdelt_tools import gdelt_news_mentions
from tools.connectors.youtube_tools import youtube_channel_stats
from tools.connectors.tavily_tools import tavily_search
from tools.connectors.hn_tools import hn_search

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


def _load_competitor_tracker_prompt() -> dict:
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "prompts" / "competitor_tracker_prompt.txt"
    )
    text = path.read_text(encoding="utf-8")
    return _parse_prompt_sections(text)


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
