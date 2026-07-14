# agents/report/roi_calculator.py
"""ROI Calculator agent — calculates return on investment for campaigns.

Report phase: uses registry tools and experiment connectors.
Does NOT write to AGENTS_DB.
"""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_REPORT_ROI
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get
from tools.connectors.experiment_tools import experiment_proportion


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_roi_calculator_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "roi_calculator_prompt.txt")


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_roi_calculator_agent() -> Agent:
    """Return a CrewAI Agent for calculating campaign ROI."""
    prompt = _load_roi_calculator_prompt()

    return Agent(
        role=prompt.get("Role") or "ROI Calculator · Return-on-Investment Analyst",
        goal=prompt.get("Goal") or "Calculate and communicate campaign ROI using multiple methodologies.",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_REPORT_ROI),
        tools=[registry_get, experiment_proportion],
        verbose=True,
        allow_delegation=False,
    )


def get_roi_calculator_task(spend_data: str, agent: Agent) -> Task:
    """Return a CrewAI Task that produces an ROI calculation.

    Args:
        spend_data: JSON string with campaign spend and results data.
        agent: The ROI calculator agent (from get_roi_calculator_agent).

    Returns:
        A CrewAI Task configured to output ROI calculations.
    """
    return Task(
        description=(
            f"Campaign spend and results data:\n{spend_data}\n\n"
            "Calculate ROI using multiple methodologies — direct ROI/ROAS, "
            "Earned Media Value, cost-efficiency metrics, attribution-modeled "
            "revenue, and LTV-based ROI. Show all inputs and formulas."
        ),
        expected_output=(
            "A valid JSON object with keys:\n"
            "- investment: number\n"
            "- direct_revenue: number\n"
            "- roi_percent: number\n"
            "- roas: number\n"
            "- emv: number\n"
            "- cost_efficiency: object with cpm, cpe, cpa\n"
            "- attribution: object with models and values\n"
            "- assessment: string — 'profitable', 'break_even', or 'loss'\n"
            "- recommendations: array of strings\n"
            "Return only the JSON object, no commentary."
        ),
        agent=agent,
    )
