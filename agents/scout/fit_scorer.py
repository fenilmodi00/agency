"""Fit Scorer agent — scores shortlisted creators on STAR Suitability.

Scout-phase agent that evaluates each shortlisted creator on the STAR Suitability (S)
dimension (items S1–S10), flags veto conditions (STAR-S2, STAR-S6), and produces
a separate campaign-fit comparison matrix without mixing commercial terms into the
Suitability read.
"""

from functools import wraps
from pathlib import Path

from config import MODEL_SCOUT_FIT
from llm_client import get_fireworks_llm
from tools.calculation_tools import calculate_fit_score as _calculate_fit_score
from tools.registry_tools import registry_get

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

try:
    from crewai.tools import tool
except ImportError:

    def tool(fn):  # type: ignore[misc]
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper.name = fn.__name__
        return wrapper


@tool
def calculate_fit_score(creator: dict, brief: dict) -> float:  # noqa: F811
    """Calculate a weighted fit score between 0.0 and 1.0 for a creator-brief pair."""
    return _calculate_fit_score(creator, brief)


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


def _load_fit_scorer_prompt() -> dict:
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "prompts" / "fit_scorer_prompt.txt"
    )
    text = path.read_text(encoding="utf-8")
    return _parse_prompt_sections(text)


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_fit_scorer_agent() -> Agent:
    """Return a CrewAI Agent for scoring creator fit against brand briefs."""
    prompt = _load_fit_scorer_prompt()

    return Agent(
        role=prompt.get("Role") or "Fit Scorer Specialist",
        goal=prompt.get("Goal") or (
            "Score each shortlisted creator on the STAR Suitability (S) dimension "
            "using items S1–S10, flag veto conditions (STAR-S2, STAR-S6), and "
            "produce a separate campaign-fit comparison matrix."
        ),
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_SCOUT_FIT),
        tools=[calculate_fit_score, registry_get],
        verbose=True,
        allow_delegation=False,
    )


def get_fit_scorer_task(brief_text: str, agent: Agent) -> Task:
    """Return a CrewAI Task for scoring creator fit.

    Args:
        brief_text: The brand brief context and JSON shortlist of creators to score.
        agent: The fit scorer agent (from get_fit_scorer_agent).

    Returns:
        A CrewAI Task configured to output a STAR Suitability read as JSON.
    """
    return Task(
        description=(
            f"Brand brief and creator shortlist:\n{brief_text}\n\n"
            "For each creator: evaluate all 10 Suitability items S1–S10 with "
            "evidence (Pass/Partial/Fail/Unknown/N/A), flag any STAR-S2 or STAR-S6 "
            "veto conditions, and produce a separate campaign-fit comparison matrix. "
            "Return the Suitability read and commercial-fit matrix as structured JSON. "
            "The Suitability read must not be mixed with campaign-specific commercial "
            "terms — those go in the separate matrix."
        ),
        expected_output=(
            "A structured JSON report containing: typed context (goal, assessment_time, "
            "platform, niche cohort), per-creator Suitability (S) read for items S1–S10 "
            "with evidence dates and confidence levels, any STAR-S2/S6 veto flags, "
            "SQS coverage indicator, and a separately labeled commercial-fit comparison "
            "matrix with scores (1-5) for audience-to-campaign fit, content style, "
            "brand/category fit, commercial terms, availability, and partnership potential."
        ),
        agent=agent,
    )
