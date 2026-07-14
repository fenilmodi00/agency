# tools/connectors/doh_tools.py
"""CrewAI tools wrapping doh.py connector for DNS-over-HTTPS lookups."""

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
    / "marketing-skills" / "scripts" / "connectors" / "doh.py"
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
            logger.warning("doh.py failed (rc=%d): %s", result.returncode, result.stderr)
            return {"error": result.stderr.strip() or "connector failed", "returncode": result.returncode}
        stdout = result.stdout.strip()
        if not stdout:
            return {}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw_output": stdout}
    except subprocess.TimeoutExpired:
        logger.warning("doh.py timed out after %ds", CONNECTOR_TIMEOUT_SECONDS)
        return {"error": "timeout"}
    except Exception as exc:
        logger.error("doh.py exception: %s", exc)
        return {"error": str(exc)}


@tool
def dns_auth_records(domain: str) -> dict:
    """Get email authentication DNS records (SPF, DKIM, DMARC) for a domain.

    Args:
        domain: The domain to query (e.g. 'example.com').

    Returns:
        Dict with spf, dkim, dmarc strings on success.
        Returns {"error": ...} on failure.
    """
    return _run_connector(["auth", domain])


@tool
def dns_query(name: str, record_type: str = "TXT") -> dict:
    """Query arbitrary DNS records for a name via DNS-over-HTTPS.

    Args:
        name: DNS name to query (e.g. 'example.com').
        record_type: DNS record type (e.g. 'TXT', 'A', 'MX', default: 'TXT').

    Returns:
        Dict with answers list on success.
        Returns {"error": ...} on failure.
    """
    return _run_connector(["query", name, "--type", record_type])
