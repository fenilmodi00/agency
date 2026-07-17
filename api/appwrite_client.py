"""Appwrite Server SDK wrapper for creator profile storage.

Provides methods to store, update, and clear creator profiles in the
Appwrite 'creators' table. Singleton pattern — one instance per process.
"""

from __future__ import annotations

import os
import threading

from appwrite.client import Client
from appwrite.exception import AppwriteException
from appwrite.permission import Permission
from appwrite.role import Role
from appwrite.query import Query
from appwrite.services.databases import Databases
from loguru import logger

# ── Env vars ──────────────────────────────────────────────────────────────────

APPWRITE_ENDPOINT: str = os.getenv("APPWRITE_ENDPOINT", "https://sgp.cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID: str = os.getenv("APPWRITE_PROJECT_ID", "")
APPWRITE_API_KEY: str = os.getenv("APPWRITE_API_KEY", "")
APPWRITE_DATABASE_ID: str = os.getenv("APPWRITE_DATABASE_ID", "vernacular_saas")
APPWRITE_CREATORS_TABLE_ID: str = os.getenv("APPWRITE_CREATORS_TABLE_ID", "creators")


class AppwriteClient:
    """Wraps the Appwrite Python SDK for server-side operations.

    Uses API key auth (server integration). Stores and updates creator
    profiles in the `creators` table within `vernacular_saas` database.
    """

    def __init__(self) -> None:
        self._client = Client()
        self._client.set_endpoint(APPWRITE_ENDPOINT)
        self._client.set_project(APPWRITE_PROJECT_ID)
        self._client.set_key(APPWRITE_API_KEY)
        self._databases = Databases(self._client)

    @staticmethod
    def _user_permissions(appwrite_uid: str) -> list[str]:
        """Return read/update/delete permissions for a single Appwrite user."""
        return [
            Permission.read(Role.user(appwrite_uid)),
            Permission.update(Role.user(appwrite_uid)),
            Permission.delete(Role.user(appwrite_uid)),
        ]

    def store_creator_profile(self, clerk_user_id: str, profile: dict) -> bool:
        """Upsert a creator profile in Appwrite.

        Queries the creators table for an existing row with matching
        clerk_user_id. If found, updates it. Otherwise creates a new row.

        Args:
            clerk_user_id: Clerk user ID (used as the lookup key).
            profile: Dictionary of creator fields (matches Creator interface).

        Returns:
            True on success, False on failure.
        """
        profile["clerk_user_id"] = clerk_user_id
        try:
            result = self._databases.list_documents(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=APPWRITE_CREATORS_TABLE_ID,
                queries=[Query.equal("clerk_user_id", clerk_user_id), Query.limit(1)],
            )
            documents = result.get("documents", [])

            existing = documents[0] if documents else None

            if existing:
                doc_id = existing["$id"]
                self._databases.update_document(
                    database_id=APPWRITE_DATABASE_ID,
                    collection_id=APPWRITE_CREATORS_TABLE_ID,
                    document_id=doc_id,
                    data=profile,
                    permissions=self._user_permissions(clerk_user_id),
                )
                logger.info("Updated creator profile for {} (doc {})", clerk_user_id, doc_id)
            else:
                self._databases.create_document(
                    database_id=APPWRITE_DATABASE_ID,
                    collection_id=APPWRITE_CREATORS_TABLE_ID,
                    document_id="unique()",
                    data=profile,
                    permissions=self._user_permissions(clerk_user_id),
                )
                logger.info("Created creator profile for {}", clerk_user_id)

            return True
        except AppwriteException:
            logger.exception("Appwrite error storing creator profile for {}", clerk_user_id)
            return False
        except Exception:
            logger.exception("Unexpected error storing creator profile for {}", clerk_user_id)
            return False

    def clear_creator_session(self, clerk_user_id: str) -> bool:
        """Clear session fields and set is_onboarded=False for a creator.

        Used when a user disconnects their Instagram account.

        Args:
            clerk_user_id: Clerk user ID.

        Returns:
            True on success, False on failure.
        """
        try:
            result = self._databases.list_documents(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=APPWRITE_CREATORS_TABLE_ID,
                queries=[Query.equal("clerk_user_id", clerk_user_id), Query.limit(1)],
            )
            documents = result.get("documents", [])

            existing = documents[0] if documents else None

            if not existing:
                logger.warning("No creator profile found for {} to clear", clerk_user_id)
                return False

            doc_id = existing["$id"]
            self._databases.update_document(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=APPWRITE_CREATORS_TABLE_ID,
                document_id=doc_id,
                data={
                    "access_token": "",
                    "token_expires_at": "",
                    "is_onboarded": False,
                },
            )
            logger.info("Cleared session for {}", clerk_user_id)
            return True
        except AppwriteException:
            logger.exception("Appwrite error clearing session for {}", clerk_user_id)
            return False
        except Exception:
            logger.exception("Unexpected error clearing session for {}", clerk_user_id)
            return False


# ── Singleton ─────────────────────────────────────────────────────────────────

_appwrite_client: AppwriteClient | None = None
_aw_lock = threading.Lock()


def get_appwrite_client() -> AppwriteClient:
    """Return the singleton AppwriteClient instance."""
    global _appwrite_client
    if _appwrite_client is None:
        with _aw_lock:
            if _appwrite_client is None:
                _appwrite_client = AppwriteClient()
    return _appwrite_client
