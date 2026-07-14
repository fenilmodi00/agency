"""Budget Optimizer agent — allocates influencer budgets across tiers and platforms.

Read-only: uses fit scoring and registry state.
"""

from pathlib import Path

from agents._base import Agent, Task, tool, load_prompt

from config import MODEL_TARGET_BUDGET
from llm_client import get_fireworks_llm

from tools.calculation_tools import calculate_fit_score as _calculate_fit_score
from tools.registry_tools import registry_get


# ---------------------------------------------------------------------------


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_budget_optimizer_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "budget_optimizer_prompt.txt")


# ---------------------------------------------------------------------------
# Tool wrapper — calculate_fit_score is not @tool-decorated in the source,
# so we wrap it so CrewAI can invoke it.
# ---------------------------------------------------------------------------


@tool
def calculate_fit_score(creator: dict, brief: dict) -> float:  # noqa: F811
    """Calculate a weighted fit score between 0.0 and 1.0 for a creator-brief pair."""
    return _calculate_fit_score(creator, brief)


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_budget_optimizer_agent() -> Agent:
    """Return a CrewAI Agent for optimizing influencer budget allocation."""
    prompt = _load_budget_optimizer_prompt()

    return Agent(
        role=prompt.get("Role") or "Budget Optimization Analyst",
        goal=prompt.get("Goal")
        or "Allocate influencer budgets to maximize ROI with labeled projections",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_TARGET_BUDGET),
        tools=[
            calculate_fit_score,
            registry_get,
        ],
        verbose=True,
        allow_delegation=False,
    )


def get_budget_optimizer_task(
    total_budget: float,
    platforms: list[str],
    campaign_goal: str,
    agent: Agent,
    audience: str = "",
    timeframe: str = "",
) -> Task:
    """Return a CrewAI Task that produces a budget allocation plan.

    Args:
        total_budget: Total campaign budget.
        platforms: Target platforms.
        campaign_goal: Campaign goal (awareness, engagement, conversions).
        agent: The budget optimizer agent (from get_budget_optimizer_agent).
        audience: Target audience description (optional).
        timeframe: Campaign timeframe (optional).

    Returns:
        A CrewAI Task configured to output a budget optimization JSON.
    """
    return Task(
        description=(
            f"Total budget: {total_budget}\n"
            f"Platforms: {', '.join(platforms)}\n"
            f"Campaign goal: {campaign_goal}\n"
            f"Target audience: {audience or '(not specified)'}\n"
            f"Timeframe: {timeframe or '(not specified)'}\n\n"
            "Optimize the budget allocation across tiers and platforms. "
            "Use fit scoring to prioritize creator alignment. "
            "Read registry state for prior budget data. "
            "Model at least 3 scenarios (Conservative, Recommended, Aggressive). "
            "Label every projected metric as Measured, User-provided, or Estimated."
        ),
        expected_output=(
            "A valid JSON object with these top-level keys:\n"
            "- total_budget: number\n"
            "- recommended_allocation: {by_tier, by_platform, contingency}\n"
            "- projected_roi: {reach, engagements, cpm, roi_ratio, label}\n"
            "- scenarios: array of {name, total_spend, projected_reach, roi, rationale}\n"
            "- optimization_strategies: array of strings\n"
            "- recommended_scenario: string\n"
            "Return only the JSON object, no commentary."
        ),
        agent=agent,
    )
