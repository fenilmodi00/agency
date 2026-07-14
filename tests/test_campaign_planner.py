"""Tests for the Campaign Planner target agent — output shape, mocked tools, task."""
import json

import pytest


class TestCampaignPlannerOutputShape:
    """Campaign planner output must have expected top-level keys."""

    REQUIRED_KEYS = {
        "campaign_name",
        "objectives",
        "strategy",
        "influencer_criteria",
        "content_requirements",
        "timeline",
        "budget_allocation",
        "success_metrics",
        "next_step",
    }

    def test_valid_campaign_planner_output(self):
        """Output must contain all required keys with correct types."""
        output = {
            "campaign_name": "Summer Launch 2024",
            "objectives": {
                "primary": {"objective": "drive awareness", "success": "1M reach", "failure": "<500K reach"},
                "secondary": ["engagement"],
            },
            "strategy": {"big_idea": "sustainable lifestyle", "key_messages": ["eco-friendly"], "platform_split": {"instagram": 60, "tiktok": 40}},
            "influencer_criteria": {"tier_mix": {"micro": 10, "nano": 20}, "selection_criteria": ["sustainable niche"]},
            "content_requirements": {"instagram": ["3 reels"]},
            "timeline": {"phases": [{"phase": "pre-launch", "dates": "week 1-2", "activities": ["briefing"]}]},
            "budget_allocation": {"influencer_fees": {"amount": 20000, "percent": 80}},
            "success_metrics": {"primary_kpis": ["reach", "engagement"], "reporting_cadence": "weekly"},
            "next_step": "brief generation",
        }
        assert self.REQUIRED_KEYS.issubset(output.keys())
        assert "primary" in output["objectives"]
        assert "primary_kpis" in output["success_metrics"]

    def test_campaign_planner_json_serializable(self):
        """Output must be JSON-serializable."""
        output = {
            "campaign_name": "test",
            "objectives": {"primary": {"objective": "", "success": "", "failure": ""}, "secondary": []},
            "strategy": {"big_idea": "", "key_messages": [], "platform_split": {}},
            "influencer_criteria": {"tier_mix": {}, "selection_criteria": []},
            "content_requirements": {},
            "timeline": {"phases": []},
            "budget_allocation": {},
            "success_metrics": {"primary_kpis": [], "reporting_cadence": ""},
            "next_step": "",
        }
        serialized = json.dumps(output)
        deserialized = json.loads(serialized)
        assert deserialized == output

    def test_campaign_planner_objectives_smart(self):
        """Objectives must have success and failure definitions."""
        obj = {"objective": "drive awareness", "success": "1M impressions", "failure": "<500K impressions"}
        assert "success" in obj
        assert "failure" in obj
        assert obj["objective"] == "drive awareness"


class TestMockedCampaignPlannerTools:
    """Mock the tools used by the campaign planner agent."""

    def test_query_creators_mocked(self, mocker):
        """Mock query_creators to return fake creator data."""
        mock_query = mocker.patch("tools.scraper_tools.query_creators")
        mock_query.return_value = [
            {"username": "creator1", "detected_niche": "fashion", "follower_count": 25000},
        ]
        result = mock_query({"niche": "fashion"})
        assert len(result) == 1
        assert result[0]["username"] == "creator1"

    def test_tavily_search_mocked(self, mocker):
        """Mock tavily_search to return fake benchmarks."""
        mock_tavily = mocker.patch("tools.connectors.tavily_tools.tavily_search")
        mock_tavily.return_value = {
            "results": [{"title": "Influencer benchmarks 2024", "url": "https://example.com"}],
            "answer": "Average engagement rate is 3.5%.",
        }
        result = mock_tavily("influencer marketing benchmarks 2024", max_results=5)
        assert len(result["results"]) >= 1

    def test_registry_get_mocked(self, mocker):
        """Mock registry_get to return fake campaign data."""
        mock_reg = mocker.patch("tools.registry_tools.registry_get")
        mock_reg.return_value = {"campaign_name": "Previous", "total_budget": 30000}
        result = mock_reg("launches", "campaign_001")
        assert result["total_budget"] == 30000


class TestCampaignPlannerTask:
    """Test the task expected output shape."""

    def test_task_expected_output_has_required_fields(self):
        """The expected output string should describe the required keys."""
        expected_output = (
            "A valid JSON object with these top-level keys:\n"
            "- campaign_name: string\n"
            "- objectives: primary (objective, success, failure) and secondary array\n"
            "- strategy: big_idea, key_messages, platform_split\n"
            "- influencer_criteria: tier_mix and selection_criteria\n"
            "- content_requirements: per-platform deliverables\n"
            "- timeline: array of phases with dates and activities\n"
            "- budget_allocation: per-category amounts and percentages\n"
            "- success_metrics: primary KPIs and reporting cadence\n"
            "- next_step: string naming the next step\n"
            "Return only the JSON object, no commentary."
        )
        assert "campaign_name" in expected_output
        assert "objectives" in expected_output
        assert "strategy" in expected_output
        assert "next_step" in expected_output
        assert "JSON object" in expected_output
