"""Tests for the FastAPI Instagram dashboard endpoints (Task 4).

Covers all 5 implemented routes: login, profile, media, insights, disconnect.
All external calls (Instagram, Appwrite, Clerk JWT) are mocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import jwt
import pytest
from fastapi.testclient import TestClient
from instagrapi.exceptions import ClientError

JWT_SECRET = "test-clerk-key"


def make_jwt(sub: str) -> str:
    """Create a valid HS256 JWT for the test Clerk secret."""
    return jwt.encode({"sub": sub}, JWT_SECRET, algorithm="HS256")


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Ensure Clerk secret and Appwrite env vars are present for api imports."""
    monkeypatch.setenv("CLERK_SECRET_KEY", JWT_SECRET)
    monkeypatch.setenv("APPWRITE_ENDPOINT", "https://sgp.cloud.appwrite.io/v1")
    monkeypatch.setenv("APPWRITE_PROJECT_ID", "test-project-id")
    monkeypatch.setenv("APPWRITE_API_KEY", "test-api-key")
    monkeypatch.setenv("APPWRITE_DATABASE_ID", "vernacular_saas")
    monkeypatch.setenv("APPWRITE_CREATORS_TABLE_ID", "creators")


@pytest.fixture
def client():
    """FastAPI TestClient for the app."""
    from api.main import app

    return TestClient(app)


@pytest.fixture
def mock_session_manager(mocker):
    """Patch get_session_manager to return a controllable mock."""
    mock_sm = mocker.MagicMock()
    mocker.patch("api.main.get_session_manager", return_value=mock_sm)
    return mock_sm


@pytest.fixture
def mock_appwrite_client(mocker):
    """Patch get_appwrite_client to return a controllable mock."""
    mock_aw = mocker.MagicMock()
    mocker.patch("api.main.get_appwrite_client", return_value=mock_aw)
    return mock_aw


@pytest.fixture
def mock_ig_client():
    """Return a fresh mock InstagramClient instance."""
    return MagicMock()


@pytest.fixture
def login_required_cls(mocker):
    """Patch LoginRequired in api.main to a testable exception class."""
    class _LoginRequired(Exception):
        pass

    mocker.patch("api.main.LoginRequired", _LoginRequired)
    return _LoginRequired


# ── POST /login ───────────────────────────────────────────────────────────────


def test_login_happy(client, mock_session_manager, mock_appwrite_client, mock_ig_client):
    """Successful login returns 200 with profile and stores it in Appwrite."""
    profile = {
        "pk": "123456",
        "username": "testuser",
        "full_name": "Test User",
        "biography": "A test bio",
        "external_url": "https://example.com",
        "follower_count": 1000,
        "following_count": 500,
        "media_count": 42,
        "is_private": False,
        "is_verified": False,
        "profile_pic_url": "https://pic.example.com/test.jpg",
        "is_business": True,
    }
    mock_ig_client.fetch_profile.return_value = profile
    mock_session_manager.get_or_create.return_value = mock_ig_client
    mock_appwrite_client.store_creator_profile.return_value = True

    token = make_jwt("user_123")
    response = client.post(
        "/login",
        json={"clerk_id": "user_123", "username": "testuser", "password": "secret"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == profile
    mock_session_manager.get_or_create.assert_called_once_with("user_123", "testuser", "secret")
    mock_ig_client.fetch_profile.assert_called_once_with(username=None)
    mock_appwrite_client.store_creator_profile.assert_called_once()


def test_login_ig_login_fail(client, mock_session_manager, mock_appwrite_client):
    """If session_manager raises a ClientError, return 502 instagram_login_failed."""
    mock_session_manager.get_or_create.side_effect = ClientError("bad credentials")

    token = make_jwt("user_123")
    response = client.post(
        "/login",
        json={"clerk_id": "user_123", "username": "testuser", "password": "secret"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 502
    body = response.json()
    assert body["error"] == "instagram_login_failed"
    assert "bad credentials" in body["message"]
    mock_appwrite_client.store_creator_profile.assert_not_called()


def test_login_no_jwt(client):
    """Missing Authorization header → 401."""
    response = client.post("/login", json={"clerk_id": "user_123", "username": "u", "password": "p"})
    assert response.status_code == 401


def test_login_clerk_id_mismatch(client, mock_session_manager):
    """Body clerk_id must match JWT sub claim; mismatch → 401."""
    token = make_jwt("user_123")
    response = client.post(
        "/login",
        json={"clerk_id": "user_456", "username": "testuser", "password": "secret"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "clerk_id_mismatch"
    mock_session_manager.get_or_create.assert_not_called()


# ── GET /profile ──────────────────────────────────────────────────────────────


def test_profile_happy(client, mock_session_manager, mock_ig_client):
    """Authenticated profile fetch returns 200 with profile dict."""
    profile = {
        "pk": "789",
        "username": "creator",
        "full_name": "Creator Name",
        "biography": "Creator bio",
        "external_url": None,
        "follower_count": 5000,
        "following_count": 300,
        "media_count": 120,
        "is_private": False,
        "is_verified": True,
        "profile_pic_url": "https://pic.example.com/creator.jpg",
        "is_business": False,
    }
    mock_ig_client.fetch_profile.return_value = profile
    mock_session_manager.get.return_value = mock_ig_client

    token = make_jwt("user_123")
    response = client.get("/profile", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == profile
    mock_session_manager.get.assert_called_once_with("user_123")
    mock_ig_client.fetch_profile.assert_called_once_with(username=None)


def test_profile_not_connected(client, mock_session_manager):
    """No client in session registry → 401 not_connected."""
    mock_session_manager.get.return_value = None

    token = make_jwt("user_123")
    response = client.get("/profile", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    body = response.json()
    assert body["error"] == "not_connected"
    assert "connect your Instagram account" in body["message"]


def test_profile_session_expired(client, mock_session_manager, mock_ig_client, login_required_cls):
    """fetch_profile raises LoginRequired → 401 session_expired."""
    mock_ig_client.fetch_profile.side_effect = login_required_cls("session expired")
    mock_session_manager.get.return_value = mock_ig_client

    token = make_jwt("user_123")
    response = client.get("/profile", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    body = response.json()
    assert body["error"] == "session_expired"
    assert "reconnect" in body["message"]


# ── GET /media ────────────────────────────────────────────────────────────────


def test_media_happy(client, mock_session_manager, mock_ig_client):
    """Authenticated media fetch returns 200 with data array."""
    media = [
        {"pk": "1", "caption_text": "Post 1", "media_type": 1},
        {"pk": "2", "caption_text": "Post 2", "media_type": 2},
    ]
    mock_ig_client.fetch_media.return_value = media
    mock_session_manager.get.return_value = mock_ig_client

    token = make_jwt("user_123")
    response = client.get("/media?amount=25", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"data": media}
    mock_ig_client.fetch_media.assert_called_once_with(amount=25)


# ── GET /insights ─────────────────────────────────────────────────────────────


def test_insights_business(client, mock_session_manager, mock_ig_client):
    """Business account insights returns 200 with insights dict."""
    insights = {"data": [{"name": "impressions", "period": "week", "values": [{"value": 1000, "end_time": "2024-01-01"}]}]}
    mock_ig_client.fetch_insights.return_value = insights
    mock_session_manager.get.return_value = mock_ig_client

    token = make_jwt("user_123")
    response = client.get("/insights", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == insights


def test_insights_non_business(client, mock_session_manager, mock_ig_client):
    """Non-business account returns 200 with error dict (graceful, not HTTP error)."""
    insights = {"error": "Business account required for insights"}
    mock_ig_client.fetch_insights.return_value = insights
    mock_session_manager.get.return_value = mock_ig_client

    token = make_jwt("user_123")
    response = client.get("/insights", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == insights


# ── POST /disconnect ──────────────────────────────────────────────────────────


def test_disconnect_happy(client, mock_session_manager, mock_appwrite_client):
    """Successful disconnect returns 200 and clears Appwrite session."""
    mock_session_manager.remove.return_value = True
    mock_appwrite_client.clear_creator_session.return_value = True

    token = make_jwt("user_123")
    response = client.post("/disconnect", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"status": "disconnected"}
    mock_session_manager.remove.assert_called_once_with("user_123")
    mock_appwrite_client.clear_creator_session.assert_called_once_with("user_123")


def test_disconnect_auth_fail(client):
    """Missing JWT on disconnect → 401."""
    response = client.post("/disconnect")
    assert response.status_code == 401


# ── POST /auth/appwrite-session ───────────────────────────────────────────────


def test_appwrite_session_happy(client, mock_appwrite_client):
    """Successful session creation returns 200 with userId and secret."""
    mock_appwrite_client.create_user_session.return_value = {
        "userId": "test-uid",
        "secret": "test-secret",
    }

    token = make_jwt("user_123")
    response = client.post(
        "/auth/appwrite-session",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"userId": "test-uid", "secret": "test-secret"}
    mock_appwrite_client.create_user_session.assert_called_once_with("user_123")


def test_appwrite_session_failure(client, mock_appwrite_client):
    """RuntimeError from Appwrite → 502 appwrite_session_failed."""
    mock_appwrite_client.create_user_session.side_effect = RuntimeError("Appwrite failed")

    token = make_jwt("user_123")
    response = client.post(
        "/auth/appwrite-session",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 502
    body = response.json()
    assert body["error"] == "appwrite_session_failed"
    assert "Appwrite failed" in body["message"]
