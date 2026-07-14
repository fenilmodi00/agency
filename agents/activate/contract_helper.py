"""Activate contract helper — drafts/reviews influencer partnership agreements."""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_ACTIVATE_CONTRACT
from llm_client import get_fireworks_llm
from tools.database_tools import get_conversation_details, get_brand_brief, save_contract
from tools.registry_tools import registry_get


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_contract_helper_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "contract_helper_prompt.txt")


CONTRACT_HELPER_TASK_DESCRIPTION = """\
You are drafting or reviewing an influencer partnership agreement.

## Input
You will receive:
- conversation_id: the DB id of the negotiation conversation
- brief_id: the brand brief id

## Process

1. **Fetch conversation details.** Call `get_conversation_details(conversation_id=...)`
   to retrieve the agreed deliverables, compensation, and creator info.

2. **Fetch the brand brief.** Call `get_brand_brief(brief_id=...)` to get campaign
   context and budget constraints.

3. **Fetch registry data.** Call `registry_get("creators", "<username>")` to check
   for existing exclusivity windows, contract status, and usage-rights history.

4. **Draft the agreement** covering all essential terms:
   - Parties and effective date
   - Scope of work / deliverables
   - Compensation and payment schedule
   - Usage rights (platforms, duration, territory)
   - Exclusivity terms
   - Approval process
   - FTC disclosure compliance
   - Warranties and representations
   - Confidentiality
   - Indemnification
   - Termination clauses

5. **Save the contract.** Call `save_contract(conversation_id=..., ...)` with the
   drafted terms. Return the saved contract id.

## Output
Return a JSON object with:
{{
  "contract_id": <int or null>,
  "status": "drafted" | "error",
  "agreed_rate": <float>,
  "usage_rights_summary": "<brief summary>",
  "key_terms": {{
    "deliverables": "<description>",
    "compensation": "<amount and schedule>",
    "exclusivity": "<terms or none>",
    "disclosure": "<FTC disclosure requirement>"
  }},
  "legal_disclaimer": "These are templates, not legal documents. Seek legal counsel before execution."
}}

Return ONLY valid JSON. No markdown fences, no extra text.
"""


def get_contract_helper_agent() -> "Agent":
    """Return a CrewAI Agent for the Activate-phase contract helper."""
    prompt = _load_contract_helper_prompt()

    return Agent(
        role=prompt.get("Role") or "Contract Helper",
        goal=prompt.get("Goal") or (
            "Draft clear influencer agreements with scope, compensation, usage rights, "
            "exclusivity, and FTC disclosure. Always attach a legal-counsel note."
        ),
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_ACTIVATE_CONTRACT),
        tools=[get_conversation_details, get_brand_brief, save_contract, registry_get],
        verbose=True,
        allow_delegation=False,
    )


def get_contract_helper_task(
    conversation_id: int, agent: "Agent", brief_id: int = 1
) -> "Task":
    """Return a CrewAI Task for the contract helper.

    Args:
        conversation_id: The DB id of the negotiation conversation.
        agent: The contract helper agent.
        brief_id: The brand brief id.
    """
    description = CONTRACT_HELPER_TASK_DESCRIPTION
    description += f"\n\n## Conversation ID\n{conversation_id}"
    description += f"\n\n## Brief ID\n{brief_id}"

    return Task(
        description=description,
        expected_output=(
            "JSON object with: contract_id (int or null), status (drafted/error), "
            "agreed_rate (float), usage_rights_summary (string), key_terms (dict), "
            "legal_disclaimer (string)."
        ),
        agent=agent,
    )
