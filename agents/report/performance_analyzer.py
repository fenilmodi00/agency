# agents/report/performance_analyzer.py
"""Performance Analyzer agent — analyzes influencer campaign performance.

Report phase: uses registry tools and Tavily Search connectors.
Does NOT write to AGENTS_DB.
"""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_REPORT_PERFORMANCE
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get
from tools.connectors.tavily_tools import tavily_search


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_performance_analyzer_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "performance_analyzer_prompt.txt")


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_performance_analyzer_agent() -> Agent:
    """Return a CrewAI Agent for analyzing influencer campaign performance."""
    prompt = _load_performance_analyzer_prompt()

    return Agent(
        role=prompt.get("Role") or "Performance Analyzer · Campaign Performance Analyst",
        goal=prompt.get("Goal") or "Analyze influencer campaign performance against targets and benchmarks.",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_REPORT_PERFORMANCE),
        tools=[registry_get, tavily_search],
        verbose=True,
        allow_delegation=False,
    )


def get_performance_analyzer_task(campaign_name: str, agent: Agent) -> Task:
    """Return a CrewAI Task that produces a campaign performance analysis.

    Args:
        campaign_name: The name of the campaign to analyze.
        agent: The performance analyzer agent (from get_performance_analyzer_agent).

    Returns:
        A CrewAI Task configured to output a performance analysis.
    """
    return Task(
        description=(
            f"Campaign name: {campaign_name}\n\n"
            "Analyze the influencer campaign's performance — core metrics "
            "vs target and benchmark, platform/influencer/content rankings, "
            "engagement quality and sentiment, conversion attribution, "
            "and ranked learnings with recommendations."
        ),
        expected_output=(
            "A valid JSON object with keys:\n"
            "- campaign: string\n"
            "- performance_verdict: string\n"
            "- metric_scorecard: array of dicts with metric, result, target, "
            "benchmark, and status\n"
            "- top_creators: array of dicts with handle and reason\n"
            "- learnings: array of strings\n"
            "- recommendations: array of strings\n"
            "Return only the JSON object, no commentary."
        ),
        agent=agent,
    )
