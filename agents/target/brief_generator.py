"""Brief Generator agent — creates structured influencer briefs for campaign creators.

Read-only: uses registry state and creator database queries.
"""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_TARGET_BRIEF
from llm_client import get_fireworks_llm

from tools.registry_tools import registry_get
from tools.scraper_tools import query_creators


# ---------------------------------------------------------------------------


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_brief_generator_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "brief_generator_prompt.txt")


# ---------------------------------------------------------------------------
# Agent & Task factory
# ---------------------------------------------------------------------------


def get_brief_generator_agent() -> Agent:
    """Return a CrewAI Agent for creating structured influencer briefs."""
    prompt = _load_brief_generator_prompt()

    return Agent(
        role=prompt.get("Role") or "Influencer Brief Specialist",
        goal=prompt.get("Goal")
        or "Create clear, comprehensive influencer briefs with explicit compliance terms",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_TARGET_BRIEF),
        tools=[
            registry_get,
            query_creators,
        ],
        verbose=True,
        allow_delegation=False,
    )


def get_brief_generator_task(
    campaign_name: str,
    product: str,
    platform: str,
    content_type: str,
    agent: Agent,
    creator_username: str | None = None,
) -> Task:
    """Return a CrewAI Task that produces a structured influencer brief.

    Args:
        campaign_name: Name of the campaign.
        product: Product or service being promoted.
        platform: Target platform (e.g. 'Instagram', 'TikTok').
        content_type: Type of content (e.g. 'review', 'tutorial').
        agent: The brief generator agent (from get_brief_generator_agent).
        creator_username: Optional creator to personalize the brief for.

    Returns:
        A CrewAI Task configured to output a structured brief JSON.
    """
    description = (
        f"Campaign: {campaign_name}\n"
        f"Product: {product}\n"
        f"Platform: {platform}\n"
        f"Content type: {content_type}\n"
    )
    if creator_username:
        description += f"Creator: {creator_username}\n"

    description += (
        "\nCreate a structured influencer brief. "
        "Read registry state for canonical narrative/claims data. "
        "Query the creator database to personalize the 'Why You' section. "
        "Ensure disclosure requirements and usage rights are stated explicitly."
    )

    return Task(
        description=description,
        expected_output=(
            "A valid JSON object with these top-level keys:\n"
            "- brief_title: string\n"
            "- campaign_overview: string\n"
            "- key_messages: array of strings\n"
            "- deliverables: array of {format, quantity, specs}\n"
            "- creative_direction: {tone, visual_style, color_palette}\n"
            "- timeline: {briefing_date, draft_deadline, go_live_date}\n"
            "- compliance: {disclosure, usage_rights}\n"
            "- compensation: {type, amount, terms}\n"
            "- contact: {point_of_contact, email}\n"
            "Return only the JSON object, no commentary."
        ),
        agent=agent,
    )
