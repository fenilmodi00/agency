# tools/connectors/ledger_tools.py
"""CrewAI tools wrapping ledger.py connector for metric ledger operations."""

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
    / "marketing-skills" / "scripts" / "connectors" / "ledger.py"
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
            logger.warning("ledger.py failed (rc=%d): %s", result.returncode, result.stderr)
            return {"error": result.stderr.strip() or "connector failed", "returncode": result.returncode}
        stdout = result.stdout.strip()
        if not stdout:
            return {}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw_output": stdout}
    except subprocess.TimeoutExpired:
        logger.warning("ledger.py timed out after %ds", CONNECTOR_TIMEOUT_SECONDS)
        return {"error": "timeout"}
    except Exception as exc:
        logger.error("ledger.py exception: %s", exc)
        return {"error": str(exc)}


@tool
def ledger_record(target: str, source: str, data_json: str) -> dict:
    """Record a metric entry in the ledger for a target from a source.

    Args:
        target: The metric target identifier.
        source: The data source identifier.
        data_json: JSON string of metric data to record.

    Returns:
        Dict with status on success.
        Returns {"error": ...} on failure.
    """
    return _run_connector(["record", target, source, data_json])


@tool
def ledger_diff(target: str, source: str) -> dict:
    """Compute the difference between current and previous metric values.

    Args:
        target: The metric target identifier.
        source: The data source identifier.

    Returns:
        Dict with delta on success.
        Returns {"error": ...} on failure.
    """
    return _run_connector(["diff", target, source])
