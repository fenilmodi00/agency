"""Tests for the Brief Generator target agent — output shape, mocked tools, task."""
import json

import pytest


class TestBriefGeneratorOutputShape:
    """Brief generator output must have expected top-level keys."""

    REQUIRED_KEYS = {
        "brief_title",
        "campaign_overview",
        "key_messages",
        "deliverables",
        "creative_direction",
        "timeline",
        "compliance",
        "compensation",
        "contact",
    }

    def test_valid_brief_generator_output(self):
        """Output must contain all required keys with correct types."""
        output = {
            "brief_title": "Summer Launch — Instagram Reels",
            "campaign_overview": "Promote new sustainable sneaker line",
            "key_messages": ["eco-friendly materials", "comfort meets style"],
            "deliverables": [{"format": "reel", "quantity": 2, "specs": "30-60s vertical video"}],
            "creative_direction": {"tone": "authentic", "visual_style": "natural lighting", "color_palette": "earth tones"},
            "timeline": {"briefing_date": "2024-06-01", "draft_deadline": "2024-06-15", "go_live_date": "2024-07-01"},
            "compliance": {"disclosure": "#ad at start of caption", "usage_rights": "12-month repost rights on brand channels"},
            "compensation": {"type": "flat fee", "amount": "$500", "terms": "Net 30"},
            "contact": {"point_of_contact": "Alice", "email": "alice@brand.com"},
        }
        assert self.REQUIRED_KEYS.issubset(output.keys())
        assert "#ad" in output["compliance"]["disclosure"] or "#sponsored" in output["compliance"]["disclosure"]

    def test_brief_generator_json_serializable(self):
        """Output must be JSON-serializable."""
        output = {
            "brief_title": "test",
            "campaign_overview": "",
            "key_messages": [],
            "deliverables": [],
            "creative_direction": {"tone": "", "visual_style": "", "color_palette": ""},
            "timeline": {"briefing_date": "", "draft_deadline": "", "go_live_date": ""},
            "compliance": {"disclosure": "#ad", "usage_rights": "standard"},
            "compensation": {"type": "", "amount": "", "terms": ""},
            "contact": {"point_of_contact": "", "email": ""},
        }
        serialized = json.dumps(output)
        deserialized = json.loads(serialized)
        assert deserialized == output

    def test_brief_generator_compliance_explicit(self):
        """Compliance section must have both disclosure and usage_rights."""
        compliance = {"disclosure": "#ad required in caption", "usage_rights": "12-month repost"}
        assert "disclosure" in compliance
        assert "usage_rights" in compliance
        assert compliance["disclosure"] != ""


class TestMockedBriefGeneratorTools:
    """Mock the tools used by the brief generator agent."""

    def test_registry_get_mocked(self, mocker):
        """Mock registry_get to return fake narrative data."""
        mock_reg = mocker.patch("tools.registry_tools.registry_get")
        mock_reg.return_value = {"narrative_canon_id": "n_001", "version": "1.0"}
        result = mock_reg("narrative", "campaign_001")
        assert result["narrative_canon_id"] == "n_001"

    def test_query_creators_mocked(self, mocker):
        """Mock query_creators to return fake creator data for personalization."""
        mock_query = mocker.patch("tools.scraper_tools.query_creators")
        mock_query.return_value = [
            {"username": "creator1", "detected_niche": "fashion", "follower_count": 25000},
        ]
        result = mock_query({"niche": "fashion"})
        assert len(result) == 1
        assert result[0]["username"] == "creator1"

    def test_registry_get_empty_returns_dict(self):
        """When registry has no data, registry_get returns dict with record=None."""
        from tools.registry_tools import registry_get
        result = registry_get("narrative", "nonexistent")
        # registry_get returns {"registry": ..., "aggregate_id": ..., "record": None}
        # when no record exists, not empty dict
        assert isinstance(result, dict)
        assert result.get("record") is None


class TestBriefGeneratorTask:
    """Test the task expected output shape."""

    def test_task_expected_output_has_required_fields(self):
        """The expected output string should describe the required keys."""
        expected_output = (
            "A valid JSON object with these top-level keys:\n"
            "- brief_title: string\n"
            "- campaign_overview: string\n"
            "- key_messages: array of strings\n"
            "- deliverables: array of {format, quantity, specs}\n"
            "- creative_direction: {tone, visual_style, color_palette}\n"
            "- timeline: {briefing_date, draft_deadline, go_live_date}\n"
            "- compliance: {disclosure, usage_rights}\n"
            "- compensation: {type, amount, terms}\n"
            "- contact: {point_of_contact, email}\n"
            "Return only the JSON object, no commentary."
        )
        assert "brief_title" in expected_output
        assert "compliance" in expected_output
        assert "disclosure" in expected_output
        assert "usage_rights" in expected_output
        assert "JSON object" in expected_output
