"""CrewAI tools for Instagram DMs, threads, and profile lookup.

All functions use the singleton from `ig_client.get_ig_client()` —
no additional Client instances are created.
"""

from functools import wraps

from instagrapi.exceptions import UserNotFound

try:
    from crewai.tools import tool
except ImportError:
    class _Tool:
        def __init__(self, fn):
            self.fn = fn
            self.name = fn.__name__
            self.description = (fn.__doc__ or "").strip()

        def __call__(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

        def run(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

    def tool(fn):
        return _Tool(fn)

from ig_client import get_ig_client


@tool
def send_instagram_dm(creator_username: str, message: str) -> dict:
    """Send a direct message to an Instagram user by username.

    Resolves the username to a user_id first, then calls send_dm.
    Returns: {"success": bool, "thread_id": str|None, "error": str|None}
    """
    client = get_ig_client()

    # Resolve username -> user_id
    try:
        user_id = client.user_id_from_username(creator_username)
    except UserNotFound:
        return {
            "success": False,
            "thread_id": None,
            "error": f"UserNotFound: {creator_username}",
        }

    if user_id is None:
        return {
            "success": False,
            "thread_id": None,
            "error": f"Could not resolve user_id for {creator_username}",
        }

    try:
        return client.send_dm(user_id, message)
    except UserNotFound:
        return {
            "success": False,
            "thread_id": None,
            "error": f"UserNotFound during DM send: {creator_username}",
        }
    except Exception as exc:
        return {
            "success": False,
            "thread_id": None,
            "error": str(exc),
        }


@tool
def read_instagram_threads(amount: int = 20) -> list[dict]:
    """Read recent direct message threads.

    Returns a list of thread dicts (serialised from instagrapi objects).
    """
    client = get_ig_client()
    threads = client.read_threads(amount=amount)

    result: list[dict] = []
    for t in threads:
        result.append({
            "thread_id": str(getattr(t, "thread_id", "")),
            "users": [str(getattr(u, "username", "")) for u in (getattr(t, "users", []) or [])],
            "last_message": getattr(t, "last_message", {}),
            "last_activity": getattr(t, "last_activity", None),
        })
    return result


@tool
def read_thread_messages(thread_id: str, amount: int = 50) -> list[dict]:
    """Read messages from a specific DM thread.

    Returns a list of message dicts.
    """
    client = get_ig_client()
    messages = client.read_thread(thread_id, amount=amount)

    result: list[dict] = []
    for m in messages:
        result.append({
            "message_id": str(getattr(m, "id", "")),
            "user_id": str(getattr(m, "user_id", "")),
            "text": getattr(m, "text", ""),
            "timestamp": getattr(m, "timestamp", None),
        })
    return result


@tool
def get_profile(username: str) -> dict | None:
    """Get public profile info for an Instagram user by username.

    Returns a dict with username, full_name, biografi, etc., or None.
    """
    client = get_ig_client()
    try:
        user = client.cl.user_info_from_username(username)
        if user is None:
            return None
        return {
            "pk": str(getattr(user, "pk", "")),
            "username": getattr(user, "username", ""),
            "full_name": getattr(user, "full_name", ""),
            "biografi": getattr(user, "biografi", ""),
            "external_url": getattr(user, "external_url", ""),
            "follower_count": getattr(user, "follower_count", 0),
            "following_count": getattr(user, "following_count", 0),
            "media_count": getattr(user, "media_count", 0),
            "is_private": getattr(user, "is_private", False),
            "is_verified": getattr(user, "is_verified", False),
            "profile_pic_url": str(getattr(user, "profile_pic_url", "")),
        }
    except UserNotFound:
        return None
    except Exception:
        return None