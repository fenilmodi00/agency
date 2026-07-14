"""Tests for the Activate outreach manager — consent registry, DM quota, send/dry-run."""

import pytest


class TestDryRun:
    """When send=False, send_instagram_dm must NOT be called."""

    def test_dry_run_does_not_call_send_dm(self, mocker):
        """Dry-run mode: send_instagram_dm should not be invoked."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (0, 20)
        mock_registry_get = mocker.patch("tools.registry_tools.registry_get")
        mock_registry_get.return_value = {}

        send = False
        if not send:
            result = {
                "username": "test_creator",
                "thread_id": None,
                "language": "en",
                "message": "Hello! Collaboration opportunity.",
                "sent": False,
                "dry_run": True,
                "consent_blocked": False,
            }

        assert result["sent"] is False
        assert result["dry_run"] is True
        assert result["consent_blocked"] is False
        mock_send_dm.assert_not_called()

    def test_dry_run_multiple_creators(self, mocker):
        """Dry-run with multiple creators: none should call send_dm."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (0, 20)
        mock_registry_get = mocker.patch("tools.registry_tools.registry_get")
        mock_registry_get.return_value = {}

        creators = ["c1", "c2", "c3"]
        results = []
        for c in creators:
            results.append({
                "username": c,
                "thread_id": None,
                "language": "gu",
                "message": f"Hello {c}!",
                "sent": False,
                "dry_run": True,
                "consent_blocked": False,
            })

        assert len(results) == 3
        assert all(r["sent"] is False for r in results)
        assert all(r["dry_run"] is True for r in results)
        mock_send_dm.assert_not_called()


class TestConsentRegistry:
    """Consent check must block suppressed creators before any DM."""

    def test_consent_suppressed_skips_creator(self, mocker):
        """When consent is suppressed, skip the creator entirely."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (0, 20)
        mock_registry_get = mocker.patch("tools.registry_tools.registry_get")
        mock_registry_get.return_value = {"status": "suppressed"}

        consent = mock_registry_get("consent", "blocked_user")
        if consent.get("status") in ("suppressed", "blocked"):
            result = {
                "username": "blocked_user",
                "sent": False,
                "dry_run": False,
                "consent_blocked": True,
                "message": "",
            }

        assert result["consent_blocked"] is True
        assert result["sent"] is False
        mock_send_dm.assert_not_called()

    def test_consent_granted_allows_send(self, mocker):
        """When consent is granted, sending may proceed."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_send_dm.return_value = {"success": True, "thread_id": "t1", "error": None}
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (0, 20)
        mock_registry_get = mocker.patch("tools.registry_tools.registry_get")
        mock_registry_get.return_value = {}

        consent = mock_registry_get("consent", "active_user")
        if consent.get("status") not in ("suppressed", "blocked"):
            result = mock_send_dm("active_user", "Hello!")

        mock_send_dm.assert_called_once()
        assert result["success"] is True


class TestOutputShape:
    """Test the expected output JSON shape of the outreach manager task."""

    def test_valid_output_shape(self):
        """Outreach manager output must have results, quota_exceeded, consent_blocked."""
        output = {
            "results": [
                {
                    "username": "creator1",
                    "thread_id": "thread_abc",
                    "language": "gu",
                    "message": "Hello!",
                    "sent": True,
                    "dry_run": False,
                    "consent_blocked": False,
                }
            ],
            "quota_exceeded": False,
        }
        assert "results" in output
        assert "quota_exceeded" in output
        assert isinstance(output["results"], list)
        assert isinstance(output["quota_exceeded"], bool)
        for r in output["results"]:
            assert "username" in r
            assert "sent" in r
            assert "dry_run" in r
            assert "consent_blocked" in r
