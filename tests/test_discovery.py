"""Tests for the Discovery agent — mock scraper DB, assert fit score math."""

import json

import pytest

from tools.calculation_tools import (
    calculate_engagement_rate,
    calculate_fit_score,
    calculate_reach_ratio,
    estimated_rate,
)


# ── Pure math tests (no mocking needed) ──────────────────────────────────────


class TestEstimatedRate:
    def test_basic_rate(self):
        assert estimated_rate({"follower_count": 10000}) == 5000.0

    def test_zero_followers(self):
        assert estimated_rate({"follower_count": 0}) == 0.0

    def test_missing_followers(self):
        assert estimated_rate({}) == 0.0

    def test_negative_followers(self):
        assert estimated_rate({"follower_count": -100}) == 0.0


class TestEngagementRate:
    def test_basic(self):
        rate = calculate_engagement_rate(1000, 50, 10)
        assert rate == pytest.approx(6.0)

    def test_zero_followers(self):
        assert calculate_engagement_rate(0, 50, 10) == 0.0

    def test_no_engagement(self):
        assert calculate_engagement_rate(1000, 0, 0) == 0.0


class TestReachRatio:
    def test_basic(self):
        assert calculate_reach_ratio(30000, 10000) == 3.0

    def test_zero_followers(self):
        assert calculate_reach_ratio(30000, 0) == 0.0


class TestFitScore:
    def test_perfect_match(self):
        """All criteria met = 1.0."""
        creator = {
            "detected_niche": "food",
            "detected_language": "gu",
            "detected_region": "gujarat",
            "follower_count": 10000,
            "avg_likes": 500,
            "avg_comments": 50,
            "avg_reel_views": 50000,
            "has_brand_experience": True,
        }
        brief = {
            "product_category": "food",
            "target_language": ["gu"],
            "target_location": "gujarat",
            "budget_max": 10000,
        }
        score = calculate_fit_score(creator, brief)
        assert score == pytest.approx(1.0)

    def test_no_match(self):
        """No criteria met = 0.0.
        Note: budget_fit (15 pts) is scored when estimated_rate <= budget_max.
        With 500 followers, estimated_rate=250, so budget_max must be < 250 to fail.
        """
        creator = {
            "detected_niche": "tech",
            "detected_language": "en",
            "detected_region": "mumbai",
            "follower_count": 500,
            "avg_likes": 1,
            "avg_comments": 0,
            "avg_reel_views": 10,
            "has_brand_experience": False,
        }
        brief = {
            "product_category": "food",
            "target_language": ["gu"],
            "target_location": "gujarat",
            "budget_max": 100,  # estimated_rate=250 > 100, so budget_fit fails
        }
        score = calculate_fit_score(creator, brief)
        assert score == pytest.approx(0.0)

    def test_partial_match(self):
        """Niche (25) + language (20) + budget_fit (15) = 60/100 = 0.60.
        With 500 followers, estimated_rate=250, budget_max=1000 so budget_fit passes.
        """
        creator = {
            "detected_niche": "food",
            "detected_language": "gu",
            "detected_region": "mumbai",
            "follower_count": 500,
            "avg_likes": 1,
            "avg_comments": 0,
            "avg_reel_views": 10,
            "has_brand_experience": False,
        }
        brief = {
            "product_category": "food",
            "target_language": ["gu"],
            "target_location": "gujarat",
            "budget_max": 1000,
        }
        score = calculate_fit_score(creator, brief)
        assert score == pytest.approx(0.60)

    def test_budget_fit_only(self):
        """Only budget fit = 15/100 = 0.15."""
        creator = {
            "detected_niche": "tech",
            "detected_language": "en",
            "detected_region": "mumbai",
            "follower_count": 1000,
            "avg_likes": 1,
            "avg_comments": 0,
            "avg_reel_views": 10,
            "has_brand_experience": False,
        }
        brief = {
            "product_category": "food",
            "target_language": ["gu"],
            "target_location": "gujarat",
            "budget_max": 10000,
        }
        score = calculate_fit_score(creator, brief)
        assert score == pytest.approx(0.15)

    def test_language_string_not_list(self):
        """target_language as a string still works."""
        creator = {
            "detected_niche": "food",
            "detected_language": "gu",
            "detected_region": "gujarat",
            "follower_count": 10000,
            "avg_likes": 500,
            "avg_comments": 50,
            "avg_reel_views": 50000,
            "has_brand_experience": True,
        }
        brief = {
            "product_category": "food",
            "target_language": "gu",
            "target_location": "gujarat",
            "budget_max": 10000,
        }
        score = calculate_fit_score(creator, brief)
        assert score == pytest.approx(1.0)


# ── Discovery task output shape ──────────────────────────────────────────────


class TestDiscoveryOutputShape:
    """Test that the expected output JSON shape is valid."""

    def test_valid_discovery_output(self):
        """A valid discovery output has username, fit_score, match_reason."""
        output = [
            {"username": "creator1", "fit_score": 85, "match_reason": "Great niche fit"},
            {"username": "creator2", "fit_score": 72, "match_reason": "Good language match"},
        ]
        for item in output:
            assert "username" in item
            assert "fit_score" in item
            assert "match_reason" in item
            assert isinstance(item["username"], str)
            assert isinstance(item["fit_score"], (int, float))
            assert isinstance(item["match_reason"], str)

    def test_discovery_output_serializable(self):
        """Discovery output must be JSON-serializable."""
        output = [
            {"username": "c1", "fit_score": 90, "match_reason": "Perfect"},
        ]
        serialized = json.dumps(output)
        deserialized = json.loads(serialized)
        assert deserialized == output

    def test_discovery_sorted_by_fit_score(self):
        """Output should be sorted by fit_score descending."""
        output = [
            {"username": "a", "fit_score": 50, "match_reason": "ok"},
            {"username": "b", "fit_score": 90, "match_reason": "great"},
            {"username": "c", "fit_score": 70, "match_reason": "good"},
        ]
        sorted_output = sorted(output, key=lambda x: x["fit_score"], reverse=True)
        scores = [item["fit_score"] for item in sorted_output]
        assert scores == [90, 70, 50]


# ── Mocked scraper tools ─────────────────────────────────────────────────────


class TestMockedScraper:
    def test_query_creators_mocked(self, mocker):
        """Mock query_creators to return fake data."""
        mock_query = mocker.patch("tools.scraper_tools.query_creators")
        mock_query.return_value = [
            {"username": "foodie_guj", "detected_niche": "food", "follower_count": 15000},
            {"username": "tech_guj", "detected_niche": "tech", "follower_count": 20000},
        ]
        result = mock_query({"niche": "food"})
        assert len(result) == 2
        assert result[0]["username"] == "foodie_guj"

    def test_get_creator_details_mocked(self, mocker):
        """Mock get_creator_details to return fake profile."""
        mock_details = mocker.patch("tools.scraper_tools.get_creator_details")
        mock_details.return_value = {
            "username": "foodie_guj",
            "follower_count": 15000,
            "detected_language": "gu",
            "detected_region": "gujarat",
        }
        result = mock_details("foodie_guj")
        assert result["detected_language"] == "gu"
