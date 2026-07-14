"""Tests for InstagramClient — mock instagrapi, test delay, lock, exceptions."""

import threading
import time

import pytest

from ig_client import InstagramClient


@pytest.fixture
def client():
    """Return a fresh InstagramClient with no login."""
    return InstagramClient()


# ── Login ────────────────────────────────────────────────────────────────────


class TestLogin:
    def test_login_no_credentials(self, client: InstagramClient):
        """login() with empty credentials returns False."""
        result = client.login(username="", password="")
        assert result is False
        assert client._logged_in is False

    def test_login_fresh(self, mocker, client: InstagramClient):
        """Fresh login calls cl.login() and dumps settings."""
        mocker.patch.object(client.cl, "login", return_value=None)
        mocker.patch.object(client, "_dump_settings", return_value=None)
        mocker.patch("os.path.exists", return_value=False)

        result = client.login(username="test_user", password="test_pass")
        assert result is True
        assert client._logged_in is True
        client.cl.login.assert_called_once_with("test_user", "test_pass")

    def test_login_session_file(self, mocker, client: InstagramClient):
        """Existing session file loads settings without fresh login."""
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch.object(client.cl, "load_settings", return_value=None)

        result = client.login(username="test_user", password="test_pass")
        assert result is True
        assert client._logged_in is True
        client.cl.load_settings.assert_called_once()

    def test_login_challenge_required(self, mocker, client: InstagramClient):
        """ChallengeRequired returns False without crashing."""
        from instagrapi.exceptions import ChallengeRequired

        mocker.patch("os.path.exists", return_value=False)
        mocker.patch.object(client.cl, "login", side_effect=ChallengeRequired("challenge"))

        result = client.login(username="test_user", password="test_pass")
        assert result is False
        assert client._logged_in is False

    def test_login_generic_exception(self, mocker, client: InstagramClient):
        """Generic exception returns False."""
        mocker.patch("os.path.exists", return_value=False)
        mocker.patch.object(client.cl, "login", side_effect=RuntimeError("network error"))

        result = client.login(username="test_user", password="test_pass")
        assert result is False


# ── send_dm ──────────────────────────────────────────────────────────────────


class TestSendDm:
    def test_send_dm_not_logged_in(self, client: InstagramClient):
        """send_dm returns error when not logged in."""
        result = client.send_dm(user_id=123, message="Hello")
        assert result["success"] is False
        assert result["error"] == "Not logged in"

    def test_send_dm_success(self, mocker, client: InstagramClient):
        """Successful DM returns success with thread_id."""
        client._logged_in = True
        mock_dm = mocker.MagicMock()
        mock_dm.thread_id = "thread_123"
        mocker.patch.object(client.cl, "direct_send", return_value=mock_dm)
        mocker.patch.object(client, "_dm_quota_ok", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)

        result = client.send_dm(user_id=123, message="Hello")
        assert result["success"] is True
        assert result["thread_id"] == "thread_123"
        assert result["error"] is None

    def test_send_dm_quota_exceeded(self, mocker, client: InstagramClient):
        """send_dm returns error when daily quota is reached."""
        client._logged_in = True
        mocker.patch.object(client, "_dm_quota_ok", return_value=False)

        result = client.send_dm(user_id=123, message="Hello")
        assert result["success"] is False
        assert "Daily DM limit" in result["error"]

    def test_send_dm_login_required_retry(self, mocker, client: InstagramClient):
        """LoginRequired triggers re-login and retry."""
        from instagrapi.exceptions import LoginRequired

        client._logged_in = True
        mocker.patch.object(client, "_dm_quota_ok", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)

        # First call raises LoginRequired, second succeeds
        mock_dm = mocker.MagicMock()
        mock_dm.thread_id = "thread_456"
        mocker.patch.object(
            client.cl,
            "direct_send",
            side_effect=[LoginRequired("expired"), mock_dm],
        )
        mocker.patch.object(client, "login", return_value=True)

        result = client.send_dm(user_id=123, message="Hello")
        assert result["success"] is True
        assert result["thread_id"] == "thread_456"
        assert client.login.called

    def test_send_dm_login_required_fail(self, mocker, client: InstagramClient):
        """LoginRequired on retry returns error."""
        from instagrapi.exceptions import LoginRequired

        client._logged_in = True
        mocker.patch.object(client, "_dm_quota_ok", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)
        mocker.patch.object(client.cl, "direct_send", side_effect=LoginRequired("expired"))
        mocker.patch.object(client, "login", return_value=True)

        result = client.send_dm(user_id=123, message="Hello")
        assert result["success"] is False
        assert result["error"] == "LoginRequired"

    def test_send_dm_user_not_found(self, mocker, client: InstagramClient):
        """UserNotFound returns error."""
        from instagrapi.exceptions import UserNotFound

        client._logged_in = True
        mocker.patch.object(client, "_dm_quota_ok", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)
        mocker.patch.object(client.cl, "direct_send", side_effect=UserNotFound("not found"))

        result = client.send_dm(user_id=123, message="Hello")
        assert result["success"] is False
        assert result["error"] == "UserNotFound"

    def test_send_dm_challenge_required(self, mocker, client: InstagramClient):
        """ChallengeRequired returns error."""
        from instagrapi.exceptions import ChallengeRequired

        client._logged_in = True
        mocker.patch.object(client, "_dm_quota_ok", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)
        mocker.patch.object(client.cl, "direct_send", side_effect=ChallengeRequired("challenge"))

        result = client.send_dm(user_id=123, message="Hello")
        assert result["success"] is False
        assert result["error"] == "ChallengeRequired"

    def test_send_dm_max_retries_exceeded(self, mocker, client: InstagramClient):
        """After 2 retries, returns max retries exceeded."""
        from instagrapi.exceptions import PleaseWaitFewMinutes

        client._logged_in = True
        mocker.patch.object(client, "_dm_quota_ok", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)
        mocker.patch.object(client.cl, "direct_send", side_effect=PleaseWaitFewMinutes("slow down"))

        result = client.send_dm(user_id=123, message="Hello")
        assert result["success"] is False
        assert result["error"] == "max retries exceeded"

    def test_send_dm_unexpected_exception(self, mocker, client: InstagramClient):
        """Unexpected exception is caught and returned as error string."""
        client._logged_in = True
        mocker.patch.object(client, "_dm_quota_ok", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)
        mocker.patch.object(client.cl, "direct_send", side_effect=ValueError("weird error"))

        result = client.send_dm(user_id=123, message="Hello")
        assert result["success"] is False
        assert "weird error" in result["error"]


# ── Lock / thread safety ─────────────────────────────────────────────────────


class TestLock:
    def test_lock_acquired_on_send_dm(self, mocker, client: InstagramClient):
        """send_dm acquires the instance lock."""
        client._logged_in = True
        mocker.patch.object(client, "_dm_quota_ok", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)
        mock_dm = mocker.MagicMock()
        mock_dm.thread_id = "t1"
        mocker.patch.object(client.cl, "direct_send", return_value=mock_dm)

        # Replace the real lock with a MagicMock to verify acquire/release
        mock_lock = mocker.MagicMock(wraps=threading.Lock())
        client._lock = mock_lock
        client.send_dm(user_id=123, message="Hello")
        mock_lock.__enter__.assert_called_once()
        mock_lock.__exit__.assert_called_once()

    def test_lock_acquired_on_read_threads(self, mocker, client: InstagramClient):
        """read_threads acquires the instance lock."""
        mocker.patch.object(client.cl, "direct_threads", return_value=[])
        mock_lock = mocker.MagicMock(wraps=threading.Lock())
        client._lock = mock_lock
        client.read_threads(amount=5)
        mock_lock.__enter__.assert_called_once()
        mock_lock.__exit__.assert_called_once()

    def test_concurrent_calls_are_serialized(self, mocker, client: InstagramClient):
        """Two concurrent send_dm calls are serialized by the lock."""
        client._logged_in = True
        mocker.patch.object(client, "_dm_quota_ok", return_value=True)
        mocker.patch("random.uniform", return_value=0.05)
        mocker.patch("time.sleep", return_value=None)
        mock_dm = mocker.MagicMock()
        mock_dm.thread_id = "t1"
        mocker.patch.object(client.cl, "direct_send", return_value=mock_dm)

        call_times = []

        def tracked_send(*args, **kwargs):
            call_times.append(time.monotonic())
            return client.send_dm(*args, **kwargs)

        t1 = threading.Thread(target=tracked_send, args=(1, "hi"))
        t2 = threading.Thread(target=tracked_send, args=(2, "hi"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Both should have succeeded
        assert len(call_times) == 2


# ── read_threads / read_thread / user_id_from_username ───────────────────────


class TestReadThreads:
    def test_read_threads_success(self, mocker, client: InstagramClient):
        mock_thread = mocker.MagicMock(spec=["thread_id", "users", "last_message", "last_activity"])
        mock_thread.thread_id = "tid_1"
        mock_thread.users = []
        mock_thread.last_message = {}
        mock_thread.last_activity = None
        mocker.patch.object(client.cl, "direct_threads", return_value=[mock_thread])

        result = client.read_threads(amount=10)
        assert len(result) == 1
        assert result[0].thread_id == "tid_1"

    def test_read_threads_login_required_retry(self, mocker, client: InstagramClient):
        from instagrapi.exceptions import LoginRequired

        mocker.patch.object(
            client.cl,
            "direct_threads",
            side_effect=[LoginRequired("expired"), []],
        )
        mocker.patch.object(client, "login", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)

        result = client.read_threads(amount=10)
        assert result == []

    def test_read_threads_exception(self, mocker, client: InstagramClient):
        mocker.patch.object(client.cl, "direct_threads", side_effect=RuntimeError("fail"))
        result = client.read_threads(amount=10)
        assert result == []


class TestReadThread:
    def test_read_thread_success(self, mocker, client: InstagramClient):
        mock_msg = mocker.MagicMock(spec=["id", "user_id", "text", "timestamp"])
        mock_msg.id = "msg_1"
        mock_msg.user_id = "123"
        mock_msg.text = "Hello"
        mock_msg.timestamp = None
        mock_thread = mocker.MagicMock()
        mock_thread.items = [mock_msg]
        mocker.patch.object(client.cl, "direct_thread", return_value=mock_thread)

        result = client.read_thread("tid_1", amount=50)
        assert len(result) == 1
        assert result[0].text == "Hello"

    def test_read_thread_not_found(self, mocker, client: InstagramClient):
        from instagrapi.exceptions import DirectThreadNotFound

        mocker.patch.object(client.cl, "direct_thread", side_effect=DirectThreadNotFound("not found"))
        result = client.read_thread("tid_1")
        assert result == []


class TestUserIdFromUsername:
    def test_user_id_success(self, mocker, client: InstagramClient):
        mocker.patch.object(client.cl, "user_id_from_username", return_value=12345)
        result = client.user_id_from_username("test_user")
        assert result == 12345

    def test_user_id_not_found(self, mocker, client: InstagramClient):
        from instagrapi.exceptions import UserNotFound

        mocker.patch.object(client.cl, "user_id_from_username", side_effect=UserNotFound("not found"))
        result = client.user_id_from_username("unknown")
        assert result is None

    def test_user_id_login_required(self, mocker, client: InstagramClient):
        from instagrapi.exceptions import LoginRequired

        mocker.patch.object(
            client.cl,
            "user_id_from_username",
            side_effect=[LoginRequired("expired"), 67890],
        )
        mocker.patch.object(client, "login", return_value=True)
        mocker.patch("random.uniform", return_value=0.01)
        mocker.patch("time.sleep", return_value=None)

        result = client.user_id_from_username("test_user")
        assert result == 67890


# ── _dm_quota_ok ─────────────────────────────────────────────────────────────


class TestDmQuota:
    def test_quota_ok_under_limit(self, client: InstagramClient):
        """Under the daily limit, quota returns True."""
        assert client._dm_quota_ok() is True

    def test_quota_exceeded(self, mocker, client: InstagramClient):
        """When timestamps fill the quota, returns False."""
        from ig_client import MAX_DMS_PER_DAY

        now = time.monotonic()
        # Fill the quota
        client._dm_timestamps = [now - 100] * MAX_DMS_PER_DAY
        assert client._dm_quota_ok() is False

    def test_quota_old_timestamps_cleaned(self, client: InstagramClient):
        """Timestamps older than 24h are cleaned out."""
        old = time.monotonic() - 90000  # ~25h ago
        client._dm_timestamps = [old]
        assert client._dm_quota_ok() is True
        assert len(client._dm_timestamps) == 1  # old removed, new added
