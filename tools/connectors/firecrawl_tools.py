# tools/connectors/firecrawl_tools.py
"""CrewAI tools wrapping firecrawl.py connector for web crawling and scraping."""

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
    / "marketing-skills" / "scripts" / "connectors" / "firecrawl.py"
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
            logger.warning("firecrawl.py failed (rc=%d): %s", result.returncode, result.stderr)
            return {"error": result.stderr.strip() or "connector failed", "returncode": result.returncode}
        stdout = result.stdout.strip()
        if not stdout:
            return {}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw_output": stdout}
    except subprocess.TimeoutExpired:
        logger.warning("firecrawl.py timed out after %ds", CONNECTOR_TIMEOUT_SECONDS)
        return {"error": "timeout"}
    except Exception as exc:
        logger.error("firecrawl.py exception: %s", exc)
        return {"error": str(exc)}


@tool
def firecrawl_search(query: str, limit: int = 10) -> list:
    """Search the web using Firecrawl search API.

    Args:
        query: Search query string.
        limit: Maximum number of results to return (default: 10).

    Returns:
        List of search result dicts with url, title, content on success.
        Requires FIRECRAWL_API_KEY env var. Returns [{"error": ...}] on failure.
    """
    result = _run_connector(["search", query, "--limit", str(limit)])
    return result if isinstance(result, list) else [{"error": "unexpected response"}]


@tool
def firecrawl_scrape(url: str) -> dict:
    """Scrape a single URL using Firecrawl.

    Args:
        url: The URL to scrape.

    Returns:
        Dict with scraped content (markdown, metadata) on success.
        Requires FIRECRAWL_API_KEY env var. Returns {"error": ...} on failure.
    """
    return _run_connector(["scrape", url])


@tool
def firecrawl_map(domain: str) -> list:
    """Map all discovered URLs on a domain using Firecrawl.

    Args:
        domain: The domain to map (e.g. 'example.com').

    Returns:
        List of discovered page URLs.
        Requires FIRECRAWL_API_KEY env var. Returns [{"error": ...}] on failure.
    """
    result = _run_connector(["map", domain])
    return result if isinstance(result, list) else [{"error": "unexpected response"}]
