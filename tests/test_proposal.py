"""Tests for the Proposal agent — mock creator content tools, assert output shape."""

import json

import pytest


class TestProposalOutputShape:
    """Test that the expected proposal output JSON has required fields."""

    REQUIRED_KEYS = {"campaign_ideas", "suggested_budget"}

    def test_valid_proposal_has_required_keys(self):
        """Each proposal must have campaign_ideas and suggested_budget."""
        proposal = {
            "creator_username": "foodie_guj",
            "campaign_ideas": ["Reel series", "Tutorial video"],
            "deliverables": ["2 Reels", "1 Story"],
            "suggested_budget": 15000,
            "timeline": "2 weeks",
            "notes": "Good fit for food niche",
        }
        assert self.REQUIRED_KEYS.issubset(proposal.keys())
        assert isinstance(proposal["campaign_ideas"], list)
        assert len(proposal["campaign_ideas"]) > 0
        assert isinstance(proposal["suggested_budget"], (int, float))
        assert proposal["suggested_budget"] > 0

    def test_proposal_json_serializable(self):
        """Proposal must be JSON-serializable."""
        proposals = [
            {
                "creator_username": "c1",
                "campaign_ideas": ["Idea A"],
                "deliverables": ["1 Reel"],
                "suggested_budget": 10000,
                "timeline": "1 week",
                "notes": "",
            }
        ]
        serialized = json.dumps(proposals)
        deserialized = json.loads(serialized)
        assert deserialized == proposals

    def test_proposal_array_shape(self):
        """Proposal output is a JSON array of objects."""
        proposals = [
            {
                "creator_username": "c1",
                "campaign_ideas": ["Idea 1"],
                "deliverables": ["1 Reel"],
                "suggested_budget": 5000,
                "timeline": "1 week",
                "notes": "",
            },
            {
                "creator_username": "c2",
                "campaign_ideas": ["Idea 2"],
                "deliverables": ["2 Reels"],
                "suggested_budget": 8000,
                "timeline": "2 weeks",
                "notes": "Premium creator",
            },
        ]
        assert len(proposals) == 2
        for p in proposals:
            assert self.REQUIRED_KEYS.issubset(p.keys())

    def test_proposal_missing_optional_keys(self):
        """Proposal without optional keys should still have required ones."""
        minimal = {
            "creator_username": "c1",
            "campaign_ideas": ["Idea"],
            "suggested_budget": 5000,
        }
        assert self.REQUIRED_KEYS.issubset(minimal.keys())

    def test_proposal_budget_is_numeric(self):
        """suggested_budget must be numeric (int or float)."""
        budgets = [5000, 15000.50, 0, -1]
        for b in budgets:
            assert isinstance(b, (int, float)), f"{b} is not numeric"


class TestMockedContentTools:
    def test_get_creator_content_summary_mocked(self, mocker):
        """Mock get_creator_content_summary to return fake data."""
        mock_summary = mocker.patch("tools.scraper_tools.get_creator_content_summary")
        mock_summary.return_value = [
            {"post_type": "reel", "avg_views": 45000},
            {"post_type": "static", "avg_views": 12000},
        ]
        result = mock_summary("foodie_guj")
        assert len(result) == 2
        assert result[0]["post_type"] == "reel"

    def test_get_creator_recent_posts_mocked(self, mocker):
        """Mock get_creator_recent_posts to return fake posts."""
        mock_posts = mocker.patch("tools.scraper_tools.get_creator_recent_posts")
        mock_posts.return_value = [
            {"id": "post1", "caption": "New recipe!", "likes": 1200},
            {"id": "post2", "caption": "Kitchen tour", "likes": 800},
        ]
        result = mock_posts("foodie_guj")
        assert len(result) == 2
        assert result[0]["caption"] == "New recipe!"
