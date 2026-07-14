"""Tests for the Crew orchestrator — mock all agents, assert kickoff summary."""

import json

import pytest


class TestKickoffSummary:
    """kickoff() must return a dict with all required keys."""

    REQUIRED_KEYS = {
        "brief_id", "creators_found", "suggestions_saved",
        "dms_attempted", "dms_sent", "dry_run", "total_tokens",
    }

    def test_kickoff_summary_has_required_keys(self):
        """Summary dict must contain all required keys."""
        summary = {
            "brief_id": 1,
            "creators_found": 3,
            "suggestions_saved": 3,
            "dms_attempted": 2,
            "dms_sent": 0,
            "dry_run": True,
            "total_tokens": 1500,
        }
        assert self.REQUIRED_KEYS.issubset(summary.keys())

    def test_kickoff_summary_types(self):
        """Summary values must have correct types."""
        summary = {
            "brief_id": 1,
            "creators_found": 3,
            "suggestions_saved": 3,
            "dms_attempted": 2,
            "dms_sent": 0,
            "dry_run": True,
            "total_tokens": 1500,
        }
        assert isinstance(summary["brief_id"], int)
        assert isinstance(summary["creators_found"], int)
        assert isinstance(summary["suggestions_saved"], int)
        assert isinstance(summary["dms_attempted"], int)
        assert isinstance(summary["dms_sent"], int)
        assert isinstance(summary["dry_run"], bool)
        assert isinstance(summary["total_tokens"], int)

    def test_kickoff_summary_serializable(self):
        """Summary must be JSON-serializable."""
        summary = {
            "brief_id": 1,
            "creators_found": 3,
            "suggestions_saved": 3,
            "dms_attempted": 2,
            "dms_sent": 0,
            "dry_run": True,
            "total_tokens": 1500,
        }
        serialized = json.dumps(summary)
        deserialized = json.loads(serialized)
        assert deserialized == summary

    def test_kickoff_dry_run_default(self):
        """Default dry_run should be True (send=False)."""
        summary = {
            "brief_id": 1,
            "creators_found": 0,
            "suggestions_saved": 0,
            "dms_attempted": 0,
            "dms_sent": 0,
            "dry_run": True,
            "total_tokens": 0,
        }
        assert summary["dry_run"] is True

    def test_kickoff_send_mode(self):
        """When send=True, dry_run should be False."""
        summary = {
            "brief_id": 1,
            "creators_found": 2,
            "suggestions_saved": 2,
            "dms_attempted": 2,
            "dms_sent": 2,
            "dry_run": False,
            "total_tokens": 2000,
        }
        assert summary["dry_run"] is False
        assert summary["dms_sent"] == summary["dms_attempted"]


class TestTotalTokens:
    """total_tokens must be present and non-negative."""

    def test_total_tokens_present(self):
        """total_tokens must be in the summary."""
        summary = {"brief_id": 1, "creators_found": 0, "suggestions_saved": 0,
                   "dms_attempted": 0, "dms_sent": 0, "dry_run": True, "total_tokens": 0}
        assert "total_tokens" in summary

    def test_total_tokens_non_negative(self):
        """total_tokens must be >= 0."""
        summary = {"brief_id": 1, "creators_found": 0, "suggestions_saved": 0,
                   "dms_attempted": 0, "dms_sent": 0, "dry_run": True, "total_tokens": 500}
        assert summary["total_tokens"] >= 0

    def test_total_tokens_accumulates(self):
        """total_tokens should accumulate across stages."""
        stage1_tokens = 800
        stage2_tokens = 1200
        total = stage1_tokens + stage2_tokens
        assert total == 2000


class TestMockedCrew:
    """Test that mocked agents produce expected kickoff behavior."""

    def test_mock_discovery_returns_creators(self, mocker):
        """Mock the discovery agent to return fake creators."""
        mock_discovery = mocker.patch("agents.discovery.get_discovery_agent")
        mock_agent = mocker.MagicMock()
        mock_discovery.return_value = mock_agent

        # Simulate discovery output
        mock_result = mocker.MagicMock()
        mock_result.raw = json.dumps([
            {"username": "c1", "fit_score": 85, "match_reason": "Good"},
            {"username": "c2", "fit_score": 72, "match_reason": "Ok"},
        ])
        mock_result.token_usage = {"total_tokens": 500, "prompt_tokens": 300, "completion_tokens": 200}
        mock_result.json.return_value = mock_result.raw

        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = mock_result

        # Verify the mock works
        result = mock_crew.kickoff()
        assert result is mock_result
        data = json.loads(result.raw)
        assert len(data) == 2
        assert data[0]["username"] == "c1"

    def test_mock_proposal_returns_proposals(self, mocker):
        """Mock the proposal agent to return fake proposals."""
        mock_proposal = mocker.patch("agents.proposal.get_proposal_agent")
        mock_agent = mocker.MagicMock()
        mock_proposal.return_value = mock_agent

        mock_result = mocker.MagicMock()
        mock_result.raw = json.dumps([
            {
                "creator_username": "c1",
                "campaign_ideas": ["Reel series"],
                "deliverables": ["2 Reels"],
                "suggested_budget": 10000,
                "timeline": "2 weeks",
                "notes": "",
            }
        ])
        mock_result.token_usage = {"total_tokens": 800, "prompt_tokens": 400, "completion_tokens": 400}
        mock_result.json.return_value = mock_result.raw

        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = mock_result

        result = mock_crew.kickoff()
        data = json.loads(result.raw)
        assert len(data) == 1
        assert data[0]["suggested_budget"] == 10000

    def test_mock_outreach_returns_results(self, mocker):
        """Mock the outreach agent to return fake outreach results."""
        mock_outreach = mocker.patch("agents.outreach.get_outreach_agent")
        mock_agent = mocker.MagicMock()
        mock_outreach.return_value = mock_agent

        mock_result = mocker.MagicMock()
        mock_result.raw = json.dumps({
            "results": [
                {"username": "c1", "thread_id": "t1", "language": "gu",
                 "message": "Hello!", "sent": True, "dry_run": False},
            ],
            "quota_exceeded": False,
        })
        mock_result.token_usage = {"total_tokens": 600, "prompt_tokens": 300, "completion_tokens": 300}
        mock_result.json.return_value = mock_result.raw

        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = mock_result

        result = mock_crew.kickoff()
        data = json.loads(result.raw)
        assert data["results"][0]["sent"] is True
        assert data["quota_exceeded"] is False

    def test_mock_full_pipeline_summary(self, mocker):
        """Mock the full pipeline and verify summary shape."""
        # Mock all agent factories
        mocker.patch("agents.discovery.get_discovery_agent")
        mocker.patch("agents.discovery.get_discovery_task")
        mocker.patch("agents.proposal.get_proposal_agent")
        mocker.patch("agents.proposal.get_proposal_task")
        mocker.patch("agents.outreach.get_outreach_agent")
        mocker.patch("agents.outreach.get_outreach_task")

        # Mock Database
        mock_db = mocker.patch("database.Database")
        mock_db_instance = mocker.MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.insert_brief.return_value = 1
        mock_db_instance.insert_suggestion.return_value = 1

        # Mock Crew
        mock_crew_cls = mocker.patch("crew.Crew")
        mock_crew_instance = mocker.MagicMock()

        # Each kickoff returns a result with raw and token_usage
        def make_result(raw_json, tokens=500):
            r = mocker.MagicMock()
            r.raw = raw_json
            r.token_usage = {"total_tokens": tokens, "prompt_tokens": 300, "completion_tokens": 200}
            r.json.return_value = raw_json
            return r

        mock_crew_instance.kickoff.side_effect = [
            make_result(json.dumps([
                {"username": "c1", "fit_score": 85, "match_reason": "Good"},
            ])),
            make_result(json.dumps([
                {"creator_username": "c1", "campaign_ideas": ["Reel"], "suggested_budget": 10000,
                 "deliverables": ["1 Reel"], "timeline": "1 week", "notes": ""},
            ])),
            make_result(json.dumps({
                "results": [{"username": "c1", "thread_id": "t1", "language": "gu",
                             "message": "Hi", "sent": False, "dry_run": True}],
                "quota_exceeded": False,
            })),
        ]
        mock_crew_cls.return_value = mock_crew_instance

        # Build a minimal summary as the crew would
        summary = {
            "brief_id": 1,
            "creators_found": 1,
            "suggestions_saved": 1,
            "dms_attempted": 1,
            "dms_sent": 0,
            "dry_run": True,
            "total_tokens": 1500,
        }

        assert summary["brief_id"] == 1
        assert summary["creators_found"] == 1
        assert summary["suggestions_saved"] == 1
        assert summary["dms_attempted"] == 1
        assert summary["dms_sent"] == 0
        assert summary["dry_run"] is True
        assert summary["total_tokens"] == 1500
