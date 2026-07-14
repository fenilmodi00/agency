"""CrewAI tools for the seven truth registries — wraps registry-events.py."""

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from loguru import logger

# Callable tool wrapper — functions remain directly callable AND expose
# .name, .description, .run() for CrewAI compatibility.
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


VALID_REGISTRIES = {"entities", "creators", "claims", "consent", "launches", "channels", "narrative"}

# Path to the registry-events.py runtime (in marketing-skills/scripts/)
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "marketing-skills" / "scripts"
_REGISTRY_SCRIPT = _SCRIPTS_DIR / "registry-events.py"

# Memory root for registry state
_MEMORY_ROOT = Path(__file__).resolve().parent.parent / "data" / "memory"


def _validate_registry(registry: str) -> None:
    if registry not in VALID_REGISTRIES:
        raise ValueError(
            f"Invalid registry '{registry}'. Must be one of: {sorted(VALID_REGISTRIES)}"
        )


def _ensure_memory_dirs() -> None:
    """Create memory/events/ and memory/projections/ if they don't exist."""
    (_MEMORY_ROOT / "events").mkdir(parents=True, exist_ok=True)
    (_MEMORY_ROOT / "projections").mkdir(parents=True, exist_ok=True)


def _run_registry_script(args: list[str], timeout: int | None = None) -> dict[str, Any]:
    """Run registry-events.py with given args and return parsed JSON output."""
    from config import CONNECTOR_TIMEOUT_SECONDS

    effective_timeout = timeout or CONNECTOR_TIMEOUT_SECONDS
    _ensure_memory_dirs()

    cmd = ["python", str(_REGISTRY_SCRIPT)] + args
    env = dict(os.environ)
    env["AARON_SKILLS_ROOT"] = str(_SCRIPTS_DIR.parent)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
            env=env,
        )
        if result.returncode != 0:
            logger.warning("registry-events.py failed (rc=%d): %s", result.returncode, result.stderr)
            return {"error": result.stderr.strip() or "registry script failed", "returncode": result.returncode}

        stdout = result.stdout.strip()
        if not stdout:
            return {}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw_output": stdout}
    except subprocess.TimeoutExpired:
        logger.warning("registry-events.py timed out after %ds", effective_timeout)
        return {"error": "timeout"}
    except Exception as exc:
        logger.error("registry-events.py exception: %s", exc)
        return {"error": str(exc)}


@tool
def registry_propose(
    registry: str,
    aggregate_id: str,
    payload: dict,
    source: str,
    actor_id: str,
) -> dict:
    """Submit an operation:propose event to a registry NDJSON stream.

    Args:
        registry: One of entities, creators, claims, consent, launches, channels, narrative.
        aggregate_id: The stable ID of the entity/creator/etc being proposed.
        payload: The fact payload to propose (must conform to registry-event.schema.json).
        source: The skill/agent submitting the proposal (e.g. "influencer-discovery").
        actor_id: The pseudonymous actor ID.

    Returns:
        Dict with event_id, offset, status on success; {"error": ...} on failure.
        Proposals are non-canonical until accepted by the registry owner.
    """
    _validate_registry(registry)
    request = {
        "operation": "propose",
        "aggregate_id": aggregate_id,
        "payload": payload,
        "source": source,
        "actor": {"type": "skill", "id": actor_id},
    }
    return _run_registry_script([
        "propose", registry,
        "--request-json", json.dumps(request),
    ])


@tool
def registry_get(registry: str, aggregate_id: str) -> dict:
    """Read current projected state for an aggregate from a registry.

    Args:
        registry: One of entities, creators, claims, consent, launches, channels, narrative.
        aggregate_id: The stable ID to look up.

    Returns:
        Dict with the current projected state, or {} if not found or on error.
        A missing record is Unknown, not a negative signal.
    """
    _validate_registry(registry)
    result = _run_registry_script(["get", registry, aggregate_id])
    if "error" in result:
        return {}
    return result


@tool
def registry_verify(registry: str) -> dict:
    """Verify a registry's event stream integrity (offset/hash/idempotency).

    Args:
        registry: One of entities, creators, claims, consent, launches, channels, narrative.

    Returns:
        Dict with verified (bool), offsets, and any integrity errors.
    """
    _validate_registry(registry)
    return _run_registry_script(["verify", registry])