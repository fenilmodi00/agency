# agents/report/report_generator.py
"""Report Generator agent — creates stakeholder-ready campaign reports.

Report phase: uses registry tools and ledger connectors.
Does NOT write to AGENTS_DB.
"""

from functools import wraps
from pathlib import Path

from config import MODEL_REPORT_GENERATOR
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get
from tools.connectors.ledger_tools import ledger_diff

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


def _load_report_generator_prompt() -> dict:
    path = Path(__file__).resolve().parent.parent.parent / "prompts" / "report_generator_prompt.txt"
    text = path.read_text(encoding="utf-8")
    return _parse_prompt_sections(text)


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_report_generator_agent() -> Agent:
    """Return a CrewAI Agent for generating stakeholder campaign reports."""
    prompt = _load_report_generator_prompt()

    return Agent(
        role=prompt.get("Role") or "Report Generator · Stakeholder Report Writer",
        goal=prompt.get("Goal") or "Create professional campaign reports tailored to specific audiences.",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_REPORT_GENERATOR),
        tools=[registry_get, ledger_diff],
        verbose=True,
        allow_delegation=False,
    )


def get_report_generator_task(
    campaign_name: str,
    audience: str,
    agent: Agent,
) -> Task:
    """Return a CrewAI Task that produces a stakeholder campaign report.

    Args:
        campaign_name: The name of the campaign to report on.
        audience: Target audience — 'executive', 'client', 'team', or 'board'.
        agent: The report generator agent (from get_report_generator_agent).

    Returns:
        A CrewAI Task configured to output a formatted campaign report.
    """
    return Task(
        description=(
            f"Campaign name: {campaign_name}\n"
            f"Target audience: {audience}\n\n"
            "Generate a professional stakeholder report with narrative structure, "
            "data tables, key learnings, and concrete recommendations "
            "appropriate for the specified audience."
        ),
        expected_output=(
            "A valid JSON object with keys:\n"
            "- campaign: string\n"
            "- audience: string\n"
            "- report_sections: array of dicts with title and content\n"
            "- key_metrics: array of dicts with metric, value, and context\n"
            "- recommendations: array of strings\n"
            "- action_items: array of dicts with item, owner, and deadline\n"
            "Return only the JSON object, no commentary."
        ),
        agent=agent,
    )
