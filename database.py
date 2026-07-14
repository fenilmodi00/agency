"""SQLite database layer with WAL mode and context-managed connections."""

import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    """SQLite wrapper for the vernacular-creator-agents database."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._mem_conn: Optional[sqlite3.Connection] = None

    def _connect(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:")
                self._mem_conn.row_factory = sqlite3.Row
                self._mem_conn.execute("PRAGMA foreign_keys = ON")
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        """Create tables from db/schema.sql."""
        schema_path = Path(__file__).parent / "db" / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        conn = self._connect()
        conn.executescript(sql)
        if self.db_path != ":memory:":
            conn.close()

    # -- brand_briefs --

    def insert_brief(self, raw_brief: str, parsed_brief: Optional[str] = None) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO brand_briefs (raw_brief, parsed_brief) VALUES (?, ?)",
                (raw_brief, parsed_brief),
            )
            conn.commit()
            return cur.lastrowid

    def get_brief(self, brief_id: int) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM brand_briefs WHERE id = ?", (brief_id,)
            ).fetchone()
        return dict(row) if row else None

    # -- campaign_suggestions --

    def insert_suggestion(
        self,
        brief_id: int,
        creator_username: str,
        fit_score: Optional[float],
        match_reason: Optional[str],
        outreach_message: Optional[str],
        campaign_ideas: Optional[str] = None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO campaign_suggestions
                   (brief_id, creator_username, fit_score, match_reason, outreach_message, campaign_ideas)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (brief_id, creator_username, fit_score, match_reason, outreach_message, campaign_ideas),
            )
            conn.commit()
            return cur.lastrowid

    def get_suggestions_by_brief(self, brief_id: int) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM campaign_suggestions WHERE brief_id = ? ORDER BY fit_score DESC",
                (brief_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # -- conversations --

    def insert_conversation(
        self,
        brief_id: int,
        creator_username: str,
        thread_id: Optional[str],
        status: str,
        last_message_text: Optional[str] = None,
        last_message_direction: Optional[str] = None,
        last_message_count: int = 0,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO conversations
                   (brief_id, creator_username, thread_id, status, last_message_text,
                    last_message_direction, last_message_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (brief_id, creator_username, thread_id, status,
                 last_message_text, last_message_direction, last_message_count),
            )
            conn.commit()
            return cur.lastrowid

    def get_conversation(self, conversation_id: int) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_conversations_by_status(self, status: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations WHERE status = ?", (status,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_conversations_by_statuses(self, statuses: tuple[str, ...]) -> list[dict]:
        """Return all conversations matching any of the given statuses."""
        placeholders = ",".join("?" for _ in statuses)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM conversations WHERE status IN ({placeholders})",
                statuses,
            ).fetchall()
        return [dict(r) for r in rows]

    def update_conversation_status(
        self,
        conversation_id: int,
        status: str,
        agreed_rate: Optional[float] = None,
        negotiation_history: Optional[str] = None,
    ) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """UPDATE conversations
                   SET status = ?, agreed_rate = COALESCE(?, agreed_rate),
                       negotiation_history = COALESCE(?, negotiation_history),
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (status, agreed_rate, negotiation_history, conversation_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def update_conversation_negotiation(
        self, conversation_id: int, negotiation_history: str, last_message_count: int
    ) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """UPDATE conversations
                   SET negotiation_history = ?, last_message_count = ?,
                       status = 'negotiating', updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (negotiation_history, last_message_count, conversation_id),
            )
            conn.commit()
            return cur.rowcount > 0

    # -- contracts --

    def insert_contract(
        self,
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
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO contracts
                   (conversation_id, creator_username, brand_name, contract_text,
                    contract_type, deliverables, usage_rights, timeline, asci_compliant)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (conversation_id, creator_username, brand_name, contract_text,
                 contract_type, deliverables, usage_rights, timeline, asci_compliant),
            )
            conn.commit()
            return cur.lastrowid

    def get_contract(self, contract_id: int) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM contracts WHERE id = ?", (contract_id,)
            ).fetchone()
        return dict(row) if row else None

    # -- dm_log --

    def insert_dm_log(
        self, creator_username: str, thread_id: Optional[str], message_text: str, direction: str
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO dm_log (creator_username, thread_id, message_text, direction) VALUES (?, ?, ?, ?)",
                (creator_username, thread_id, message_text, direction),
            )
            conn.commit()
            return cur.lastrowid

    def get_todays_dm_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM dm_log WHERE date(sent_at) = date('now')"
            ).fetchone()
        return row["cnt"]

    # -- convenience join --

    def get_conversation_details(self, conversation_id: int) -> Optional[dict]:
        """JOIN conversations with brand_briefs to return creator_username + raw_brief."""
        with self._connect() as conn:
            row = conn.execute(
                """SELECT c.*, b.raw_brief
                   FROM conversations c
                   JOIN brand_briefs b ON c.brief_id = b.id
                   WHERE c.id = ?""",
                (conversation_id,),
            ).fetchone()
        return dict(row) if row else None