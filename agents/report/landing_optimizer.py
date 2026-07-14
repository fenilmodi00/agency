# agents/report/landing_optimizer.py
"""Landing Optimizer agent — optimizes landing pages for influencer-driven traffic.

Report phase: uses Firecrawl, PageSpeed Insights, and Tavily Extract connectors.
Does NOT write to AGENTS_DB.
"""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_REPORT_LANDING
from llm_client import get_fireworks_llm
from tools.connectors.firecrawl_tools import firecrawl_scrape
from tools.connectors.psi_tools import pagespeed_insights
from tools.connectors.tavily_tools import tavily_extract


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_landing_optimizer_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "landing_optimizer_prompt.txt")


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_landing_optimizer_agent() -> Agent:
    """Return a CrewAI Agent for optimizing influencer landing pages."""
    prompt = _load_landing_optimizer_prompt()

    return Agent(
        role=prompt.get("Role") or "Landing Optimizer · Landing Page Conversion Specialist",
        goal=prompt.get("Goal") or "Optimize landing pages for influencer-driven traffic.",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_REPORT_LANDING),
        tools=[firecrawl_scrape, pagespeed_insights, tavily_extract],
        verbose=True,
        allow_delegation=False,
    )


def get_landing_optimizer_task(page_url: str, agent: Agent) -> Task:
    """Return a CrewAI Task that produces a landing page optimization plan.

    Args:
        page_url: The landing page URL to analyze and optimize.
        agent: The landing optimizer agent (from get_landing_optimizer_agent).

    Returns:
        A CrewAI Task configured to output a landing page optimization plan.
    """
    return Task(
        description=(
            f"Landing page URL: {page_url}\n\n"
            "Analyze the landing page for message match, page structure, "
            "social proof integration, and conversion optimization. "
            "Produce a prioritized optimization plan with A/B test roadmap."
        ),
        expected_output=(
            "A valid JSON object with keys:\n"
            "- page_url: string — the analyzed URL\n"
            "- message_match_score: number — 0 to 10\n"
            "- issues: array of dicts with area, severity, description, and fix\n"
            "- ab_test_roadmap: array of dicts with hypothesis, variants, "
            "sample_size, duration_days, and success_metric\n"
            "- expected_impact: string — estimated conversion improvement\n"
            "Return only the JSON object, no commentary."
        ),
        agent=agent,
    )
