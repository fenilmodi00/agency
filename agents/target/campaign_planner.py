"""Campaign Planner agent — designs influencer campaigns from strategy to execution.

Read-only: uses creator database query, Tavily search, and registry state
to build campaign plans.
"""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_TARGET_PLANNER
from llm_client import get_fireworks_llm

from tools.scraper_tools import query_creators
from tools.connectors.tavily_tools import tavily_search
from tools.registry_tools import registry_get


# ---------------------------------------------------------------------------


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_campaign_planner_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "campaign_planner_prompt.txt")


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_campaign_planner_agent() -> Agent:
    """Return a CrewAI Agent for designing influencer campaign plans."""
    prompt = _load_campaign_planner_prompt()

    return Agent(
        role=prompt.get("Role") or "Campaign Planning Strategist",
        goal=prompt.get("Goal")
        or "Design complete influencer campaign plans from strategy to execution",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_TARGET_PLANNER),
        tools=[
            query_creators,
            tavily_search,
            registry_get,
        ],
        verbose=True,
        allow_delegation=False,
    )


def get_campaign_planner_task(
    brand: str,
    budget: float,
    audience: str,
    timeframe: str,
    agent: Agent,
    campaign_type: str = "product launch",
    platforms: list[str] | None = None,
) -> Task:
    """Return a CrewAI Task that produces a campaign plan.

    Args:
        brand: Brand or product name.
        budget: Total campaign budget.
        audience: Target audience description.
        timeframe: Campaign timeframe.
        agent: The campaign planner agent (from get_campaign_planner_agent).
        campaign_type: Type of campaign (default: 'product launch').
        platforms: Target platforms (default: ['Instagram', 'TikTok']).

    Returns:
        A CrewAI Task configured to output a campaign plan JSON.
    """
    if platforms is None:
        platforms = ["Instagram", "TikTok"]

    return Task(
        description=(
            f"Brand/product: {brand}\n"
            f"Budget: {budget}\n"
            f"Target audience: {audience}\n"
            f"Timeframe: {timeframe}\n"
            f"Campaign type: {campaign_type}\n"
            f"Platforms: {', '.join(platforms)}\n\n"
            "Design a complete influencer campaign plan. "
            "Query the creator database to validate tier mixes, "
            "search the web for benchmarks, and read registry state "
            "for prior data. Output a structured plan with SMART objectives, "
            "influencer criteria, content requirements, timeline, "
            "budget allocation, and success metrics."
        ),
        expected_output=(
            "A valid JSON object with these top-level keys:\n"
            "- campaign_name: string\n"
            "- objectives: primary (objective, success, failure) and secondary array\n"
            "- strategy: big_idea, key_messages, platform_split\n"
            "- influencer_criteria: tier_mix and selection_criteria\n"
            "- content_requirements: per-platform deliverables\n"
            "- timeline: array of phases with dates and activities\n"
            "- budget_allocation: per-category amounts and percentages\n"
            "- success_metrics: primary KPIs and reporting cadence\n"
            "- next_step: string naming the next step\n"
            "Return only the JSON object, no commentary."
        ),
        agent=agent,
    )
