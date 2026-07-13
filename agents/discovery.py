"""Discovery agent — finds best-matching vernacular creators for brand briefs.

Read-only: uses scraper tools and fit-scoring. Does NOT write to AGENTS_DB.
"""

from functools import wraps
from pathlib import Path

from crewai import Agent, Task

from config import MODEL_DISCOVERY
from llm_client import get_fireworks_llm
from tools.calculation_tools import calculate_fit_score as _calculate_fit_score
from tools.scraper_tools import get_creator_details, query_creators

# ---------------------------------------------------------------------------
# Prompt parsing — extracts ## Role / ## Goal / ## Backstory sections from
# a markdown prompt file. No dependency on prompt_loader (not yet created).
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


def _load_discovery_prompt() -> dict:
    path = Path(__file__).resolve().parent.parent / "prompts" / "discovery_prompt.txt"
    text = path.read_text(encoding="utf-8")
    return _parse_prompt_sections(text)


# ---------------------------------------------------------------------------
# Tool wrapper — calculate_fit_score is not @tool-decorated in the source,
# so we wrap it so CrewAI can invoke it.
# ---------------------------------------------------------------------------

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
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_discovery_agent() -> Agent:
    """Return a CrewAI Agent for discovering matching vernacular creators."""
    prompt = _load_discovery_prompt()

    return Agent(
        role=prompt.get("Role") or "Creator Discovery Specialist",
        goal=prompt.get("Goal") or "Find the best-matching creators based on a brand brief",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_DISCOVERY),
        tools=[query_creators, get_creator_details, calculate_fit_score],
        verbose=True,
        allow_delegation=False,
    )


def get_discovery_task(brief_text: str, agent: Agent) -> Task:
    """Return a CrewAI Task that produces a ranked creator shortlist as JSON.

    Args:
        brief_text: The raw brand brief text to match against creators.
        agent: The discovery agent (from get_discovery_agent).

    Returns:
        A CrewAI Task configured to output a valid JSON array with keys
        username, fit_score, and match_reason.
    """
    return Task(
        description=(
            f"Brand brief:\n{brief_text}\n\n"
            "Parse the brief, query available creators, score each for fit, "
            "and return a ranked shortlist."
        ),
        expected_output=(
            "A valid JSON array where each element contains:\n"
            "- username: string — creator's platform username or handle\n"
            "- fit_score: number — 0 to 100\n"
            "- match_reason: string — brief explanation of why this creator fits\n"
            "Results must be sorted by fit_score descending. "
            "Return only the JSON array, no commentary."
        ),
        agent=agent,
    )