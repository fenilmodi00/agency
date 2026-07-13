"""Contract Agent — generates ASCI-compliant collaboration agreements."""

from pathlib import Path

from crewai import Agent

from config import MODEL_CONTRACT
from llm_client import get_fireworks_llm
from tools.database_tools import get_brand_brief, get_conversation_details, save_contract


def _load_prompt() -> str:
    """Load the contract prompt from prompts/contract_prompt.txt."""
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "contract_prompt.txt"
    return prompt_path.read_text(encoding="utf-8")


def get_contract_agent() -> Agent:
    """Return a CrewAI Agent for generating collaboration contracts.

    The agent reads agreed terms from a conversation, generates a bilingual
    contract (English + Gujarati summary) with ASCI disclosure placeholders,
    and saves the result.
    """
    prompt = _load_prompt()

    return Agent(
        role="Contract Drafter",
        goal=(
            "Generate a bilingual collaboration agreement between the brand and "
            "the creator. Output valid JSON with contract_text, gujarati_summary, "
            "contract_type, deliverables, usage_rights, timeline, and asci_compliant."
        ),
        backstory=(
            "Influencer marketing in India is governed by ASCI guidelines. "
            "Contracts must include disclosure requirements (#ad/#sponsored), "
            "clear deliverable specs, usage rights, timeline, and termination "
            "clauses. All output is a template requiring legal review."
        ),
        llm=get_fireworks_llm(MODEL_CONTRACT),
        tools=[get_conversation_details, get_brand_brief, save_contract],
        verbose=True,
        max_iter=5,
    )