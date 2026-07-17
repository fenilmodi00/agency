"""Tests for InstagramClient extended methods: fetch_profile, fetch_media, fetch_insights, logout, per-user session support.

All tests mock instagrapi.Client — no real network or Instagram API calls.
"""

import datetime
import os

import pytest

from ig_client import InstagramClient, get_ig_client


@pytest.fixture
def client(mocker):
    """Return a fresh InstagramClient with mocked instagrapi Client."""
    mocker.patch("ig_client.Client")
    return InstagramClient()


# ── fetch_profile ─────────────────────────────────────────────────────────────


class TestFetchProfile:
    def test_fetch_profile_happy(self, mocker, client: InstagramClient):
        """fetch_profile with username returns dict with correct keys from mock User."""
        mock_user = mocker.MagicMock()
        mock_user.pk = 123456
        mock_user.username = "test_user"
        mock_user.full_name = "Test User"
        mock_user.biography = "Bio text"
        mock_user.external_url = "https://example.com"
        mock_user.follower_count = 1000
        mock_user.following_count = 500
        mock_user.media_count = 42
        mock_user.is_private = False
        mock_user.is_verified = True
        mock_user.profile_pic_url = "https://pic.url/123.jpg"
        mock_user.is_business = True

        mocker.patch.object(client.cl, "user_info_from_username", return_value=mock_user)

        result = client.fetch_profile(username="test_user")

        assert result is not None
        assert result["pk"] == 123456
        assert result["username"] == "test_user"
        assert result["full_name"] == "Test User"
        assert result["biography"] == "Bio text"
        assert result["external_url"] == "https://example.com"
        assert result["follower_count"] == 1000
        assert result["following_count"] == 500
        assert result["media_count"] == 42
        assert result["is_private"] is False
        assert result["is_verified"] is True
        assert result["profile_pic_url"] == "https://pic.url/123.jpg"
        assert result["is_business"] is True

    def test_fetch_profile_user_not_found(self, mocker, client: InstagramClient):
        """fetch_profile returns None when UserNotFound is raised."""
        from instagrapi.exceptions import UserNotFound

        mocker.patch.object(
            client.cl, "user_info_from_username", side_effect=UserNotFound("not found")
        )

        result = client.fetch_profile(username="nonexistent")
        assert result is None

    def test_fetch_profile_re_login(self, mocker, client: InstagramClient):
        """fetch_profile triggers re-login on LoginRequired, then succeeds."""
        from instagrapi.exceptions import LoginRequired

        mock_user = mocker.MagicMock()
        mock_user.pk = 789
        mock_user.username = "retry_user"
        mock_user.full_name = "Retry User"
        mock_user.biography = ""
        mock_user.external_url = ""
        mock_user.follower_count = 0
        mock_user.following_count = 0
        mock_user.media_count = 0
        mock_user.is_private = True
        mock_user.is_verified = False
        mock_user.profile_pic_url = ""
        mock_user.is_business = False

        mocker.patch.object(
            client.cl,
            "user_info_from_username",
            side_effect=[LoginRequired("expired"), mock_user],
        )
        mocker.patch.object(client, "login", return_value=True)
        mocker.patch("time.sleep", return_value=None)

        result = client.fetch_profile(username="retry_user")

        assert result is not None
        assert result["pk"] == 789
        assert client.login.called

    def test_fetch_profile_own_when_username_none(self, mocker, client: InstagramClient):
        """fetch_profile with username=None fetches own profile via cl.user_info."""
        client.cl.user_id = "self_123"

        mock_user = mocker.MagicMock()
        mock_user.pk = 111
        mock_user.username = "me"
        mock_user.full_name = "Me Myself"
        mock_user.biography = "mine"
        mock_user.external_url = ""
        mock_user.follower_count = 200
        mock_user.following_count = 300
        mock_user.media_count = 5
        mock_user.is_private = False
        mock_user.is_verified = False
        mock_user.profile_pic_url = ""
        mock_user.is_business = False

        mocker.patch.object(client.cl, "user_info", return_value=mock_user)

        result = client.fetch_profile(username=None)

        assert result is not None
        assert result["pk"] == 111
        assert result["username"] == "me"
        client.cl.user_info.assert_called_once_with("self_123")


# ── fetch_media ────────────────────────────────────────────────────────────────


class TestFetchMedia:
    def test_fetch_media_happy(self, mocker, client: InstagramClient):
        """fetch_media returns list of dicts from mock Media objects."""
        client.cl.user_id = "12345"

        mock_media_1 = mocker.MagicMock()
        mock_media_1.pk = "media_pk_1"
        mock_media_1.caption_text = "Hello world"
        mock_media_1.media_type = 1
        mock_media_1.thumbnail_url = "https://thumb.url/1.jpg"
        mock_media_1.media_url = "https://media.url/1.jpg"
        mock_media_1.permalink = "https://instagram.com/p/abc123"
        mock_media_1.taken_at = datetime.datetime(2025, 1, 15, 12, 30, 0)
        mock_media_1.like_count = 100
        mock_media_1.comment_count = 10
        mock_media_1.view_count = 500
        mock_media_1.play_count = 50

        mock_media_2 = mocker.MagicMock()
        mock_media_2.pk = "media_pk_2"
        mock_media_2.caption_text = ""
        mock_media_2.media_type = 2
        mock_media_2.thumbnail_url = None
        mock_media_2.media_url = "https://media.url/2.mp4"
        mock_media_2.permalink = "https://instagram.com/p/def456"
        mock_media_2.taken_at = datetime.datetime(2025, 1, 16, 8, 0, 0)
        mock_media_2.like_count = 250
        mock_media_2.comment_count = 25
        mock_media_2.view_count = 1000
        mock_media_2.play_count = 200

        mocker.patch.object(
            client.cl, "user_medias", return_value=[mock_media_1, mock_media_2]
        )

        result = client.fetch_media(amount=25)

        assert isinstance(result, list)
        assert len(result) == 2

        assert result[0]["pk"] == "media_pk_1"
        assert result[0]["caption_text"] == "Hello world"
        assert result[0]["media_type"] == 1
        assert result[0]["thumbnail_url"] == "https://thumb.url/1.jpg"
        assert result[0]["media_url"] == "https://media.url/1.jpg"
        assert result[0]["permalink"] == "https://instagram.com/p/abc123"
        assert result[0]["taken_at"] == "2025-01-15T12:30:00"
        assert result[0]["like_count"] == 100
        assert result[0]["comment_count"] == 10
        assert result[0]["view_count"] == 500
        assert result[0]["play_count"] == 50

        assert result[1]["pk"] == "media_pk_2"
        assert result[1]["caption_text"] == ""
        assert result[1]["media_type"] == 2
        assert result[1]["taken_at"] == "2025-01-16T08:00:00"


# ── fetch_insights ─────────────────────────────────────────────────────────────


class TestFetchInsights:
    def test_fetch_insights_business(self, mocker, client: InstagramClient):
        """fetch_insights returns dict for business account."""
        mock_insights = {
            "followers_count": 5000,
            "followers_delta_from_last_week": 50,
            "accounts_reached": 15000,
            "total_interactions": 800,
        }
        mocker.patch.object(client.cl, "insights_account", return_value=mock_insights)

        result = client.fetch_insights()

        assert result == mock_insights
        assert result["followers_count"] == 5000
        assert result["accounts_reached"] == 15000

    def test_fetch_insights_non_business(self, mocker, client: InstagramClient):
        """fetch_insights returns error dict when UserError is raised (non-business account)."""
        from instagrapi.exceptions import UserError

        mocker.patch.object(
            client.cl, "insights_account", side_effect=UserError("not business")
        )

        result = client.fetch_insights()

        assert result is not None
        assert result["error"] == "Business account required for insights"


# ── logout ─────────────────────────────────────────────────────────────────────


class TestLogout:
    def test_logout(self, mocker, client: InstagramClient):
        """logout calls cl.logout(), sets _logged_in=False, deletes session file."""
        client._logged_in = True

        mocker.patch.object(client.cl, "logout", return_value=None)
        exists_mock = mocker.patch("os.path.exists", return_value=True)
        remove_mock = mocker.patch("os.remove", return_value=None)

        result = client.logout()

        assert result is True
        assert client._logged_in is False
        client.cl.logout.assert_called_once()
        exists_mock.assert_called_once()
        remove_mock.assert_called_once()

    def test_logout_no_session_file(self, mocker, client: InstagramClient):
        """logout still succeeds when session file doesn't exist."""
        client._logged_in = True

        mocker.patch.object(client.cl, "logout", return_value=None)
        mocker.patch("os.path.exists", return_value=False)
        remove_mock = mocker.patch("os.remove", return_value=None)

        result = client.logout()

        assert result is True
        assert client._logged_in is False
        remove_mock.assert_not_called()


# ── Per-user session support ───────────────────────────────────────────────────


class TestPerUserSession:
    def test_per_user_session(self):
        """InstagramClient accepts session_file_path and stores it."""
        path = "data/sessions/test_user.json"
        c = InstagramClient(session_file_path=path)
        assert c._session_file_path == path

    def test_singleton_unchanged(self):
        """get_ig_client() still returns singleton with _session_file_path is None."""
        c = get_ig_client()
        assert c._session_file_path is None

    def test_login_uses_session_file_path(self, mocker):
        """login() uses _session_file_path when set."""
        path = "data/sessions/custom.json"
        c = InstagramClient(session_file_path=path)

        mocker.patch("os.path.exists", return_value=False)
        mocker.patch.object(c.cl, "login", return_value=None)
        dump_mock = mocker.patch.object(c, "_dump_settings", return_value=None)

        c.login(username="test", password="pass")

        dump_mock.assert_called_once()

    def test_login_fallback_to_global_session_file(self, mocker, client: InstagramClient):
        """login() falls back to IG_SESSION_FILE when _session_file_path is None."""
        mocker.patch("os.path.exists", return_value=False)
        mocker.patch.object(client.cl, "login", return_value=None)
        dump_mock = mocker.patch.object(client, "_dump_settings", return_value=None)

        client.login(username="test", password="pass")

        dump_mock.assert_called_once()

    def test_dump_settings_uses_session_file_path(self, mocker):
        """_dump_settings() uses _session_file_path when set."""
        path = "data/sessions/custom.json"
        c = InstagramClient(session_file_path=path)

        makedirs_mock = mocker.patch("os.makedirs", return_value=None)
        dump_mock = mocker.patch.object(c.cl, "dump_settings", return_value=None)
        chmod_mock = mocker.patch("os.chmod", return_value=None)

        c._dump_settings()

        makedirs_mock.assert_called_once()
        dump_mock.assert_called_once_with(path)
        chmod_mock.assert_called_once_with(path, 0o600)

    def test_dump_settings_fallback_to_global(self, client: InstagramClient, mocker):
        """_dump_settings() falls back to IG_SESSION_FILE when _session_file_path is None."""
        mocker.patch("os.makedirs", return_value=None)
        dump_mock = mocker.patch.object(client.cl, "dump_settings", return_value=None)
        chmod_mock = mocker.patch("os.chmod", return_value=None)

        client._dump_settings()

        dump_mock.assert_called_once()
        chmod_mock.assert_called_once()


# ── Adversarial: malformed_input ───────────────────────────────────────────────


class TestMalformedInput:
    def test_fetch_profile_empty_username(self, mocker, client: InstagramClient):
        """fetch_profile with empty string username should still call the client."""
        mock_user = mocker.MagicMock()
        mock_user.pk = 0
        mocker.patch.object(client.cl, "user_info_from_username", return_value=mock_user)

        result = client.fetch_profile(username="")
        assert result is not None

    def test_fetch_profile_none_username_own_profile(self, mocker, client: InstagramClient):
        """fetch_profile with username=None fetches own profile without error."""
        client.cl.user_id = "own_123"
        mock_user = mocker.MagicMock()
        mock_user.pk = 42
        mocker.patch.object(client.cl, "user_info", return_value=mock_user)

        result = client.fetch_profile(username=None)
        assert result is not None
        assert result["pk"] == 42
