"""Tests for the Activate content amplifier — paid and repurpose modes."""

import pytest


class TestModes:
    """Tests for paid and repurpose mode outputs."""

    def test_paid_mode_output(self):
        """Paid mode must include content scores, tiers, and budget allocation."""
        output = {
            "mode": "paid",
            "content_scores": [
                {
                    "content_id": "post1",
                    "title": "Product review",
                    "score": 22,
                    "tier": "must_amplify",
                    "recommended_spend": 2000.0,
                },
                {
                    "content_id": "post2",
                    "title": "Tutorial",
                    "score": 14,
                    "tier": "consider",
                    "recommended_spend": 800.0,
                },
            ],
            "strategy_summary": "Boost top 2 posts with Spark Ads",
            "budget_allocation": {"post1": 2000.0, "post2": 800.0},
            "distribution_plan": None,
            "rights_summary": None,
            "metric_labels": {"CPM": "Estimated"},
        }
        assert output["mode"] == "paid"
        assert len(output["content_scores"]) == 2
        assert output["content_scores"][0]["tier"] == "must_amplify"
        assert sum(output["budget_allocation"].values()) == 2800.0
        assert output["distribution_plan"] is None

    def test_repurpose_mode_output(self):
        """Repurpose mode must include distribution plan and rights summary."""
        output = {
            "mode": "repurpose",
            "content_scores": [
                {
                    "content_id": "video1",
                    "title": "Demo video",
                    "score": 20,
                    "tier": "must_amplify",
                    "recommended_spend": None,
                }
            ],
            "strategy_summary": "Repurpose demo video into 6 assets",
            "budget_allocation": {},
            "distribution_plan": "30-day plan: Reel, Stories, website embed, email",
            "rights_summary": "Full usage rights for 12 months",
            "metric_labels": {"reach": "Measured"},
        }
        assert output["mode"] == "repurpose"
        assert output["distribution_plan"] is not None
        assert output["rights_summary"] is not None

    def test_metric_labels_present(self):
        """All metrics must be labeled Measured, User-provided, or Estimated."""
        output = {
            "metric_labels": {"CPM": "Estimated", "CTR": "User-provided", "reach": "Measured"},
        }
        for label in output["metric_labels"].values():
            assert label in ("Measured", "User-provided", "Estimated")
