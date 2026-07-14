# tools/connectors/bluesky_tools.py
"""CrewAI tools wrapping bluesky.py connector for Bluesky social metrics."""

import json
import subprocess
from functools import wraps
from pathlib import Path
from typing import Any

from loguru import logger

try:
    from crewai.tools import tool as _crewai_tool

    def tool(fn):  # type: ignore[misc]
        """Wraps fn for CrewAI compat. Returns callable with .run(), .name, .description."""
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper.name = fn.__name__
        wrapper.description = (fn.__doc__ or "").strip()
        wrapper.run = wrapper
        return wrapper
except ImportError:

    def tool(fn):  # type: ignore[misc]
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper.name = fn.__name__
        wrapper.run = wrapper
        return wrapper


_CONNECTOR_SCRIPT = (
    Path(__file__).resolve().parent.parent.parent
    / "marketing-skills" / "scripts" / "connectors" / "bluesky.py"
)


def _run_connector(args: list[str]) -> dict[str, Any] | list:
    """Run a connector script and return parsed JSON. Returns error dict on failure."""
    from config import CONNECTOR_TIMEOUT_SECONDS

    cmd = ["python", str(_CONNECTOR_SCRIPT)] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=CONNECTOR_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            logger.warning("bluesky.py failed (rc=%d): %s", result.returncode, result.stderr)
            return {"error": result.stderr.strip() or "connector failed", "returncode": result.returncode}
        stdout = result.stdout.strip()
        if not stdout:
            return {}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw_output": stdout}
    except subprocess.TimeoutExpired:
        logger.warning("bluesky.py timed out after %ds", CONNECTOR_TIMEOUT_SECONDS)
        return {"error": "timeout"}
    except Exception as exc:
        logger.error("bluesky.py exception: %s", exc)
        return {"error": str(exc)}


@tool
def bluesky_profile(handle: str) -> dict:
    """Get Bluesky profile details (display name, followers, follows, posts).

    Args:
        handle: Bluesky handle (e.g. 'test.bsky.social').

    Returns:
        Dict with handle, display_name, followers, follows, posts_count on success.
        Returns {"error": ...} on failure.
    """
    return _run_connector(["profile", handle])


@tool
def bluesky_feed(handle: str) -> list:
    """Get recent posts from a Bluesky user's feed.

    Args:
        handle: Bluesky handle (e.g. 'test.bsky.social').

    Returns:
        List of dicts with post text, likes, reposts, replies on success.
        Returns [{"error": ...}] on failure.
    """
    return _run_connector(["feed", handle])


@tool
def bluesky_actors(query: str) -> list:
    """Search for Bluesky actors by display name or handle.

    Args:
        query: Search query string.

    Returns:
        List of matching actor profiles.
        Returns [{"error": ...}] on failure.
    """
    return _run_connector(["actors", query])
