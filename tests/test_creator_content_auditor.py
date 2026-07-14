"""Tests for the Activate creator content auditor — STAR gate with SHIP/FIX/BLOCK."""

import pytest


class TestVerdicts:
    """Tests for the three STAR gate verdicts."""

    def test_ship_verdict(self):
        """SHIP: No vetoes, clean submission."""
        output = {
            "verdict": "SHIP",
            "sqs": 84,
            "vetoes": [],
            "revision_notes": "",
            "score_breakdown": {
                "suitability": 85,
                "trust": 82,
                "appeal": 80,
                "return": 90,
            },
        }
        assert output["verdict"] == "SHIP"
        assert output["sqs"] > 0
        assert len(output["vetoes"]) == 0

    def test_fix_verdict(self):
        """FIX: Revisions required, vetoes present but fixable."""
        output = {
            "verdict": "FIX",
            "sqs": 59,
            "vetoes": ["STAR-T1"],
            "revision_notes": "Add #ad disclosure to the caption.",
            "score_breakdown": {
                "suitability": 85,
                "trust": 40,
                "appeal": 80,
                "return": 70,
            },
        }
        assert output["verdict"] == "FIX"
        assert "STAR-T1" in output["vetoes"]
        assert output["revision_notes"] != ""

    def test_block_verdict(self):
        """BLOCK: Unfixable veto triggered, sqs is null."""
        output = {
            "verdict": "BLOCK",
            "sqs": None,
            "vetoes": ["STAR-T1", "STAR-T2"],
            "revision_notes": "Missing disclosure and false claim.",
            "score_breakdown": {
                "suitability": 85,
                "trust": 20,
                "appeal": 80,
                "return": 70,
            },
        }
        assert output["verdict"] == "BLOCK"
        assert output["sqs"] is None
        assert len(output["vetoes"]) > 0


class TestOutputShape:
    """Test the expected output JSON shape for auditor."""

    def test_valid_output_shape(self):
        """Auditor output must have verdict, sqs, vetoes, revision_notes, score_breakdown."""
        output = {
            "verdict": "SHIP",
            "sqs": 80,
            "vetoes": [],
            "revision_notes": "",
            "score_breakdown": {
                "suitability": 80,
                "trust": 80,
                "appeal": 80,
                "return": 80,
            },
        }
        assert "verdict" in output
        assert "sqs" in output
        assert "vetoes" in output
        assert "revision_notes" in output
        assert "score_breakdown" in output
        assert output["verdict"] in ("SHIP", "FIX", "BLOCK")
        assert isinstance(output["score_breakdown"], dict)
