"""Tests for registry tools — wraps registry-events.py via subprocess."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.registry_tools import registry_get, registry_propose, registry_verify


class TestRegistryGet:
    def test_returns_dict_on_success(self):
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"aggregate_id": "creator-abc", "handle": "@test", "rate": 5000})
        mock_result.returncode = 0
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_get("creators", "creator-abc")
        assert isinstance(result, dict)
        assert result["aggregate_id"] == "creator-abc"

    def test_returns_empty_dict_on_failure(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 1
        mock_result.stderr = "not found"
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_get("creators", "nonexistent")
        assert result == {}

    def test_returns_empty_dict_on_timeout(self):
        import subprocess
        with patch("tools.registry_tools.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="python", timeout=30)):
            result = registry_get("creators", "any")
        assert result == {}


class TestRegistryPropose:
    def test_returns_dict_with_event_id_on_success(self):
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"event_id": "evt-001", "offset": 1, "status": "proposed"})
        mock_result.returncode = 0
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_propose(
                registry="creators",
                aggregate_id="creator-new",
                payload={"handle": "@newcreator", "niche": "food"},
                source="influencer-discovery",
                actor_id="scout-agent",
            )
        assert result["event_id"] == "evt-001"
        assert result["status"] == "proposed"

    def test_returns_error_dict_on_failure(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 1
        mock_result.stderr = "invalid payload"
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_propose("creators", "x", {}, "test", "test")
        assert "error" in result


class TestRegistryVerify:
    def test_returns_dict_on_success(self):
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"verified": True, "offsets": 5})
        mock_result.returncode = 0
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_verify("creators")
        assert result["verified"] is True


class TestRegistryValidation:
    def test_invalid_registry_raises(self):
        with pytest.raises(ValueError):
            registry_get("invalid_registry", "x")

    def test_invalid_registry_propose_raises(self):
        with pytest.raises(ValueError):
            registry_propose("bad", "x", {}, "test", "test")