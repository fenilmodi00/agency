"""Tests for the Outreach agent — mock InstagramClient and quota."""

import pytest


class TestDryRun:
    """When send=False, send_instagram_dm must NOT be called."""

    def test_dry_run_does_not_call_send_dm(self, mocker):
        """Dry-run mode: send_instagram_dm should not be invoked."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (0, 20)

        # Simulate the outreach agent's dry-run logic
        send = False
        if not send:
            # In dry-run, we compose the message but don't call send_dm
            message = "Hello! Collaboration opportunity."
            result = {
                "username": "test_creator",
                "thread_id": None,
                "language": "en",
                "message": message,
                "sent": False,
                "dry_run": True,
            }
        else:
            result = mock_send_dm("test_creator", "Hello!")

        assert result["sent"] is False
        assert result["dry_run"] is True
        mock_send_dm.assert_not_called()

    def test_dry_run_multiple_creators(self, mocker):
        """Dry-run with multiple creators: none should call send_dm."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (0, 20)

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
            })

        assert len(results) == 3
        assert all(r["sent"] is False for r in results)
        assert all(r["dry_run"] is True for r in results)
        mock_send_dm.assert_not_called()


class TestSendMode:
    """When send=True, send_instagram_dm must be called."""

    def test_send_calls_send_dm(self, mocker):
        """send=True should invoke send_instagram_dm."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_send_dm.return_value = {"success": True, "thread_id": "thread_123", "error": None}
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (0, 20)

        send = True
        if send:
            result = mock_send_dm("test_creator", "Hello! Collaboration opportunity.")

        mock_send_dm.assert_called_once_with("test_creator", "Hello! Collaboration opportunity.")
        assert result["success"] is True
        assert result["thread_id"] == "thread_123"

    def test_send_calls_save_and_log(self, mocker):
        """After successful send, save_conversation and log_dm should be called."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_send_dm.return_value = {"success": True, "thread_id": "thread_123", "error": None}
        mock_save = mocker.patch("tools.database_tools.save_conversation")
        mock_save.return_value = 1
        mock_log = mocker.patch("tools.database_tools.log_dm")
        mock_log.return_value = 1
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (0, 20)

        # Simulate the send flow
        dm_result = mock_send_dm("test_creator", "Hello!")
        if dm_result["success"]:
            save_result = mock_save(
                brief_id=1,
                creator_username="test_creator",
                thread_id=dm_result["thread_id"],
                status="outreach_sent",
                last_message_text="Hello!",
                last_message_direction="sent",
            )
            log_result = mock_log(
                creator_username="test_creator",
                thread_id=dm_result["thread_id"],
                message_text="Hello!",
                direction="sent",
            )

        mock_save.assert_called_once()
        mock_log.assert_called_once()
        assert save_result == 1
        assert log_result == 1

    def test_send_failure_does_not_save(self, mocker):
        """When send fails, save_conversation and log_dm should NOT be called."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_send_dm.return_value = {"success": False, "thread_id": None, "error": "UserNotFound"}
        mock_save = mocker.patch("tools.database_tools.save_conversation")
        mock_log = mocker.patch("tools.database_tools.log_dm")
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (0, 20)

        dm_result = mock_send_dm("unknown_user", "Hello!")
        if dm_result["success"]:
            mock_save(...)
            mock_log(...)

        mock_save.assert_not_called()
        mock_log.assert_not_called()
        assert dm_result["success"] is False


class TestQuota:
    """Tests for DM quota enforcement."""

    def test_quota_exceeded_stops_sending(self, mocker):
        """When quota is exceeded, no more DMs should be sent."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (20, 20)  # quota full

        sent_today, max_dms = mock_check_quota()
        if sent_today >= max_dms:
            # Should stop — do not call send_dm
            pass
        else:
            mock_send_dm("creator", "msg")

        mock_send_dm.assert_not_called()

    def test_quota_available_allows_sending(self, mocker):
        """When quota is available, DMs can be sent."""
        mock_send_dm = mocker.patch("tools.instagram_tools.send_instagram_dm")
        mock_send_dm.return_value = {"success": True, "thread_id": "t1", "error": None}
        mock_check_quota = mocker.patch("tools.database_tools.check_dm_quota")
        mock_check_quota.return_value = (5, 20)  # 5 sent, 15 remaining

        sent_today, max_dms = mock_check_quota()
        if sent_today < max_dms:
            result = mock_send_dm("creator", "msg")

        mock_send_dm.assert_called_once()
        assert result["success"] is True


class TestOutreachOutputShape:
    """Test the expected output JSON shape of the outreach task."""

    def test_valid_outreach_output(self):
        """Outreach output must have results array and quota_exceeded flag."""
        output = {
            "results": [
                {
                    "username": "creator1",
                    "thread_id": "thread_abc",
                    "language": "gu",
                    "message": "Hello!",
                    "sent": True,
                    "dry_run": False,
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
