"""CrewAI database tools wrapping the Database class.

All tools delegate to parameterized SQL inside database.py — no raw SQL strings
are accepted from agent output.
"""

from typing import Optional

from config import MAX_DMS_PER_DAY
from database import Database

# ---------------------------------------------------------------------------
# CrewAI @tool with fallback so the module imports regardless of install state
# ---------------------------------------------------------------------------
try:
    from crewai import tool
except ImportError:
    class _Tool:  # minimal fallback — provides .name, .description, .run
        def __init__(self, fn):
            self.fn = fn
            self.name = fn.__name__
            self.description = (fn.__doc__ or "").strip()
            __name__ = fn.__name__
            __doc__ = fn.__doc__

        def __call__(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

        def run(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

    def tool(fn):  # type: ignore[misc]
        return _Tool(fn)

# ---------------------------------------------------------------------------
# Global database instance — set via set_database() or auto-initialized with
# :memory: on first tool call. Tests *must* call set_database() before use.
# ---------------------------------------------------------------------------
_db: Optional[Database] = None


def set_database(db: Database):
    """Set the Database instance used by all tools. Call once at startup."""
    global _db
    _db = db


def _get_db() -> Database:
    global _db
    if _db is None:
        db = Database(":memory:")
        db.init_db()
        _db = db
    return _db


# ---------------------------------------------------------------------------
# Conversation tools
# ---------------------------------------------------------------------------

@tool
def save_conversation(
    brief_id: int,
    creator_username: str,
    thread_id: str,
    status: str = 'outreach_sent',
    last_message_text: str = '',
    last_message_direction: str = 'sent',
    last_message_count: int = 0,
) -> int:
    """Insert a new conversation record and return its id."""
    db = _get_db()
    return db.insert_conversation(
        brief_id=brief_id,
        creator_username=creator_username,
        thread_id=thread_id,
        status=status,
        last_message_text=last_message_text or None,
        last_message_direction=last_message_direction or None,
        last_message_count=last_message_count,
    )


@tool
def update_conversation_status(
    conversation_id: int,
    status: str,
    agreed_rate: Optional[float] = None,
    negotiation_history: Optional[str] = None,
) -> bool:
    """Update conversation status and optional negotiation fields. Returns True if a row was updated."""
    db = _get_db()
    return db.update_conversation_status(
        conversation_id=conversation_id,
        status=status,
        agreed_rate=agreed_rate,
        negotiation_history=negotiation_history,
    )


@tool
def update_conversation_negotiation(
    conversation_id: int,
    negotiation_history: str,
    last_message_count: int,
) -> bool:
    """Update negotiation history and message count, set status to 'negotiating'. Returns True if updated."""
    db = _get_db()
    return db.update_conversation_negotiation(
        conversation_id=conversation_id,
        negotiation_history=negotiation_history,
        last_message_count=last_message_count,
    )


@tool
def get_conversation_history(conversation_id: int) -> Optional[dict]:
    """Return the full conversation record including negotiation_history."""
    db = _get_db()
    return db.get_conversation(conversation_id)


@tool
def get_conversations_by_status(status: str) -> list:
    """Return all conversations matching the given status."""
    db = _get_db()
    return db.get_conversations_by_status(status)


# ---------------------------------------------------------------------------
# Brand brief tools
# ---------------------------------------------------------------------------

@tool
def get_brand_budget(brief_id: int) -> tuple:
    """Parse parsed_brief JSON and return (budget_min, budget_max). Returns (None, None) on failure."""
    db = _get_db()
    brief = db.get_brief(brief_id)
    if not brief or not brief.get("parsed_brief"):
        return (None, None)
    try:
        import json
        parsed = json.loads(brief["parsed_brief"])
        return (parsed.get("budget_min"), parsed.get("budget_max"))
    except (json.JSONDecodeError, TypeError):
        return (None, None)


@tool
def get_brand_brief(brief_id: int) -> Optional[dict]:
    """Return the full brand_brief record including raw_brief and parsed_brief."""
    db = _get_db()
    return db.get_brief(brief_id)


# ---------------------------------------------------------------------------
# Join tool
# ---------------------------------------------------------------------------

@tool
def get_conversation_details(conversation_id: int) -> Optional[dict]:
    """JOIN conversations with brand_briefs. Returns row with creator_username + raw_brief."""
    db = _get_db()
    return db.get_conversation_details(conversation_id)


# ---------------------------------------------------------------------------
# Contract tools
# ---------------------------------------------------------------------------

@tool
def save_contract(
    conversation_id: int,
    creator_username: str,
    brand_name: Optional[str],
    contract_text: str,
    contract_type: str,
    deliverables: Optional[str] = None,
    usage_rights: Optional[str] = None,
    timeline: Optional[str] = None,
    asci_compliant: int = 0,
) -> int:
    """Insert a contract record and return its id."""
    db = _get_db()
    return db.insert_contract(
        conversation_id=conversation_id,
        creator_username=creator_username,
        brand_name=brand_name,
        contract_text=contract_text,
        contract_type=contract_type,
        deliverables=deliverables,
        usage_rights=usage_rights,
        timeline=timeline,
        asci_compliant=asci_compliant,
    )


# ---------------------------------------------------------------------------
# DM quota tools
# ---------------------------------------------------------------------------

@tool
def check_dm_quota() -> tuple:
    """Return (sent_today, MAX_DMS_PER_DAY)."""
    db = _get_db()
    sent = db.get_todays_dm_count()
    return (sent, MAX_DMS_PER_DAY)


@tool
def log_dm(
    creator_username: str,
    thread_id: str,
    message_text: str,
    direction: str,
) -> int:
    """Log a sent/received DM and return the log entry id."""
    db = _get_db()
    return db.insert_dm_log(
        creator_username=creator_username,
        thread_id=thread_id,
        message_text=message_text,
        direction=direction,
    )