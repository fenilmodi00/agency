# tools/connectors/tavily_tools.py
"""CrewAI tools wrapping tavily.py connector for web search and content extraction."""

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
    / "marketing-skills" / "scripts" / "connectors" / "tavily.py"
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
            logger.warning("tavily.py failed (rc=%d): %s", result.returncode, result.stderr)
            return {"error": result.stderr.strip() or "connector failed", "returncode": result.returncode}
        stdout = result.stdout.strip()
        if not stdout:
            return {}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw_output": stdout}
    except subprocess.TimeoutExpired:
        logger.warning("tavily.py timed out after %ds", CONNECTOR_TIMEOUT_SECONDS)
        return {"error": "timeout"}
    except Exception as exc:
        logger.error("tavily.py exception: %s", exc)
        return {"error": str(exc)}


@tool
def tavily_search(query: str, max_results: int = 5) -> dict:
    """Search the web using Tavily AI search engine.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (default: 5).

    Returns:
        Dict with results list and answer string on success.
        Requires TAVILY_API_KEY env var. Returns {"error": ...} on failure.
    """
    return _run_connector(["search", query, "--max-results", str(max_results)])


@tool
def tavily_extract(url: str) -> dict:
    """Extract clean content from a URL using Tavily extract API.

    Args:
        url: The URL to extract content from.

    Returns:
        Dict with extracted content on success.
        Requires TAVILY_API_KEY env var. Returns {"error": ...} on failure.
    """
    return _run_connector(["extract", url])
