"""Activate outreach manager — sends personalized DMs with quota + consent checks.

Safety:
- Always checks DM quota before sending.
- Always checks registry_get("consent", creator_id) before sending.
- When send=False (default) the agent generates DMs but never sends.
- When send=True the agent attempts to send after quota + consent checks.
"""

from pathlib import Path

from config import MODEL_ACTIVATE_OUTREACH
from llm_client import get_fireworks_llm

from tools.instagram_tools import send_instagram_dm
from tools.scraper_tools import get_creator_language
from tools.database_tools import save_conversation, log_dm, check_dm_quota
from tools.registry_tools import registry_get, registry_propose

try:
    from crewai import Agent, Task
except ImportError:
    class Agent:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Task:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)


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


def _load_outreach_manager_prompt() -> dict:
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "prompts" / "outreach_manager_prompt.txt"
    )
    text = path.read_text(encoding="utf-8")
    return _parse_prompt_sections(text)


OUTREACH_MANAGER_PROMPT_EXTRA = """\
## Input
You will receive a JSON list of proposals. Each proposal contains at least:
- username: the creator's Instagram handle
- any additional context fields from the proposal stage

## Process (follow EXACTLY, step by step)

1. **Check consent registry first.** Call `registry_get("consent", "<creator_username>")`.
   - If the returned dict contains a `"status"` key with value `"suppressed"` or
     `"blocked"`, SKIP this creator entirely. Do NOT send a DM. Do NOT compose a
     message. Log the skip and set `"consent_blocked": true` in the output.
   - If consent is absent or granted, proceed to step 2.

2. **Check DM quota.** Call `check_dm_quota()`. It returns `(sent_today, MAX_DMS_PER_DAY)`.
   - If `sent_today >= MAX_DMS_PER_DAY`, STOP. Do NOT process any more proposals.
     Set `"quota_exceeded": true` for remaining creators.

3. **Get the creator's language.** Call `get_creator_language(username="<username>")`.
   Use the returned language for composing the DM. Default to English if empty.

4. **Compose the DM.** Write a warm, concise outreach message in the creator's
   language introducing the brand collaboration opportunity.

5. **Sending decision** — THIS IS CRITICAL:
   - If `SEND_MODE` is **false**: DO NOT call `send_instagram_dm`. Record the
     message text but mark `"sent": false`, `"dry_run": true`.
   - If `SEND_MODE` is **true**:
     - Call `send_instagram_dm(creator_username="<username>", message="<message>")`.
     - If the send succeeds, call both:
       - `save_conversation(...)`
       - `log_dm(...)`
     - If the send fails, record the error and skip save/log.

## Send Mode
SEND_MODE = {send}

## Brief ID
BRIEF_ID = {brief_id}

## Output
Return a JSON object with this structure:
{{
  "results": [
    {{
      "username": "<creator_username>",
      "thread_id": "<thread_id or null>",
      "language": "<detected_language or 'en'>",
      "message": "<composed message or '' if consent_blocked>",
      "sent": true/false,
      "dry_run": true/false,
      "consent_blocked": true/false
    }},
    ...
  ],
  "quota_exceeded": true/false
}}

Return ONLY valid JSON. No markdown fences, no extra text.
"""


def get_outreach_manager_agent(send: bool = False) -> "Agent":
    """Return a CrewAI Agent for Activate-phase outreach management.

    Args:
        send: When True the agent is allowed to send DMs (after quota + consent checks).
              When False (default) dry-run mode — messages composed but never sent.
    """
    prompt = _load_outreach_manager_prompt()

    tools = [
        send_instagram_dm,
        get_creator_language,
        save_conversation,
        log_dm,
        check_dm_quota,
        registry_get,
        registry_propose,
    ]

    return Agent(
        role=prompt.get("Role") or "Outreach Manager",
        goal=prompt.get("Goal") or (
            "Send personalized DMs to creators in their preferred language. "
            "Always check DM quota before sending. Check registry consent first."
        ),
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_ACTIVATE_OUTREACH),
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def get_outreach_manager_task(
    proposals_json: str,
    agent: "Agent",
    brief_id: int = 1,
    send: bool = False,
) -> "Task":
    """Return a CrewAI Task for the outreach manager agent.

    Args:
        proposals_json: JSON string of proposals to outreach.
        agent: The outreach manager agent.
        brief_id: Brand brief id for saving conversations.
        send: If False, dry-run — no DMs are actually sent.
    """
    description = OUTREACH_MANAGER_PROMPT_EXTRA.format(
        send=str(send).lower(), brief_id=brief_id
    )
    description += f"\n\n## Proposals\n{proposals_json}"

    return Task(
        description=description,
        expected_output=(
            "JSON object with 'results' array. Each result: "
            "username, thread_id, language, message, sent (bool), dry_run (bool), "
            "consent_blocked (bool). Top-level 'quota_exceeded' boolean."
        ),
        agent=agent,
    )
