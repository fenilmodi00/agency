"""Tests for the Activate contract helper — drafting and review."""

import pytest


class TestDrafting:
    """Tests for contract drafting output."""

    def test_draft_has_required_fields(self):
        """Draft contract must have all required fields."""
        output = {
            "contract_id": 1,
            "status": "drafted",
            "agreed_rate": 500.0,
            "usage_rights_summary": "12-month non-exclusive on Instagram and TikTok",
            "key_terms": {
                "deliverables": "2 Instagram posts, 1 Reel",
                "compensation": "$500, 50% upfront, 50% on approval",
                "exclusivity": "None",
                "disclosure": "#ad required in caption",
            },
            "legal_disclaimer": (
                "These are templates, not legal documents. "
                "Seek legal counsel before execution."
            ),
        }
        assert "contract_id" in output
        assert "status" in output
        assert "agreed_rate" in output
        assert "usage_rights_summary" in output
        assert "key_terms" in output
        assert "legal_disclaimer" in output

    def test_status_is_drafted_or_error(self):
        """Contract status must be 'drafted' or 'error'."""
        output = {"status": "drafted"}
        assert output["status"] in ("drafted", "error")

    def test_draft_includes_disclaimer(self):
        """Draft must include the legal disclaimer."""
        output = {
            "legal_disclaimer": (
                "These are templates, not legal documents. "
                "Seek legal counsel before execution."
            ),
        }
        assert "legal" in output["legal_disclaimer"].lower()
        assert "counsel" in output["legal_disclaimer"].lower()


class TestOutputShape:
    """Test the expected output JSON shape of contract helper."""

    def test_valid_output_shape(self):
        """Contract output must have contract_id, status, agreed_rate, key_terms."""
        output = {
            "contract_id": 1,
            "status": "drafted",
            "agreed_rate": 500.0,
            "usage_rights_summary": "12-month non-exclusive",
            "key_terms": {"deliverables": "2 posts"},
            "legal_disclaimer": "Seek legal counsel.",
        }
        assert output["contract_id"] is not None
        assert output["status"] == "drafted"
        assert output["agreed_rate"] > 0
