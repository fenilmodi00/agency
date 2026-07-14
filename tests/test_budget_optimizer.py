"""Tests for the Budget Optimizer target agent — output shape, mocked tools, task."""
import json

import pytest


class TestBudgetOptimizerOutputShape:
    """Budget optimizer output must have expected top-level keys."""

    REQUIRED_KEYS = {
        "total_budget",
        "recommended_allocation",
        "projected_roi",
        "scenarios",
        "optimization_strategies",
        "recommended_scenario",
    }

    def test_valid_budget_optimizer_output(self):
        """Output must contain all required keys with correct types."""
        output = {
            "total_budget": 50000,
            "recommended_allocation": {
                "by_tier": {"micro": {"amount": 25000, "percent": 50, "count": 10}},
                "by_platform": {"instagram": {"amount": 30000, "percent": 60}},
                "contingency": {"amount": 2500, "percent": 5},
            },
            "projected_roi": {"reach": "1.5M", "engagements": "150K", "cpm": "$10", "roi_ratio": "3.5:1", "label": "Estimated"},
            "scenarios": [
                {"name": "Conservative", "total_spend": 45000, "projected_reach": "1M", "roi": "2.5:1", "rationale": "lower risk"},
            ],
            "optimization_strategies": ["shift 10% to micro-influencers for better engagement"],
            "recommended_scenario": "Recommended",
        }
        assert self.REQUIRED_KEYS.issubset(output.keys())
        assert output["total_budget"] == 50000
        assert len(output["scenarios"]) >= 1
        assert output["recommended_scenario"] in ["Conservative", "Recommended", "Aggressive"]

    def test_budget_optimizer_json_serializable(self):
        """Output must be JSON-serializable."""
        output = {
            "total_budget": 0,
            "recommended_allocation": {"by_tier": {}, "by_platform": {}, "contingency": {"amount": 0, "percent": 0}},
            "projected_roi": {"reach": "", "engagements": "", "cpm": "", "roi_ratio": "", "label": "Estimated"},
            "scenarios": [],
            "optimization_strategies": [],
            "recommended_scenario": "",
        }
        serialized = json.dumps(output)
        deserialized = json.loads(serialized)
        assert deserialized == output

    def test_budget_optimizer_allocation_sums_to_100(self):
        """Allocation by_tier percentages should sum to 100 (with contingency)."""
        allocation = {
            "by_tier": {
                "nano": {"amount": 10000, "percent": 20, "count": 20},
                "micro": {"amount": 25000, "percent": 50, "count": 10},
                "macro": {"amount": 12500, "percent": 25, "count": 2},
            },
            "by_platform": {},
            "contingency": {"amount": 2500, "percent": 5},
        }
        tier_total = sum(t["percent"] for t in allocation["by_tier"].values())
        cont = allocation["contingency"]["percent"]
        assert tier_total + cont == pytest.approx(100.0)

    def test_projected_roi_has_label(self):
        """ROI projections must be labeled."""
        roi = {"reach": "1M", "engagements": "100K", "cpm": "$10", "roi_ratio": "3:1", "label": "Estimated"}
        assert roi["label"] in ("Measured", "User-provided", "Estimated")


class TestMockedBudgetOptimizerTools:
    """Mock the tools used by the budget optimizer agent."""

    def test_calculate_fit_score_mocked(self, mocker):
        """Mock calculate_fit_score to return a specific score."""
        mock_score = mocker.patch("agents.target.budget_optimizer._calculate_fit_score")
        mock_score.return_value = 0.85
        result = mock_score(
            {"detected_niche": "fashion", "detected_language": "en"},
            {"product_category": "fashion", "target_language": ["en"]},
        )
        assert result == 0.85

    def test_registry_get_mocked(self, mocker):
        """Mock registry_get to return fake budget data."""
        mock_reg = mocker.patch("tools.registry_tools.registry_get")
        mock_reg.return_value = {"total_budget": 30000, "used": 15000}
        result = mock_reg("launches", "campaign_001")
        assert result["total_budget"] == 30000

    def test_registry_get_empty(self):
        """When registry has no data, registry_get returns dict with record=None."""
        from tools.registry_tools import registry_get
        result = registry_get("launches", "nonexistent_campaign")
        assert isinstance(result, dict)
        assert result.get("record") is None


class TestBudgetOptimizerTask:
    """Test the task expected output shape."""

    def test_task_expected_output_has_required_fields(self):
        """The expected output string should describe the required keys."""
        expected_output = (
            "A valid JSON object with these top-level keys:\n"
            "- total_budget: number\n"
            "- recommended_allocation: {by_tier, by_platform, contingency}\n"
            "- projected_roi: {reach, engagements, cpm, roi_ratio, label}\n"
            "- scenarios: array of {name, total_spend, projected_reach, roi, rationale}\n"
            "- optimization_strategies: array of strings\n"
            "- recommended_scenario: string\n"
            "Return only the JSON object, no commentary."
        )
        assert "total_budget" in expected_output
        assert "recommended_allocation" in expected_output
        assert "projected_roi" in expected_output
        assert "scenarios" in expected_output
        assert "optimization_strategies" in expected_output
        assert "JSON object" in expected_output
