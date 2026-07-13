"""Proposal agent and task for vernacular-creator-agents.

The Proposal agent generates campaign proposals for a list of creators.
It only reads creator data — it does NOT write to AGENTS_DB.
"""

from crewai import Agent, Task
from crewai.tools import tool
from config import MODEL_PROPOSAL
from llm_client import get_fireworks_llm
from tools.scraper_tools import (
    get_creator_content_summary as _raw_content_summary,
    get_creator_recent_posts as _raw_recent_posts,
)


# Wrap raw scraper functions as proper CrewAI BaseTool instances
@tool
def get_creator_content_summary(username: str) -> list:
    """Get content summary (post types, avg views, etc.) for a creator."""
    return _raw_content_summary(username)


@tool
def get_creator_recent_posts(username: str) -> list:
    """Get recent posts for a creator."""
    return _raw_recent_posts(username)


def get_proposal_agent() -> Agent:
    """Return a CrewAI Agent for generating creator campaign proposals."""
    return Agent(
        role="Proposal Strategist",
        goal="Generate detailed campaign proposals for vernacular content creators",
        backstory=(
            "You are an expert creator-campaign strategist. You analyze creator "
            "profiles, content summaries, and recent posts to craft tailored "
            "campaign proposals with deliverables, budgets, and timelines."
        ),
        llm=get_fireworks_llm(MODEL_PROPOSAL),
        tools=[get_creator_content_summary, get_creator_recent_posts],
        verbose=True,
    )


def get_proposal_task(creators_json: str, agent: Agent) -> Task:
    """Return a CrewAI Task that produces campaign proposals for the given creators.

    Args:
        creators_json: JSON string of the creators to propose campaigns for.
        agent: The proposal agent (from get_proposal_agent).

    Returns:
        A CrewAI Task configured with the correct expected output schema.
    """
    return Task(
        description=(
            f"Analyze the following creators (JSON): {creators_json}\n\n"
            "For each creator, research their content summary and recent posts "
            "using the available tools. Then generate a campaign proposal."
        ),
        expected_output=(
            "A JSON array where each element contains:\n"
            "- creator_username: string\n"
            "- campaign_ideas: array of campaign concept strings\n"
            "- deliverables: array of deliverable descriptions\n"
            "- suggested_budget: numeric budget in INR\n"
            "- timeline: string describing the campaign timeline\n"
            "- notes: string with additional context or caveats"
        ),
        agent=agent,
    )