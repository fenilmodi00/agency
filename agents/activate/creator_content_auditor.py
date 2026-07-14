"""Activate creator content auditor — STAR pre-publish gate with SHIP/FIX/BLOCK verdict."""

from pathlib import Path

from agents._base import Agent, Task, load_prompt

from config import MODEL_ACTIVATE_AUDITOR
from llm_client import get_fireworks_llm
from tools.registry_tools import registry_get
from tools.connectors.tavily_tools import tavily_extract


_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_creator_content_auditor_prompt() -> dict:
    return load_prompt(_PROMPTS_DIR, "creator_content_auditor_prompt.txt")


AUDITOR_TASK_DESCRIPTION = """\
You are reviewing one influencer content submission. Your job is to apply the STAR
framework and return a verdict.

## Input
You will receive:
- submission_text: the influencer's caption, script, or content description
- brief_context: the campaign brief for reference
- creator_info: dict with username, follower_count, niche, and any prior notes

## Process

1. **Fetch registry data.** Call `registry_get("creators", "<username>")` to
   pull the creator's dossier. If available, fold in the Suitability read.

2. **Fetch supporting context.** Use `tavily_extract(url)` to check any submitted
   links or references for claim verification.

3. **Score the four STAR dimensions:**
   - **Suitability (S1-S10):** Brand alignment, audience authenticity
   - **Trust (T1-T10):** Disclosure adequacy (T1), claim integrity (T2),
     brand safety (T3), overall trustworthiness
   - **Appeal (A1-A10):** Creative quality, production value, platform fit
   - **Return (R1-R10):** Forecast potential (pre-publish = na for R1-R6)

4. **Verify vetoes:**
   - STAR-T1: Material connection exists but disclosure is absent/inadequate → BLOCK
   - STAR-T2: Material factual/product claim is false or unsubstantiated → BLOCK
   - STAR-T3: Disqualifying brand-safety evidence → BLOCK
   - STAR-S2: Verified follower fraud → BLOCK
   - STAR-S6: Verified bought/coordinated engagement → BLOCK

5. **Compute the verdict:**
   - SHIP: No vetoes, all STAR items pass or partial
   - FIX: Revisions required (e.g. STAR-T1/STAR-T2 fixable)
   - BLOCK: Unfixable veto triggered

## Output
Return a JSON object with:
{{
  "verdict": "SHIP" | "FIX" | "BLOCK",
  "sqs": <0-100 integer or null if BLOCK>,
  "vetoes": ["<veto_id>", ...],
  "revision_notes": "<constructive feedback for creator or ''>",
  "score_breakdown": {{
    "suitability": <0-100>,
    "trust": <0-100>,
    "appeal": <0-100>,
    "return": <0-100>
  }}
}}

Return ONLY valid JSON. No markdown fences, no extra text.
"""


def get_creator_content_auditor_agent() -> "Agent":
    """Return a CrewAI Agent for the Activate-phase creator content auditor."""
    prompt = _load_creator_content_auditor_prompt()

    return Agent(
        role=prompt.get("Role") or "Creator Content Auditor",
        goal=prompt.get("Goal") or (
            "Run the STAR pre-publish gate. Score Trust and Appeal, "
            "fold in Suitability, compute SQS, and return SHIP/FIX/BLOCK verdict."
        ),
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_ACTIVATE_AUDITOR),
        tools=[registry_get, tavily_extract],
        verbose=True,
        allow_delegation=False,
    )


def get_creator_content_auditor_task(
    submission_text: str, agent: "Agent", brief_context: str = "", creator_info: str = ""
) -> "Task":
    """Return a CrewAI Task for the creator content auditor.

    Args:
        submission_text: The influencer's content submission (caption, script, etc.).
        agent: The creator content auditor agent.
        brief_context: The campaign brief for context.
        creator_info: JSON string with creator info.
    """
    description = AUDITOR_TASK_DESCRIPTION
    description += f"\n\n## Submission\n{submission_text}"
    if brief_context:
        description += f"\n\n## Brief Context\n{brief_context}"
    if creator_info:
        description += f"\n\n## Creator Info\n{creator_info}"

    return Task(
        description=description,
        expected_output=(
            "JSON object with: verdict (SHIP/FIX/BLOCK), sqs (0-100 or null), "
            "vetoes (list), revision_notes (string), score_breakdown (dict)."
        ),
        agent=agent,
    )
