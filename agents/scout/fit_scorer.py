"""Fit Scorer agent — scores shortlisted creators on STAR Suitability.

Scout-phase agent that evaluates each shortlisted creator on the STAR Suitability (S)
dimension (items S1–S10), flags veto conditions (STAR-S2, STAR-S6), and produces
a separate campaign-fit comparison matrix without mixing commercial terms into the
Suitability read.
"""

from pathlib import Path

from agents._base import Agent, Task, tool, load_prompt

from config import MODEL_SCOUT_FIT
from llm_client import get_fireworks_llm
from tools.calculation_tools import calculate_fit_score as _calculate_fit_score
from tools.registry_tools import registry_get


@tool
def calculate_fit_score(creator: dict, brief: dict) -> float:  # noqa: F811
    """Calculate a weighted fit score between 0.0 and 1.0 for a creator-brief pair."""
    return _calculate_fit_score(creator, brief)


# ---------------------------------------------------------------------------


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_fit_scorer_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "fit_scorer_prompt.txt")


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
