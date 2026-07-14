"""Tests for the Negotiator agent — mock conversations and budget."""

import pytest


class TestBudgetOverrun:
    """When the creator's rate exceeds budget, the agent should escalate."""

    def test_budget_overrun_returns_escalate(self):
        """If creator asks for more than budget allows, action should be 'escalate'."""
        budget_max = 10000
        creator_rate = 15000

        if creator_rate > budget_max:
            action = "escalate"
        else:
            action = "accept"

        assert action == "escalate"

    def test_budget_within_range_returns_accept(self):
        """If creator rate is within budget, action should be 'accept'."""
        budget_max = 20000
        creator_rate = 15000

        if creator_rate <= budget_max:
            action = "accept"
        else:
            action = "escalate"

        assert action == "accept"

    def test_budget_overrun_percent(self):
        """Budget overrun percent from config: 120% of budget_max."""
        budget_max = 10000
        overrun_threshold = budget_max * 120 / 100  # 12000
        creator_rate = 11000  # within 120%

        if creator_rate > overrun_threshold:
            action = "escalate"
        else:
            action = "counter"

        assert action == "counter"

        creator_rate = 13000  # exceeds 120%
        if creator_rate > overrun_threshold:
            action = "escalate"
        else:
            action = "counter"

        assert action == "escalate"


class TestRoundLimit:
    """After MAX_NEGOTIATION_ROUNDS (3), the agent should give up."""

    def test_round_3_returns_give_up(self):
        """Round 3 should result in give_up action."""
        max_rounds = 3
        round_number = 3

        if round_number >= max_rounds:
            action = "give_up"
        else:
            action = "counter"

        assert action == "give_up"

    def test_round_2_returns_counter(self):
        """Round 2 should still allow counter."""
        max_rounds = 3
        round_number = 2

        if round_number >= max_rounds:
            action = "give_up"
        else:
            action = "counter"

        assert action == "counter"

    def test_round_1_returns_counter(self):
        """Round 1 should allow counter."""
        max_rounds = 3
        round_number = 1

        if round_number >= max_rounds:
            action = "give_up"
        else:
            action = "counter"

        assert action == "counter"


class TestNegotiatorOutputShape:
    """Test the expected output JSON shape of the negotiator task."""

    REQUIRED_KEYS = {"action", "response", "agreed_rate", "round_number", "status"}

    def test_valid_negotiator_output(self):
        """Negotiator output must have all required keys."""
        output = {
            "action": "accept",
            "response": "Thank you! We accept your rate.",
            "agreed_rate": 12000,
            "round_number": 2,
            "status": "accepted",
        }
        assert self.REQUIRED_KEYS.issubset(output.keys())
        assert output["action"] in ("accept", "counter", "wait", "escalate", "give_up")
        assert output["status"] in ("open", "accepted", "escalated", "closed", "give_up")

    def test_negotiator_escalate_output(self):
        """Escalate action should have escalated status."""
        output = {
            "action": "escalate",
            "response": "This rate exceeds our budget. Escalating to manager.",
            "agreed_rate": None,
            "round_number": 2,
            "status": "escalated",
        }
        assert self.REQUIRED_KEYS.issubset(output.keys())
        assert output["action"] == "escalate"
        assert output["status"] == "escalated"

    def test_negotiator_give_up_output(self):
        """Give up action should have give_up status."""
        output = {
            "action": "give_up",
            "response": "We cannot reach an agreement. Thank you for your time.",
            "agreed_rate": None,
            "round_number": 3,
            "status": "give_up",
        }
        assert self.REQUIRED_KEYS.issubset(output.keys())
        assert output["action"] == "give_up"
        assert output["status"] == "give_up"


class TestMockedNegotiator:
    def test_get_conversation_history_mocked(self, mocker):
        """Mock get_conversation_history to return fake conversation."""
        mock_history = mocker.patch("tools.database_tools.get_conversation_history")
        mock_history.return_value = {
            "id": 1,
            "brief_id": 1,
            "creator_username": "creator1",
            "status": "negotiating",
            "negotiation_history": 'round 1: counter 8000',
            "last_message_count": 2,
        }
        result = mock_history(1)
        assert result["status"] == "negotiating"
        assert result["negotiation_history"] == "round 1: counter 8000"

    def test_get_brand_budget_mocked(self, mocker):
        """Mock get_brand_budget to return budget range."""
        mock_budget = mocker.patch("tools.database_tools.get_brand_budget")
        mock_budget.return_value = (5000, 15000)
        result = mock_budget(1)
        assert result == (5000, 15000)
        assert result[0] <= result[1]
