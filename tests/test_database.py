"""Tests for the Database class using an in-memory SQLite database."""

import json
import sqlite3

import pytest

from database import Database


@pytest.fixture
def db():
    """Create a fresh in-memory Database with schema applied."""
    d = Database(":memory:")
    d.init_db()
    return d


# ── brand_briefs CRUD ────────────────────────────────────────────────────────


class TestBrandBriefs:
    def test_insert_and_get_brief(self, db: Database):
        brief_id = db.insert_brief("Brand wants Gujarati food creators")
        assert brief_id is not None and brief_id > 0

        row = db.get_brief(brief_id)
        assert row is not None
        assert row["raw_brief"] == "Brand wants Gujarati food creators"
        assert row["parsed_brief"] is None

    def test_insert_with_parsed_brief(self, db: Database):
        parsed = json.dumps({"budget_min": 5000, "budget_max": 15000})
        brief_id = db.insert_brief("Raw text", parsed_brief=parsed)
        row = db.get_brief(brief_id)
        assert row["parsed_brief"] == parsed

    def test_get_brief_not_found(self, db: Database):
        assert db.get_brief(9999) is None

    def test_multiple_briefs(self, db: Database):
        id1 = db.insert_brief("Brief A")
        id2 = db.insert_brief("Brief B")
        assert id2 > id1
        assert db.get_brief(id1)["raw_brief"] == "Brief A"
        assert db.get_brief(id2)["raw_brief"] == "Brief B"


# ── campaign_suggestions CRUD ────────────────────────────────────────────────


class TestCampaignSuggestions:
    def test_insert_suggestion(self, db: Database):
        brief_id = db.insert_brief("Brief")
        sug_id = db.insert_suggestion(
            brief_id=brief_id,
            creator_username="test_user",
            fit_score=85.0,
            match_reason="Good niche fit",
            outreach_message="Hi!",
        )
        assert sug_id is not None and sug_id > 0

    def test_get_suggestions_by_brief_ordered(self, db: Database):
        brief_id = db.insert_brief("Brief")
        db.insert_suggestion(brief_id, "user_a", 50.0, "ok", "msg")
        db.insert_suggestion(brief_id, "user_b", 90.0, "great", "msg")
        db.insert_suggestion(brief_id, "user_c", 70.0, "decent", "msg")

        suggestions = db.get_suggestions_by_brief(brief_id)
        assert len(suggestions) == 3
        # Should be ordered by fit_score DESC
        scores = [s["fit_score"] for s in suggestions]
        assert scores == [90.0, 70.0, 50.0]

    def test_suggestions_empty_for_missing_brief(self, db: Database):
        assert db.get_suggestions_by_brief(9999) == []

    def test_suggestion_with_campaign_ideas(self, db: Database):
        brief_id = db.insert_brief("Brief")
        sug_id = db.insert_suggestion(
            brief_id=brief_id,
            creator_username="user",
            fit_score=75.0,
            match_reason="match",
            outreach_message="hello",
            campaign_ideas='["Reel series", "Tutorial"]',
        )
        row = db.get_suggestions_by_brief(brief_id)[0]
        assert row["campaign_ideas"] == '["Reel series", "Tutorial"]'


# ── conversations CRUD ───────────────────────────────────────────────────────


class TestConversations:
    def test_insert_and_get_conversation(self, db: Database):
        brief_id = db.insert_brief("Brief")
        conv_id = db.insert_conversation(
            brief_id=brief_id,
            creator_username="creator1",
            thread_id="thread_abc",
            status="outreach_sent",
            last_message_text="Hello!",
            last_message_direction="sent",
            last_message_count=1,
        )
        row = db.get_conversation(conv_id)
        assert row is not None
        assert row["creator_username"] == "creator1"
        assert row["status"] == "outreach_sent"

    def test_get_conversation_not_found(self, db: Database):
        assert db.get_conversation(9999) is None

    def test_get_conversations_by_status(self, db: Database):
        brief_id = db.insert_brief("Brief")
        db.insert_conversation(brief_id, "u1", "t1", "outreach_sent")
        db.insert_conversation(brief_id, "u2", "t2", "negotiating")
        db.insert_conversation(brief_id, "u3", "t3", "outreach_sent")

        sent = db.get_conversations_by_status("outreach_sent")
        assert len(sent) == 2
        negotiating = db.get_conversations_by_status("negotiating")
        assert len(negotiating) == 1

    def test_update_conversation_status(self, db: Database):
        brief_id = db.insert_brief("Brief")
        conv_id = db.insert_conversation(brief_id, "u1", "t1", "outreach_sent")
        updated = db.update_conversation_status(conv_id, "negotiating", agreed_rate=5000.0)
        assert updated is True

        row = db.get_conversation(conv_id)
        assert row["status"] == "negotiating"
        assert row["agreed_rate"] == 5000.0

    def test_update_conversation_status_not_found(self, db: Database):
        updated = db.update_conversation_status(9999, "accepted")
        assert updated is False

    def test_update_conversation_negotiation(self, db: Database):
        brief_id = db.insert_brief("Brief")
        conv_id = db.insert_conversation(brief_id, "u1", "t1", "outreach_sent")
        updated = db.update_conversation_negotiation(conv_id, "round 1 done", 2)
        assert updated is True

        row = db.get_conversation(conv_id)
        assert row["status"] == "negotiating"
        assert row["negotiation_history"] == "round 1 done"
        assert row["last_message_count"] == 2


# ── contracts CRUD ───────────────────────────────────────────────────────────


class TestContracts:
    def test_insert_and_get_contract(self, db: Database):
        brief_id = db.insert_brief("Brief")
        conv_id = db.insert_conversation(brief_id, "creator", "t1", "accepted")
        contract_id = db.insert_contract(
            conversation_id=conv_id,
            creator_username="creator",
            brand_name="TestBrand",
            contract_text="#ad Collaboration agreement",
            contract_type="paid",
            deliverables="2 Reels",
            usage_rights="6 months",
            timeline="30 days",
            asci_compliant=1,
        )
        row = db.get_contract(contract_id)
        assert row is not None
        assert row["contract_text"] == "#ad Collaboration agreement"
        assert row["contract_type"] == "paid"
        assert row["asci_compliant"] == 1

    def test_get_contract_not_found(self, db: Database):
        assert db.get_contract(9999) is None


# ── dm_log CRUD ──────────────────────────────────────────────────────────────


class TestDmLog:
    def test_insert_dm_log(self, db: Database):
        log_id = db.insert_dm_log("creator1", "thread_1", "Hello!", "sent")
        assert log_id is not None and log_id > 0

    def test_todays_dm_count(self, db: Database):
        db.insert_dm_log("u1", "t1", "msg1", "sent")
        db.insert_dm_log("u2", "t2", "msg2", "sent")
        db.insert_dm_log("u3", "t3", "msg3", "received")
        count = db.get_todays_dm_count()
        assert count == 3


# ── convenience join ─────────────────────────────────────────────────────────


class TestConversationDetails:
    def test_get_conversation_details(self, db: Database):
        brief_id = db.insert_brief("Brand brief text here")
        conv_id = db.insert_conversation(brief_id, "creator1", "t1", "outreach_sent")
        details = db.get_conversation_details(conv_id)
        assert details is not None
        assert details["creator_username"] == "creator1"
        assert details["raw_brief"] == "Brand brief text here"

    def test_get_conversation_details_not_found(self, db: Database):
        assert db.get_conversation_details(9999) is None


# ── edge cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_foreign_key_enforced(self, db: Database):
        """Inserting a suggestion with a non-existent brief_id should fail."""
        with pytest.raises(sqlite3.IntegrityError):
            db.insert_suggestion(brief_id=9999, creator_username="u", fit_score=1.0, match_reason="r", outreach_message="m")

    def test_conversation_status_check_constraint(self, db: Database):
        """Invalid status should be rejected by the CHECK constraint."""
        brief_id = db.insert_brief("Brief")
        with pytest.raises(sqlite3.IntegrityError):
            db.insert_conversation(brief_id, "u", "t", "invalid_status")

    def test_dm_log_direction_check(self, db: Database):
        """Invalid direction should be rejected."""
        with pytest.raises(sqlite3.IntegrityError):
            db.insert_dm_log("u", "t", "msg", "invalid_direction")
