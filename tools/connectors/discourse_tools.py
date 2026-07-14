# tools/connectors/discourse_tools.py
"""CrewAI tools wrapping discourse.py connector for Discourse forum metrics."""

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
    / "marketing-skills" / "scripts" / "connectors" / "discourse.py"
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
            logger.warning("discourse.py failed (rc=%d): %s", result.returncode, result.stderr)
            return {"error": result.stderr.strip() or "connector failed", "returncode": result.returncode}
        stdout = result.stdout.strip()
        if not stdout:
            return {}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw_output": stdout}
    except subprocess.TimeoutExpired:
        logger.warning("discourse.py timed out after %ds", CONNECTOR_TIMEOUT_SECONDS)
        return {"error": "timeout"}
    except Exception as exc:
        logger.error("discourse.py exception: %s", exc)
        return {"error": str(exc)}


@tool
def discourse_latest(base_url: str) -> dict:
    """Get the latest topics from a Discourse forum.

    Args:
        base_url: Base URL of the Discourse instance (e.g. 'https://forum.example.com').

    Returns:
        Dict with topics list (id, title, posts_count, views) on success.
        Returns {"error": ...} on failure.
    """
    return _run_connector(["latest", base_url])


@tool
def discourse_topic(base_url: str, topic_id: int) -> dict:
    """Get full details of a specific Discourse topic.

    Args:
        base_url: Base URL of the Discourse instance.
        topic_id: Numeric topic ID.

    Returns:
        Dict with topic details and posts on success.
        Returns {"error": ...} on failure.
    """
    return _run_connector(["topic", base_url, str(topic_id)])


@tool
def discourse_health(base_url: str) -> dict:
    """Check the health status of a Discourse instance.

    Args:
        base_url: Base URL of the Discourse instance.

    Returns:
        Dict with health status info on success.
        Returns {"error": ...} on failure.
    """
    return _run_connector(["health", base_url])
