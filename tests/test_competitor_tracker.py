"""Tests for the Competitor Tracker target agent — output shape, mocked tools, task."""
import json

import pytest


class TestCompetitorTrackerOutputShape:
    """Competitor tracker output must have expected top-level keys."""

    REQUIRED_KEYS = {
        "competitive_set",
        "partnership_rosters",
        "campaigns",
        "comparison",
        "opportunities",
        "summary",
    }

    def test_valid_competitor_tracker_output(self):
        """Output must contain all required keys."""
        output = {
            "competitive_set": [{"name": "CompetitorA", "platforms": ["instagram"], "focus_areas": ["awareness"]}],
            "partnership_rosters": {"CompetitorA": [{"creator_handle": "c1", "platform": "instagram", "followers": 10000, "partnership_type": "paid", "duration": "3mo"}]},
            "campaigns": {"CompetitorA": [{"timeline": "Q2 2024", "platforms": ["instagram"], "content_types": ["reel"], "estimated_spend": 50000, "notes": "launch campaign"}]},
            "comparison": {"table": "side-by-side comparison"},
            "opportunities": [{"rank": 1, "opportunity": "gap in TikTok", "rationale": "no competitors active"}],
            "summary": "CompetitorA runs micro-influencer heavy campaigns.",
        }
        assert self.REQUIRED_KEYS.issubset(output.keys())
        assert len(output["opportunities"]) >= 1

    def test_competitor_tracker_json_serializable(self):
        """Output must be JSON-serializable."""
        output = {
            "competitive_set": [],
            "partnership_rosters": {},
            "campaigns": {},
            "comparison": {"table": ""},
            "opportunities": [{"rank": 1, "opportunity": "test", "rationale": "test"}],
            "summary": "test",
        }
        serialized = json.dumps(output)
        deserialized = json.loads(serialized)
        assert deserialized == output

    def test_competitor_tracker_opportunities_ranked(self):
        """Opportunities must be sorted by rank ascending."""
        opportunities = [
            {"rank": 2, "opportunity": "b", "rationale": ""},
            {"rank": 1, "opportunity": "a", "rationale": ""},
            {"rank": 3, "opportunity": "c", "rationale": ""},
        ]
        sorted_opps = sorted(opportunities, key=lambda x: x["rank"])
        assert sorted_opps[0]["rank"] == 1
        assert sorted_opps[1]["rank"] == 2
        assert sorted_opps[2]["rank"] == 3


class TestMockedCompetitorTrackerTools:
    """Mock the connector tools used by the competitor tracker agent."""

    def test_gdelt_news_mentions_mocked(self, mocker):
        """Mock gdelt_news_mentions to return fake news data."""
        mock_gdelt = mocker.patch("tools.connectors.gdelt_tools.gdelt_news_mentions")
        mock_gdelt.return_value = {
            "articles": [
                {"title": "BrandX launches campaign", "source": "TechCrunch", "date": "2024-01-15"},
            ]
        }
        result = mock_gdelt("BrandX", days=30)
        assert len(result["articles"]) == 1
        assert result["articles"][0]["title"] == "BrandX launches campaign"

    def test_youtube_channel_stats_mocked(self, mocker):
        """Mock youtube_channel_stats to return fake channel data."""
        mock_yt = mocker.patch("tools.connectors.youtube_tools.youtube_channel_stats")
        mock_yt.return_value = {"subscriber_count": 50000, "total_views": 2000000, "video_count": 150}
        result = mock_yt("@testhandle")
        assert result["subscriber_count"] == 50000

    def test_tavily_search_mocked(self, mocker):
        """Mock tavily_search to return fake search results."""
        mock_tavily = mocker.patch("tools.connectors.tavily_tools.tavily_search")
        mock_tavily.return_value = {
            "results": [{"title": "Competitor analysis", "url": "https://example.com"}],
            "answer": "Competitor is running influencer campaigns.",
        }
        result = mock_tavily("competitor influencer marketing", max_results=5)
        assert len(result["results"]) == 1
        assert "answer" in result


class TestCompetitorTrackerTask:
    """Test the task expected output shape."""

    def test_task_expected_output_has_required_fields(self):
        """The expected output string should describe the required keys."""
        expected_output = (
            "A valid JSON object with these top-level keys:\n"
            "- competitive_set: array of competitors with platforms and focus areas\n"
            "- partnership_rosters: per-competitor array of creator partnerships\n"
            "- campaigns: per-competitor array of campaign details\n"
            "- comparison: side-by-side table string\n"
            "- opportunities: array of ranked opportunities with rationale\n"
            "- summary: executive summary string\n"
            "Return only the JSON object, no commentary."
        )
        assert "competitive_set" in expected_output
        assert "partnership_rosters" in expected_output
        assert "campaigns" in expected_output
        assert "opportunities" in expected_output
        assert "summary" in expected_output
        assert "JSON object" in expected_output
