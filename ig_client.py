"""instagrapi wrapper with session persistence, jittered delays, rate limiting, and thread safety.

Single Client instance per process. All Instagram calls are serialized via a threading.Lock.
"""

import json
import os
import random
import threading
import time

from loguru import logger
from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    DirectError,
    DirectThreadNotFound,
    LoginRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
    UserNotFound,
)

# ── Defaults (override via env or config.py) ────────────────────────────────
try:
    from config import (
        DM_DELAY_MAX,
        DM_DELAY_MIN,
        IG_PASSWORD,
        IG_SESSION_FILE,
        IG_USERNAME,
        MAX_DMS_PER_DAY,
    )
except ImportError:
    import os as _os

    IG_USERNAME = _os.getenv("IG_USERNAME", "")
    IG_PASSWORD = _os.getenv("IG_PASSWORD", "")
    IG_SESSION_FILE = _os.getenv("IG_SESSION_FILE", "data/ig_session.json")
    _dm_seconds = int(_os.getenv("DM_DELAY_SECONDS", "5"))
    _dm_jitter = int(_os.getenv("DM_DELAY_JITTER", "3"))
    DM_DELAY_MIN = max(0, _dm_seconds - _dm_jitter)
    DM_DELAY_MAX = _dm_seconds + _dm_jitter
    MAX_DMS_PER_DAY = int(_os.getenv("MAX_DMS_PER_DAY", "20"))

# ── Singleton ────────────────────────────────────────────────────────────────

_singleton: "InstagramClient | None" = None
_singleton_lock = threading.Lock()


def get_ig_client() -> "InstagramClient":
    """Return the singleton InstagramClient (lazy init, no login)."""
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = InstagramClient()
    return _singleton


# ── Instagram Client ─────────────────────────────────────────────────────────


class InstagramClient:
    """Thread-safe wrapper around instagrapi.Client.

    __init__ only creates the Client — login() must be called explicitly.
    """

    def __init__(self) -> None:
        self.cl = Client()
        self._lock = threading.Lock()
        self._dm_timestamps: list[float] = []
        self._logged_in = False

    # ── Login ──────────────────────────────────────────────────────────────

    def login(self, username: str | None = None, password: str | None = None) -> bool:
        username = username or IG_USERNAME
        password = password or IG_PASSWORD
        if not username or not password:
            logger.warning("login() called without credentials; skip")
            return False

        try:
            if os.path.exists(IG_SESSION_FILE):
                logger.info("Loading existing session from {}", IG_SESSION_FILE)
                self.cl.load_settings(IG_SESSION_FILE)
                self._logged_in = True
                return True

            logger.info("Fresh login for {}", username)
            self.cl.login(username, password)
            self._dump_settings()
            self._logged_in = True
            return True
        except ChallengeRequired:
            logger.warning("Challenge required for {} — use challenge_code_handler", username)
            return False
        except Exception as exc:
            logger.error("Login failed: {}", exc)
            return False

    def _dump_settings(self) -> None:
        os.makedirs(os.path.dirname(IG_SESSION_FILE) or ".", exist_ok=True)
        self.cl.dump_settings(IG_SESSION_FILE)
        try:
            os.chmod(IG_SESSION_FILE, 0o600)
        except OSError:
            pass  # Windows may ignore chmod

    # ── Challenge ──────────────────────────────────────────────────────────

    def challenge_code_handler(self, username: str, choice: str) -> None:
        logger.info(
            "Challenge for {}: chose '{}'. Manually provide the verification code when prompted by instagrapi.",
            username,
            choice,
        )

    # ── Token-bucket rate limiter ──────────────────────────────────────────

    def _dm_quota_ok(self) -> bool:
        now = time.monotonic()
        window = 86400  # 24 h
        self._dm_timestamps = [t for t in self._dm_timestamps if now - t < window]
        if len(self._dm_timestamps) >= MAX_DMS_PER_DAY:
            oldest = self._dm_timestamps[0]
            wait = oldest + window - now
            logger.warning(
                "Daily DM quota ({}) reached. Resume in {:.0f}s", MAX_DMS_PER_DAY, wait
            )
            return False
        self._dm_timestamps.append(now)
        return True

    # ── DM helpers ─────────────────────────────────────────────────────────

    def send_dm(self, user_id: int, message: str) -> dict:
        """Send a DM with jittered delay and rate limiting.

        Returns: {"success": bool, "thread_id": str|None, "error": str|None}
        """
        with self._lock:
            if not self._logged_in:
                return {"success": False, "thread_id": None, "error": "Not logged in"}

            if not self._dm_quota_ok():
                return {
                    "success": False,
                    "thread_id": None,
                    "error": f"Daily DM limit ({MAX_DMS_PER_DAY}) reached",
                }

            delay = random.uniform(DM_DELAY_MIN, DM_DELAY_MAX)
            logger.info("Pre-DM delay: {:.2f}s", delay)
            time.sleep(delay)

            for attempt in range(2):
                try:
                    dm = self.cl.direct_send(message, user_ids=[user_id])
                    return {
                        "success": True,
                        "thread_id": str(getattr(dm, "thread_id", None)),
                        "error": None,
                    }
                except LoginRequired:
                    if attempt == 0:
                        logger.warning("Session expired, re-login and retry")
                        self.login()
                        continue
                    return {"success": False, "thread_id": None, "error": "LoginRequired"}
                except PleaseWaitFewMinutes:
                    wait = random.uniform(15, 60) * (attempt + 1)
                    logger.warning("Rate limited; backoff {:.1f}s", wait)
                    time.sleep(wait)
                    continue
                except (UserNotFound, DirectError) as exc:
                    return {"success": False, "thread_id": None, "error": type(exc).__name__}
                except ChallengeRequired:
                    return {
                        "success": False,
                        "thread_id": None,
                        "error": "ChallengeRequired",
                    }
                except RateLimitError:
                    wait = random.uniform(15, 60) * (attempt + 1)
                    logger.warning("RateLimitError; backoff {:.1f}s", wait)
                    time.sleep(wait)
                    continue
                except Exception as exc:
                    logger.error("send_dm unexpected: {}", exc)
                    return {"success": False, "thread_id": None, "error": str(exc)}

            return {"success": False, "thread_id": None, "error": "max retries exceeded"}

    # ── Thread read ────────────────────────────────────────────────────────

    def read_threads(self, amount: int = 20) -> list:
        with self._lock:
            for attempt in range(2):
                try:
                    threads = self.cl.direct_threads(amount=amount)
                    return list(threads) if threads else []
                except LoginRequired:
                    if attempt == 0:
                        self.login()
                        continue
                    return []
                except PleaseWaitFewMinutes:
                    time.sleep(random.uniform(15, 60) * (attempt + 1))
                    continue
                except RateLimitError:
                    time.sleep(random.uniform(15, 60) * (attempt + 1))
                    continue
                except Exception as exc:
                    logger.error("read_threads error: {}", exc)
                    return []
            return []

    def read_thread(self, thread_id, amount: int = 50) -> list:
        with self._lock:
            for attempt in range(2):
                try:
                    thread = self.cl.direct_thread(thread_id, amount=amount)
                    msgs = getattr(thread, "items", getattr(thread, "messages", []))
                    return list(msgs) if msgs else []
                except LoginRequired:
                    if attempt == 0:
                        self.login()
                        continue
                    return []
                except (DirectThreadNotFound, UserNotFound):
                    return []
                except PleaseWaitFewMinutes:
                    time.sleep(random.uniform(15, 60) * (attempt + 1))
                    continue
                except RateLimitError:
                    time.sleep(random.uniform(15, 60) * (attempt + 1))
                    continue
                except Exception as exc:
                    logger.error("read_thread error: {}", exc)
                    return []
            return []

    # ── User lookup ────────────────────────────────────────────────────────

    def user_id_from_username(self, username: str) -> int | None:
        with self._lock:
            for attempt in range(2):
                try:
                    user_id = self.cl.user_id_from_username(username)
                    return int(user_id) if user_id else None
                except LoginRequired:
                    if attempt == 0:
                        self.login()
                        continue
                    return None
                except UserNotFound:
                    return None
                except PleaseWaitFewMinutes:
                    time.sleep(random.uniform(15, 60) * (attempt + 1))
                    continue
                except RateLimitError:
                    time.sleep(random.uniform(15, 60) * (attempt + 1))
                    continue
                except Exception as exc:
                    logger.error("user_id_from_username error: {}", exc)
                    return None
            return None