"""Audience Mapper agent — profiles target audiences and maps subculture communities.

Scout-phase agent that produces demographic/psychographic profiles, platform-priority
matrices, named personas, influencer-selection criteria (audience mode), or community
maps, culture decodes, key-voice tiers, Brand Fit Score, and entry strategy (niche mode).
"""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_SCOUT_AUDIENCE
from llm_client import get_fireworks_llm

from tools.scraper_tools import query_creators
from tools.connectors.tavily_tools import tavily_search
from tools.connectors.pageviews_tools import wikipedia_pageviews


# ---------------------------------------------------------------------------


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_audience_mapper_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "audience_mapper_prompt.txt")


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_audience_mapper_agent() -> Agent:
    """Return a CrewAI Agent for audience mapping and community analysis."""
    prompt = _load_audience_mapper_prompt()

    return Agent(
        role=prompt.get("Role") or "Audience Mapper Specialist",
        goal=prompt.get("Goal") or (
            "Analyse target audiences and niche communities to produce "
            "demographic/psychographic profiles, platform-priority matrices, "
            "named personas, and influencer-selection criteria."
        ),
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_SCOUT_AUDIENCE),
        tools=[query_creators, tavily_search, wikipedia_pageviews],
        verbose=True,
        allow_delegation=False,
    )


def get_audience_mapper_task(brief_text: str, agent: Agent) -> Task:
    """Return a CrewAI Task for audience analysis.

    Args:
        brief_text: The raw brand brief or community description to analyse.
        agent: The audience mapper agent (from get_audience_mapper_agent).

    Returns:
        A CrewAI Task configured to output a structured audience analysis JSON.
    """
    return Task(
        description=(
            f"Brand brief or community:\n{brief_text}\n\n"
            "Analyse the target audience or niche community. In audience mode, "
            "produce demographic/psychographic profiles, a platform-priority matrix, "
            "named personas, and influencer-selection criteria. In niche mode, "
            "produce a community map, culture decode, key-voice tiers, Brand Fit Score, "
            "and entry strategy. Return a structured JSON report."
        ),
        expected_output=(
            "A structured JSON report containing: audience or community analysis, "
            "demographics with confidence levels, psychographic profile, platform "
            "priorities, persona(s), and influencer-selection criteria (audience mode) "
            "or community map, culture decode, tiered key voices, Brand Fit Score (X/25) "
            "with verdict, phased entry strategy, and red lines (niche mode)."
        ),
        agent=agent,
    )
