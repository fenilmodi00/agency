# tools/connectors/youtube_tools.py
"""CrewAI tools wrapping youtube.py connector for creator metrics."""

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
    / "marketing-skills" / "scripts" / "connectors" / "youtube.py"
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
            logger.warning("youtube.py failed (rc=%d): %s", result.returncode, result.stderr)
            return {"error": result.stderr.strip() or "connector failed", "returncode": result.returncode}
        stdout = result.stdout.strip()
        if not stdout:
            return {}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw_output": stdout}
    except subprocess.TimeoutExpired:
        logger.warning("youtube.py timed out after %ds", CONNECTOR_TIMEOUT_SECONDS)
        return {"error": "timeout"}
    except Exception as exc:
        logger.error("youtube.py exception: %s", exc)
        return {"error": str(exc)}


@tool
def youtube_channel_stats(handle: str) -> dict:
    """Get real YouTube channel statistics (subscriber count, total views, video count).

    Args:
        handle: YouTube channel handle (e.g. '@testhandle') or channel ID.

    Returns:
        Dict with subscriber_count, total_views, video_count on success.
        Requires YOUTUBE_API_KEY env var. Returns {"error": ...} on failure.
    """
    return _run_connector(["channel", handle])


@tool
def youtube_videos(handle: str, limit: int = 10) -> list:
    """Get per-video stats (views, likes, comments) for a YouTube channel's recent videos.

    Args:
        handle: YouTube channel handle (e.g. '@testhandle') or channel ID.
        limit: Maximum number of videos to return (default: 10).

    Returns:
        List of dicts with title, views, likes, comments on success.
        Returns [{"error": ...}] on failure.
    """
    return _run_connector(["videos", handle, "--limit", str(limit)])
