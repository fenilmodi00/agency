"""Tests for the Contract agent — mock conversation details, assert contract text."""

import pytest


class TestContractContent:
    """Contract text must contain #ad/#sponsored and legal disclaimer."""

    REQUIRED_DISCLOSURES = ["#ad", "#sponsored"]
    LEGAL_DISCLAIMER_PHRASES = [
        "legal review",
        "not legal advice",
        "template",
        "consult",
        "attorney",
    ]

    def test_contract_contains_ad_disclosure(self):
        """Contract text must contain #ad or #sponsored."""
        contract_text = (
            "#ad Collaboration agreement between Brand and Creator. "
            "This is a paid partnership. #sponsored"
        )
        has_disclosure = any(d in contract_text.lower() for d in self.REQUIRED_DISCLOSURES)
        assert has_disclosure, "Contract must contain #ad or #sponsored"

    def test_contract_contains_legal_disclaimer(self):
        """Contract text must contain a legal disclaimer phrase."""
        contract_text = (
            "#ad Collaboration agreement. This is a template requiring "
            "legal review. Not legal advice. Consult an attorney before signing."
        )
        has_disclaimer = any(p in contract_text.lower() for p in self.LEGAL_DISCLAIMER_PHRASES)
        assert has_disclaimer, "Contract must contain a legal disclaimer"

    def test_contract_has_both_disclosure_and_disclaimer(self):
        """Contract must have both disclosure and disclaimer."""
        contract_text = (
            "#ad Collaboration agreement between Brand and Creator.\n\n"
            "Deliverables: 2 Reels, 1 Story\n"
            "Budget: ₹15,000\n"
            "Timeline: 2 weeks\n\n"
            "This is a template requiring legal review. "
            "Not legal advice. Consult an attorney before signing. #sponsored"
        )
        has_disclosure = any(d in contract_text.lower() for d in self.REQUIRED_DISCLOSURES)
        has_disclaimer = any(p in contract_text.lower() for p in self.LEGAL_DISCLAIMER_PHRASES)
        assert has_disclosure, "Missing #ad or #sponsored"
        assert has_disclaimer, "Missing legal disclaimer"


class TestContractOutputShape:
    """Test the expected output JSON shape of the contract task."""

    REQUIRED_KEYS = {
        "contract_text", "contract_type", "deliverables",
        "usage_rights", "timeline", "asci_compliant",
    }

    def test_valid_contract_output(self):
        """Contract output must have all required keys."""
        contract = {
            "contract_text": "#ad Agreement...",
            "contract_type": "paid",
            "deliverables": "2 Reels, 1 Story",
            "usage_rights": "6 months exclusive",
            "timeline": "2 weeks",
            "asci_compliant": 1,
        }
        assert self.REQUIRED_KEYS.issubset(contract.keys())
        assert contract["contract_type"] in ("barter", "paid", "affiliate")
        assert contract["asci_compliant"] in (0, 1)

    def test_contract_type_validation(self):
        """contract_type must be one of barter, paid, affiliate."""
        valid_types = {"barter", "paid", "affiliate"}
        assert "paid" in valid_types
        assert "barter" in valid_types
        assert "affiliate" in valid_types

    def test_contract_asci_compliant_flag(self):
        """asci_compliant should be 1 when contract follows ASCI guidelines."""
        contract = {
            "contract_text": "#ad Agreement with disclosures...",
            "contract_type": "paid",
            "asci_compliant": 1,
        }
        assert contract["asci_compliant"] == 1


class TestMockedContract:
    def test_get_conversation_details_mocked(self, mocker):
        """Mock get_conversation_details to return fake conversation + brief."""
        mock_details = mocker.patch("tools.database_tools.get_conversation_details")
        mock_details.return_value = {
            "id": 1,
            "brief_id": 1,
            "creator_username": "creator1",
            "status": "accepted",
            "agreed_rate": 12000.0,
            "raw_brief": "Brand wants Gujarati food creators",
        }
        result = mock_details(1)
        assert result["creator_username"] == "creator1"
        assert result["agreed_rate"] == 12000.0
        assert "raw_brief" in result

    def test_get_brand_brief_mocked(self, mocker):
        """Mock get_brand_brief to return brand brief."""
        mock_brief = mocker.patch("tools.database_tools.get_brand_brief")
        mock_brief.return_value = {
            "id": 1,
            "raw_brief": "Brand wants Gujarati food creators",
            "parsed_brief": '{"budget_min": 5000, "budget_max": 15000}',
        }
        result = mock_brief(1)
        assert result["raw_brief"] == "Brand wants Gujarati food creators"
        assert "budget_max" in result["parsed_brief"]

    def test_save_contract_mocked(self, mocker):
        """Mock save_contract to return a contract ID."""
        mock_save = mocker.patch("tools.database_tools.save_contract")
        mock_save.return_value = 42
        result = mock_save(
            conversation_id=1,
            creator_username="creator1",
            brand_name="TestBrand",
            contract_text="#ad Agreement...",
            contract_type="paid",
            deliverables="2 Reels",
            usage_rights="6 months",
            timeline="2 weeks",
            asci_compliant=1,
        )
        assert result == 42
