# agents/report/performance_analyzer.py
"""Performance Analyzer agent — analyzes influencer campaign performance.

Report phase: uses registry tools and Tavily Search connectors.
Does NOT write to AGENTS_DB.
"""

from functools import wraps
from pathlib import Path

from config import MODEL_REPORT_PERFORMANCE
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get
from tools.connectors.tavily_tools import tavily_search

try:
    from crewai import Agent, Task
except ImportError:
    class Agent:  # type: ignore[no_redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Task:  # type: ignore[no_redef]
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
# Prompt parsing
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


def _load_performance_analyzer_prompt() -> dict:
    path = Path(__file__).resolve().parent.parent.parent / "prompts" / "performance_analyzer_prompt.txt"
    text = path.read_text(encoding="utf-8")
    return _parse_prompt_sections(text)


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
