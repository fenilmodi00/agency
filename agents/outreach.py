"""Outreach agent — generates and (optionally) sends DM proposals to creators.

Safety:
- Always checks DM quota before sending.
- When send=False (default) the agent generates the DM message but never
  calls send_instagram_dm. This is the dry-run / approval gate mode.
- When send=True the agent will attempt to send and then save/log the result.
"""

from config import MODEL_OUTREACH
from llm_client import get_fireworks_llm

# Tools used by the outreach agent — imported exactly once at module level.
from tools.instagram_tools import send_instagram_dm
from tools.scraper_tools import get_creator_language
from tools.database_tools import save_conversation, log_dm, check_dm_quota

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


OUTREACH_PROMPT = """\
You are the Outreach Agent. Your job is to review a list of creator proposals \
and send a personalized direct message to each creator in their preferred language.

## Input
You will receive a JSON list of proposals. Each proposal contains at least:
- username: the creator's Instagram handle
- any additional context fields from the proposal stage

## Process (follow EXACTLY, step by step)

1. **Check DM quota first.** Call `check_dm_quota()`. It returns `(sent_today, MAX_DMS_PER_DAY)`.
   - If `sent_today >= MAX_DMS_PER_DAY`, STOP. Do NOT process any more proposals.
     Return the result for already-processed creators and set `"quota_exceeded": true`
     for any remaining.

2. **Get the creator's language.** Call `get_creator_language(username="<username>")`.
   Use the returned language for composing the DM. If the tool returns an empty
   list or no language, default to English.

3. **Compose the DM.** Write a warm, concise outreach message in the creator's
   language. The message should introduce the brand collaboration opportunity
   and invite the creator to respond.

4. **Sending decision** — THIS IS CRITICAL:
   - If `SEND_MODE` is **false** (the variable defined below):
     - DO NOT call `send_instagram_dm`.
     - Record the message text for review but mark `"sent": false`, `"dry_run": true`.
   - If `SEND_MODE` is **true**:
     - Call `send_instagram_dm(creator_username="<username>", message="<message>")`.
     - If the send succeeds, call both:
       - `save_conversation(brief_id=<brief_id>, creator_username="<username>", thread_id="<thread_id>", status="outreach_sent", last_message_text="<message>", last_message_direction="sent")`
       - `log_dm(creator_username="<username>", thread_id="<thread_id>", message_text="<message>", direction="sent")`
     - If the send fails, record the error in the output and skip save/log.

5. **Repeat** steps 1-4 for each proposal in order, stopping early if the DM
   quota is exhausted.

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
      "message": "<composed message>",
      "sent": true/false,
      "dry_run": true/false
    }},
    ...
  ],
  "quota_exceeded": true/false
}}

Return ONLY valid JSON. No markdown fences, no extra text.
"""


def get_outreach_agent(send: bool = False) -> "Agent":
    """Return a CrewAI Agent configured for creator outreach.

    Args:
        send: When True the agent is allowed to actually send DMs.
              When False (default) the agent generates messages but does not
              call send_instagram_dm — dry-run / approval mode.
    """
    tools = [
        send_instagram_dm,
        get_creator_language,
        save_conversation,
        log_dm,
        check_dm_quota,
    ]

    return Agent(
        role="Vernacular Creator Outreach Specialist",
        goal="Personalized DM outreach to regional creators in their native language. "
             "Always check DM quota before sending. Never send if quota is exceeded.",
        backstory=(
            "You are a specialist in vernacular creator outreach. You know how to "
            "compose warm, culturally-aware messages in regional languages. You are "
            "careful with rate limits and always respect the DM quota."
        ),
        llm=get_fireworks_llm(MODEL_OUTREACH),
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def get_outreach_task(
    proposals_json: str,
    agent: "Agent",
    brief_id: int = 1,
    send: bool = False,
) -> "Task":
    """Return a CrewAI Task for the outreach agent.

    Args:
        proposals_json: JSON string of the proposals to outreach.
        agent: The outreach agent returned by `get_outreach_agent()`.
        brief_id: Brand brief id used when saving conversations.
        send: If False, dry-run mode — no DMs are actually sent.
    """
    prompt = OUTREACH_PROMPT.format(send=str(send).lower(), brief_id=brief_id)

    return Task(
        description=f"{prompt}\n\n## Proposals\n{proposals_json}",
        expected_output=(
            "JSON object with 'results' array. Each result contains: "
            "username, thread_id, language, message, sent (bool), dry_run (bool). "
            "Top-level 'quota_exceeded' boolean."
        ),
        agent=agent,
    )