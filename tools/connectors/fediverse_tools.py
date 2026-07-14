# tools/connectors/fediverse_tools.py
"""CrewAI tools wrapping fediverse.py connector for Mastodon/Lemmy social metrics."""

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
    / "marketing-skills" / "scripts" / "connectors" / "fediverse.py"
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
            logger.warning("fediverse.py failed (rc=%d): %s", result.returncode, result.stderr)
            return {"error": result.stderr.strip() or "connector failed", "returncode": result.returncode}
        stdout = result.stdout.strip()
        if not stdout:
            return {}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw_output": stdout}
    except subprocess.TimeoutExpired:
        logger.warning("fediverse.py timed out after %ds", CONNECTOR_TIMEOUT_SECONDS)
        return {"error": "timeout"}
    except Exception as exc:
        logger.error("fediverse.py exception: %s", exc)
        return {"error": str(exc)}


@tool
def mastodon_trends(instance: str) -> dict:
    """Get trending tags on a Mastodon instance.

    Args:
        instance: Mastodon instance domain (e.g. 'mastodon.social').

    Returns:
        Dict with tags list on success.
        Returns {"error": ...} on failure.
    """
    return _run_connector(["mastodon-trends", instance])


@tool
def mastodon_tag(instance: str, tag: str) -> list:
    """Search for public posts with a specific hashtag on a Mastodon instance.

    Args:
        instance: Mastodon instance domain (e.g. 'mastodon.social').
        tag: Hashtag to search for (without # prefix).

    Returns:
        List of post dicts on success.
        Returns [{"error": ...}] on failure.
    """
    result = _run_connector(["mastodon-tag", instance, tag])
    return result if isinstance(result, list) else [{"error": "unexpected response"}]


@tool
def lemmy_search(query: str) -> list:
    """Search Lemmy communities and posts by keyword.

    Args:
        query: Search query string.

    Returns:
        List of result dicts on success.
        Returns [{"error": ...}] on failure.
    """
    result = _run_connector(["lemmy-search", query])
    return result if isinstance(result, list) else [{"error": "unexpected response"}]
