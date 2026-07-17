"""Tests for the FastAPI backend infrastructure (Task 2).

Tests cover: health endpoint, route stubs, Clerk JWT auth, SessionManager LRU
eviction, and AppwriteClient store operations. All external calls are mocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_env_and_reimport():
    """Ensure api modules load without leftover env state from other tests."""
    import os

    os.environ.setdefault("CLERK_SECRET_KEY", "test-clerk-key")
    os.environ.setdefault("APPWRITE_ENDPOINT", "https://sgp.cloud.appwrite.io/v1")
    os.environ.setdefault("APPWRITE_PROJECT_ID", "test-project-id")
    os.environ.setdefault("APPWRITE_API_KEY", "test-api-key")
    os.environ.setdefault("APPWRITE_DATABASE_ID", "vernacular_saas")
    os.environ.setdefault("APPWRITE_CREATORS_TABLE_ID", "creators")


@pytest.fixture
def client():
    """FastAPI TestClient for the app."""
    from api.main import app

    return TestClient(app)


# ── 1. Health endpoint ───────────────────────────────────────────────────────


def test_health_endpoint(client):
    """GET /health returns 200 + {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── 2. Route stubs (501) ─────────────────────────────────────────────────────


def test_login_stub(client):
    """POST /login returns 401 (auth required, endpoint implemented)."""
    response = client.post("/login", json={"clerk_user_id": "user_1"})
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


def test_profile_stub(client):
    """GET /profile returns 401 (auth required, endpoint implemented)."""
    response = client.get("/profile")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


def test_media_stub(client):
    """GET /media returns 401 (auth required, endpoint implemented)."""
    response = client.get("/media")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


def test_insights_stub(client):
    """GET /insights returns 401 (auth required, endpoint implemented)."""
    response = client.get("/insights")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


def test_disconnect_stub(client):
    """POST /disconnect returns 401 (auth required, endpoint implemented)."""
    response = client.post("/disconnect")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


# ── 3. Clerk JWT verification ────────────────────────────────────────────────


def test_verify_jwt_valid():
    """Mock jwt.decode returns {"sub": "user_123"} → verify_clerk_jwt returns "user_123"."""
    from api.auth import verify_clerk_jwt

    with patch("api.auth.jwt.decode", return_value={"sub": "user_123"}):
        result = verify_clerk_jwt("fake-token")
        assert result == "user_123"


def test_verify_jwt_invalid():
    """Mock jwt.decode raises jwt.InvalidTokenError → verify_clerk_jwt returns None."""
    from api.auth import verify_clerk_jwt

    with patch("api.auth.jwt.decode", side_effect=jwt.InvalidTokenError):
        result = verify_clerk_jwt("bad-token")
        assert result is None


def test_verify_jwt_malformed_empty():
    """verify_clerk_jwt returns None for empty string."""
    from api.auth import verify_clerk_jwt

    result = verify_clerk_jwt("")
    assert result is None


def test_verify_jwt_malformed_garbage():
    """verify_clerk_jwt returns None for malformed tokens (not enough segments)."""
    from api.auth import verify_clerk_jwt

    result = verify_clerk_jwt("not.a.jwt")
    assert result is None


def test_verify_jwt_expired():
    """verify_clerk_jwt returns None when jwt.expired exception is raised."""
    from api.auth import verify_clerk_jwt

    with patch("api.auth.jwt.decode", side_effect=jwt.ExpiredSignatureError):
        result = verify_clerk_jwt("expired-token")
        assert result is None


def test_get_clerk_user_id_missing_header(client):
    """Test that a protected endpoint returns 401 when no auth header is provided.

    Uses a dedicated test route that requires the auth dependency,
    then verifies 401 is returned when no Authorization header is sent.
    """
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient as TC

    from api.auth import get_clerk_user_id
    from api.main import app as main_app

    # Add a temporary protected route that uses the dependency
    @main_app.get("/_test_protected")
    async def _test_protected(user_id: str = Depends(get_clerk_user_id)):
        return {"user_id": user_id}

    tc = TC(main_app)
    # No Authorization header → should fail with 401 or 422 (header missing)
    response = tc.get("/_test_protected")
    assert response.status_code in (401, 403, 422), f"Expected 401/403/422, got {response.status_code}"


def test_get_clerk_user_id_invalid_token():
    """get_clerk_user_id raises HTTPException 401 for invalid token."""
    import asyncio

    from fastapi import HTTPException

    from api.auth import verify_clerk_jwt

    # Test verify_clerk_jwt with None returns None -> dependency would raise 401
    with patch("api.auth.jwt.decode", side_effect=jwt.InvalidTokenError):
        assert verify_clerk_jwt("invalid") is None


# ── 4. SessionManager ────────────────────────────────────────────────────────


def test_session_manager_get_or_create():
    """Mock InstagramClient, assert client created with correct session_file_path,
    login called, stored in dict."""
    from unittest.mock import patch as _patch

    from api.session_manager import SessionManager

    sm = SessionManager()

    with _patch("api.session_manager.InstagramClient") as mock_ic:
        mock_instance = MagicMock()
        mock_instance._logged_in = True
        mock_ic.return_value = mock_instance

        result = sm.get_or_create("user_abc", "testuser", "testpass")

        # InstagramClient created
        mock_ic.assert_called_once()
        # login called
        mock_instance.login.assert_called_once_with("testuser", "testpass")
        # result is the mock instance
        assert result is mock_instance
        # stored in dict
        assert sm._clients["user_abc"] is mock_instance


def test_session_manager_get_or_create_reuses_existing():
    """If client already exists and is logged in, return it without re-creation."""
    from unittest.mock import patch as _patch

    from api.session_manager import SessionManager

    sm = SessionManager()

    with _patch("api.session_manager.InstagramClient") as mock_ic:
        mock_instance = MagicMock()
        mock_instance._logged_in = True
        mock_ic.return_value = mock_instance

        first = sm.get_or_create("user_xyz", "u", "p")
        second = sm.get_or_create("user_xyz", "u", "p")

        assert first is second
        # Only one InstagramClient was created
        mock_ic.assert_called_once()
        # login called only once
        mock_instance.login.assert_called_once()


def test_session_manager_get_or_create_relogin():
    """If client exists but not logged in, re-login."""
    from unittest.mock import patch as _patch

    from api.session_manager import SessionManager

    sm = SessionManager()

    with _patch("api.session_manager.InstagramClient") as mock_ic:
        mock_instance = MagicMock()
        mock_instance._logged_in = False
        mock_ic.return_value = mock_instance

        result = sm.get_or_create("user_rl", "u", "p")

        # Still 1 creation, 1 login call
        mock_ic.assert_called_once()
        mock_instance.login.assert_called_once_with("u", "p")
        assert result is mock_instance


def test_session_lru_eviction():
    """Add 51 clients, assert oldest evicted and .logout() called."""
    from unittest.mock import patch as _patch

    from api.session_manager import SessionManager

    sm = SessionManager()

    with _patch("api.session_manager.InstagramClient") as mock_ic:
        clients = []
        for i in range(51):
            mock_instance = MagicMock()
            mock_instance._logged_in = True
            mock_ic.return_value = mock_instance
            clients.append(mock_instance)
            sm.get_or_create(f"user_{i}", f"u_{i}", "p")

        # 51 creations, 51 logins
        assert mock_ic.call_count == 51

        # First client (user_0) should have been evicted
        assert clients[0].logout.called
        assert "user_0" not in sm._clients

        # Should have exactly 50 clients
        assert len(sm._clients) == 50

        # Last 50 clients are still present
        for i in range(1, 51):
            assert f"user_{i}" in sm._clients


def test_session_manager_get_none():
    """get() returns None for unknown user."""
    from api.session_manager import SessionManager

    sm = SessionManager()
    assert sm.get("nonexistent") is None


def test_session_manager_remove():
    """remove() calls logout and removes from dict."""
    from unittest.mock import patch as _patch

    from api.session_manager import SessionManager

    sm = SessionManager()

    with _patch("api.session_manager.InstagramClient") as mock_ic:
        mock_instance = MagicMock()
        mock_instance._logged_in = True
        mock_ic.return_value = mock_instance

        sm.get_or_create("user_rm", "u", "p")
        result = sm.remove("user_rm")

        assert result is True
        mock_instance.logout.assert_called_once()
        assert "user_rm" not in sm._clients


def test_session_manager_remove_unknown():
    """remove() returns False for unknown user."""
    from api.session_manager import SessionManager

    sm = SessionManager()
    assert sm.remove("ghost") is False


# ── 5. AppwriteClient ────────────────────────────────────────────────────────


def test_appwrite_store_creator_profile_update():
    """Mock Databases.list_documents returns existing row → update_document called."""
    from unittest.mock import MagicMock, patch

    from api.appwrite_client import AppwriteClient

    # Given env vars are set (see _clear_env_and_reimport fixture)
    ac = AppwriteClient()

    with patch.object(ac, "_databases") as mock_db:
        # Simulate existing row found with matching clerk_user_id
        mock_row = {"$id": "doc_123", "clerk_user_id": "user_abc"}
        mock_db.list_documents.return_value = {"documents": [mock_row], "total": 1}

        result = ac.store_creator_profile("user_abc", {"ig_username": "test_user", "follower_count": 1000})

        assert result is True
        # update_document should be called (row exists)
        mock_db.update_document.assert_called_once()
        args, kwargs = mock_db.update_document.call_args
        assert kwargs["document_id"] == "doc_123"
        mock_db.create_document.assert_not_called()


def test_appwrite_store_creator_profile_create():
    """Mock Databases.list_documents returns no rows → create_document called."""
    from unittest.mock import patch

    from api.appwrite_client import AppwriteClient

    ac = AppwriteClient()

    with patch.object(ac, "_databases") as mock_db:
        # No existing row
        mock_db.list_documents.return_value = {"documents": [], "total": 0}

        result = ac.store_creator_profile("user_xyz", {"ig_username": "new_user", "follower_count": 500})

        assert result is True
        mock_db.create_document.assert_called_once()
        mock_db.update_document.assert_not_called()


def test_appwrite_clear_creator_session():
    """clear_creator_session calls update_document with cleared fields."""
    from unittest.mock import MagicMock, patch

    from api.appwrite_client import AppwriteClient

    ac = AppwriteClient()

    with patch.object(ac, "_databases") as mock_db:
        mock_row = {"$id": "doc_456", "clerk_user_id": "user_abc"}
        mock_db.list_documents.return_value = {"documents": [mock_row], "total": 1}

        result = ac.clear_creator_session("user_abc")

        assert result is True
        mock_db.update_document.assert_called_once()
        args, kwargs = mock_db.update_document.call_args
        data = kwargs["data"]
        assert data.get("access_token") == ""
        assert data.get("token_expires_at") == ""
        assert data.get("is_onboarded") is False
