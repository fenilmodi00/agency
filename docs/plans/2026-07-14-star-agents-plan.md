# STAR Agents Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the 5-agent CrewAI pipeline into a 24-agent STAR framework (16 influencer + 8 protocol registry) by enriching agents with marketing-skills playbooks, wiring all bundled connectors as tools, and adding NDJSON event registries.

**Architecture:** Five-layer model — 16 STAR execution agents (4 per phase: scout/target/activate/report), 8 protocol registry agents (utility agents called within phases), 17 connector tool modules + registry tools, dual state (existing SQLite + new NDJSON event streams), and hybrid phase-flag orchestration in main.py (Approach C: backward-compatible default + `--phase` flag).

**Tech Stack:** Python 3.11+, CrewAI, Fireworks AI (GLM-5.2), SQLite, instagrapi, loguru, pytest/pytest-mock, registry-events.py (existing 1805-line NDJSON runtime)

**Design doc:** `docs/plans/2026-07-14-star-agents-design.md` (commit 5f53f0d)

---

## Implementation Order

The plan is organized into 13 tasks. Each task is self-contained and commits independently. Tasks 1-3 are foundations (config, registry tools, connector tools). Tasks 4-8 build the 24 agents in phase order (scout, target, activate, report, protocol). Task 9 creates thin shims for backward compat. Tasks 10-12 wire orchestration (StarCrew, main.py, check_replies.py). Task 13 is final verification.

**Conventions for every agent file** (apply to all 24 agents in Tasks 4-8):
- Follow the existing `agents/discovery.py` pattern: `_parse_prompt_sections()`, `_load_*_prompt()`, `get_*_agent()`, `get_*_task()`
- `try: from crewai import Agent, Task` / `except ImportError:` stubs (like `agents/outreach.py`)
- `verbose=True, allow_delegation=False` on every Agent
- Prompts loaded from `prompts/*_prompt.txt` via `Path.read_text(encoding="utf-8")`
- Tools imported at module level from `tools/`
- Each prompt file uses `## Role / ## Goal / ## Backstory` sections, content distilled from the corresponding `marketing-skills/influencer/**/SKILL.md` or `marketing-skills/protocol/**/SKILL.md`

**Conventions for every test file** (apply to all 28 new test files):
- `import pytest` + `from pytest_mock import MockerFixture` (if mocking)
- Test factory returns Agent-like object, test task has expected_output string, test tool list
- Mock LLM: `mocker.patch("agents.*.get_fireworks_llm", return_value=MagicMock())`
- Mock CrewAI: `mocker.patch("agents.*.Agent", side_effect=lambda **kw: type("Agent", (), kw)())`
- No real network, no real LLM, no real Instagram
- File naming: `tests/test_<agent_name>.py`

---

### Task 1: Config + Memory Directory Foundation

**Files:**
- Modify: `config.py` (add 19 new model config vars + connector timeout)
- Modify: `.env.example` (add new vars)
- Modify: `.gitignore` (add `data/memory/`)
- Create: `data/memory/.gitkeep`
- Create: `data/memory/events/.gitkeep`
- Create: `data/memory/projections/.gitkeep`
- Test: `tests/test_config_star.py`

**Step 1: Write the failing test**

```python
# tests/test_config_star.py
"""Tests for STAR config additions."""

import importlib


def test_scout_model_vars_exist():
    import config
    importlib.reload(config)
    assert hasattr(config, "MODEL_SCOUT_AUDIENCE")
    assert hasattr(config, "MODEL_SCOUT_TREND")
    assert hasattr(config, "MODEL_SCOUT_DISCOVERY")
    assert hasattr(config, "MODEL_SCOUT_FIT")
    assert all(isinstance(getattr(config, v), str) for v in [
        "MODEL_SCOUT_AUDIENCE", "MODEL_SCOUT_TREND", "MODEL_SCOUT_DISCOVERY", "MODEL_SCOUT_FIT"
    ])


def test_target_model_vars_exist():
    import config
    importlib.reload(config)
    for v in ["MODEL_TARGET_COMPETITOR", "MODEL_TARGET_PLANNER", "MODEL_TARGET_BRIEF", "MODEL_TARGET_BUDGET"]:
        assert hasattr(config, v)
        assert isinstance(getattr(config, v), str)


def test_activate_model_vars_exist():
    import config
    importlib.reload(config)
    for v in ["MODEL_ACTIVATE_OUTREACH", "MODEL_ACTIVATE_AUDITOR", "MODEL_ACTIVATE_CONTRACT", "MODEL_ACTIVATE_AMPLIFIER"]:
        assert hasattr(config, v)
        assert isinstance(getattr(config, v), str)


def test_report_model_vars_exist():
    import config
    importlib.reload(config)
    for v in ["MODEL_REPORT_LANDING", "MODEL_REPORT_PERFORMANCE", "MODEL_REPORT_ROI", "MODEL_REPORT_GENERATOR"]:
        assert hasattr(config, v)
        assert isinstance(getattr(config, v), str)


def test_protocol_model_var_exists():
    import config
    importlib.reload(config)
    assert hasattr(config, "MODEL_PROTOCOL_REGISTRY")
    assert isinstance(config.MODEL_PROTOCOL_REGISTRY, str)


def test_connector_timeout_exists():
    import config
    importlib.reload(config)
    assert hasattr(config, "CONNECTOR_TIMEOUT_SECONDS")
    assert isinstance(config.CONNECTOR_TIMEOUT_SECONDS, int)
    assert config.CONNECTOR_TIMEOUT_SECONDS > 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config_star.py -v`
Expected: FAIL with `AttributeError: module 'config' has no attribute 'MODEL_SCOUT_AUDIENCE'`

**Step 3: Write minimal implementation**

Add to `config.py` after the existing `MODEL_CONTRACT` block (line 28):

```python
# ---------------------------------------------------------------------------
# STAR phase model paths (v2 — 24-agent enrichment)
# ---------------------------------------------------------------------------
# Scout phase
MODEL_SCOUT_AUDIENCE: str = os.getenv("MODEL_SCOUT_AUDIENCE", "accounts/fireworks/models/glm-5p2")
MODEL_SCOUT_TREND: str = os.getenv("MODEL_SCOUT_TREND", "accounts/fireworks/models/glm-5p2")
MODEL_SCOUT_DISCOVERY: str = os.getenv("MODEL_SCOUT_DISCOVERY", "accounts/fireworks/models/glm-5p2")
MODEL_SCOUT_FIT: str = os.getenv("MODEL_SCOUT_FIT", "accounts/fireworks/models/glm-5p2")
# Target phase
MODEL_TARGET_COMPETITOR: str = os.getenv("MODEL_TARGET_COMPETITOR", "accounts/fireworks/models/glm-5p2")
MODEL_TARGET_PLANNER: str = os.getenv("MODEL_TARGET_PLANNER", "accounts/fireworks/models/glm-5p2")
MODEL_TARGET_BRIEF: str = os.getenv("MODEL_TARGET_BRIEF", "accounts/fireworks/models/glm-5p2")
MODEL_TARGET_BUDGET: str = os.getenv("MODEL_TARGET_BUDGET", "accounts/fireworks/models/glm-5p2")
# Activate phase
MODEL_ACTIVATE_OUTREACH: str = os.getenv("MODEL_ACTIVATE_OUTREACH", "accounts/fireworks/models/qwen3p7-plus")
MODEL_ACTIVATE_AUDITOR: str = os.getenv("MODEL_ACTIVATE_AUDITOR", "accounts/fireworks/models/glm-5p2")
MODEL_ACTIVATE_CONTRACT: str = os.getenv("MODEL_ACTIVATE_CONTRACT", "accounts/fireworks/models/glm-5p2")
MODEL_ACTIVATE_AMPLIFIER: str = os.getenv("MODEL_ACTIVATE_AMPLIFIER", "accounts/fireworks/models/qwen3p7-plus")
# Report phase
MODEL_REPORT_LANDING: str = os.getenv("MODEL_REPORT_LANDING", "accounts/fireworks/models/glm-5p2")
MODEL_REPORT_PERFORMANCE: str = os.getenv("MODEL_REPORT_PERFORMANCE", "accounts/fireworks/models/glm-5p2")
MODEL_REPORT_ROI: str = os.getenv("MODEL_REPORT_ROI", "accounts/fireworks/models/glm-5p2")
MODEL_REPORT_GENERATOR: str = os.getenv("MODEL_REPORT_GENERATOR", "accounts/fireworks/models/glm-5p2")
# Protocol phase
MODEL_PROTOCOL_REGISTRY: str = os.getenv("MODEL_PROTOCOL_REGISTRY", "accounts/fireworks/models/glm-5p2")

# Connector subprocess timeout (seconds)
CONNECTOR_TIMEOUT_SECONDS: int = int(os.getenv("CONNECTOR_TIMEOUT_SECONDS", "30"))
```

Add to `.gitignore`:
```
# STAR registry state (runtime)
data/memory/
```

Create `data/memory/.gitkeep`, `data/memory/events/.gitkeep`, `data/memory/projections/.gitkeep` (empty files so directory structure exists in git despite `data/memory/` being ignored — actually, since the whole dir is ignored, these won't be tracked. Instead, create the dirs at runtime in `registry_tools.py` Task 2. For now, just add the .gitignore entry.)

Add to `.env.example` the new vars (copy from config.py defaults).

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config_star.py -v`
Expected: PASS (6 tests)

**Step 5: Run existing tests to verify no regressions**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All 117 existing tests still pass

**Step 6: Commit**

```bash
git add config.py .env.example .gitignore tests/test_config_star.py
git commit -m "feat(config): add 19 STAR model paths + connector timeout for 24-agent enrichment"
```

---

### Task 2: Registry Tools (`tools/registry_tools.py`)

**Files:**
- Create: `tools/registry_tools.py`
- Test: `tests/test_registry_tools.py`

**Step 1: Write the failing test**

```python
# tests/test_registry_tools.py
"""Tests for registry tools — wraps registry-events.py via subprocess."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.registry_tools import registry_get, registry_propose, registry_verify


class TestRegistryGet:
    def test_returns_dict_on_success(self):
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"aggregate_id": "creator-abc", "handle": "@test", "rate": 5000})
        mock_result.returncode = 0
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_get("creators", "creator-abc")
        assert isinstance(result, dict)
        assert result["aggregate_id"] == "creator-abc"

    def test_returns_empty_dict_on_failure(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 1
        mock_result.stderr = "not found"
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_get("creators", "nonexistent")
        assert result == {}

    def test_returns_empty_dict_on_timeout(self):
        import subprocess
        with patch("tools.registry_tools.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="python", timeout=30)):
            result = registry_get("creators", "any")
        assert result == {}


class TestRegistryPropose:
    def test_returns_dict_with_event_id_on_success(self):
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"event_id": "evt-001", "offset": 1, "status": "proposed"})
        mock_result.returncode = 0
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_propose(
                registry="creators",
                aggregate_id="creator-new",
                payload={"handle": "@newcreator", "niche": "food"},
                source="influencer-discovery",
                actor_id="scout-agent",
            )
        assert result["event_id"] == "evt-001"
        assert result["status"] == "proposed"

    def test_returns_error_dict_on_failure(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 1
        mock_result.stderr = "invalid payload"
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_propose("creators", "x", {}, "test", "test")
        assert "error" in result


class TestRegistryVerify:
    def test_returns_dict_on_success(self):
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"verified": True, "offsets": 5})
        mock_result.returncode = 0
        with patch("tools.registry_tools.subprocess.run", return_value=mock_result):
            result = registry_verify("creators")
        assert result["verified"] is True


class TestRegistryValidation:
    def test_invalid_registry_raises(self):
        with pytest.raises(ValueError):
            registry_get("invalid_registry", "x")

    def test_invalid_registry_propose_raises(self):
        with pytest.raises(ValueError):
            registry_propose("bad", "x", {}, "test", "test")
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_registry_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.registry_tools'`

**Step 3: Write minimal implementation**

```python
# tools/registry_tools.py
"""CrewAI tools for the seven truth registries — wraps registry-events.py."""

import json
import os
import subprocess
from functools import wraps
from pathlib import Path
from typing import Any

from loguru import logger

try:
    from crewai.tools import tool
except ImportError:
    def tool(fn):  # type: ignore[misc]
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper.name = fn.__name__
        return wrapper


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
    return _run_registry_script(["get", registry, aggregate_id])


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
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_registry_tools.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add tools/registry_tools.py tests/test_registry_tools.py
git commit -m "feat(tools): add registry_tools wrapping registry-events.py for NDJSON registries"
```

---

### Task 3: Connector Tools (`tools/connectors/`)

**Files:**
- Create: `tools/connectors/__init__.py` (empty)
- Create: `tools/connectors/youtube_tools.py`
- Create: `tools/connectors/bluesky_tools.py`
- Create: `tools/connectors/tavily_tools.py`
- Create: `tools/connectors/firecrawl_tools.py`
- Create: `tools/connectors/gdelt_tools.py`
- Create: `tools/connectors/pageviews_tools.py`
- Create: `tools/connectors/hn_tools.py`
- Create: `tools/connectors/rss_tools.py`
- Create: `tools/connectors/doh_tools.py`
- Create: `tools/connectors/wayback_tools.py`
- Create: `tools/connectors/appstore_tools.py`
- Create: `tools/connectors/kg_tools.py`
- Create: `tools/connectors/ledger_tools.py`
- Create: `tools/connectors/experiment_tools.py`
- Create: `tools/connectors/psi_tools.py`
- Create: `tools/connectors/fediverse_tools.py`
- Create: `tools/connectors/discourse_tools.py`
- Test: `tests/test_connector_tools.py`

**Step 1: Write the failing test**

```python
# tests/test_connector_tools.py
"""Tests for connector tools — wraps marketing-skills/scripts/connectors/*.py."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.connectors.youtube_tools import youtube_channel_stats, youtube_videos
from tools.connectors.bluesky_tools import bluesky_profile
from tools.connectors.tavily_tools import tavily_search, tavily_extract
from tools.connectors.firecrawl_tools import firecrawl_search
from tools.connectors.gdelt_tools import gdelt_news_mentions
from tools.connectors.pageviews_tools import wikipedia_pageviews
from tools.connectors.hn_tools import hn_search
from tools.connectors.rss_tools import rss_monitor_feed
from tools.connectors.doh_tools import dns_auth_records
from tools.connectors.wayback_tools import wayback_history
from tools.connectors.appstore_tools import appstore_lookup
from tools.connectors.kg_tools import wikidata_reconcile
from tools.connectors.ledger_tools import ledger_record, ledger_diff
from tools.connectors.experiment_tools import experiment_proportion
from tools.connectors.psi_tools import pagespeed_insights
from tools.connectors.fediverse_tools import mastodon_trends
from tools.connectors.discourse_tools import discourse_latest


def _mock_subprocess(stdout: str = "", returncode: int = 0, stderr: str = ""):
    m = MagicMock()
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


class TestYoutubeTools:
    def test_channel_stats_returns_dict(self):
        with patch("tools.connectors.youtube_tools.subprocess.run",
                   return_value=_mock_subprocess('{"subscriber_count": 47000, "video_count": 120}')):
            result = youtube_channel_stats("@testhandle")
        assert isinstance(result, dict)
        assert result["subscriber_count"] == 47000

    def test_channel_stats_returns_error_on_timeout(self):
        import subprocess
        with patch("tools.connectors.youtube_tools.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd="python", timeout=30)):
            result = youtube_channel_stats("@testhandle")
        assert "error" in result

    def test_videos_returns_list(self):
        with patch("tools.connectors.youtube_tools.subprocess.run",
                   return_value=_mock_subprocess('[{"title": "v1", "views": 1000}]')):
            result = youtube_videos("@testhandle", limit=5)
        assert isinstance(result, list)
        assert len(result) == 1


class TestBlueskyTools:
    def test_profile_returns_dict(self):
        with patch("tools.connectors.bluesky_tools.subprocess.run",
                   return_value=_mock_subprocess('{"handle": "test.bsky.social", "followers": 1000}')):
            result = bluesky_profile("test.bsky.social")
        assert result["handle"] == "test.bsky.social"


class TestTavilyTools:
    def test_search_returns_dict(self):
        with patch("tools.connectors.tavily_tools.subprocess.run",
                   return_value=_mock_subprocess('{"results": [{"title": "x"}], "answer": "yes"}')):
            result = tavily_search("test query", max_results=5)
        assert "results" in result

    def test_extract_returns_dict(self):
        with patch("tools.connectors.tavily_tools.subprocess.run",
                   return_value=_mock_subprocess('{"content": "page text"}')):
            result = tavily_extract("https://example.com")
        assert "content" in result


class TestFirecrawlTools:
    def test_search_returns_list(self):
        with patch("tools.connectors.firecrawl_tools.subprocess.run",
                   return_value=_mock_subprocess('[{"url": "https://x.com", "content": "..."}]')):
            result = firecrawl_search("test", limit=10)
        assert isinstance(result, list)


class TestGdeltTools:
    def test_news_mentions_returns_dict(self):
        with patch("tools.connectors.gdelt_tools.subprocess.run",
                   return_value=_mock_subprocess('{"articles": [{"url": "x"}]}')):
            result = gdelt_news_mentions("test brand", days=30)
        assert "articles" in result


class TestPageviewsTools:
    def test_pageviews_returns_dict(self):
        with patch("tools.connectors.pageviews_tools.subprocess.run",
                   return_value=_mock_subprocess('{"monthly_views": [100, 200, 300]}')):
            result = wikipedia_pageviews("Test Article", months=12)
        assert "monthly_views" in result


class TestHnTools:
    def test_search_returns_dict(self):
        with patch("tools.connectors.hn_tools.subprocess.run",
                   return_value=_mock_subprocess('{"hits": [{"title": "x", "points": 50}]}')):
            result = hn_search("test brand")
        assert "hits" in result


class TestRssTools:
    def test_monitor_returns_dict(self):
        with patch("tools.connectors.rss_tools.subprocess.run",
                   return_value=_mock_subprocess('{"entries": [{"title": "x", "link": "y"}]}')):
            result = rss_monitor_feed("https://example.com/feed.xml")
        assert "entries" in result


class TestDohTools:
    def test_auth_records_returns_dict(self):
        with patch("tools.connectors.doh_tools.subprocess.run",
                   return_value=_mock_subprocess('{"spf": "v=spf1 ...", "dmarc": "v=DMARC1; ..."}')):
            result = dns_auth_records("example.com")
        assert "spf" in result


class TestWaybackTools:
    def test_history_returns_list(self):
        with patch("tools.connectors.wayback_tools.subprocess.run",
                   return_value=_mock_subprocess('[{"timestamp": "20240101", "url": "x"}]')):
            result = wayback_history("https://example.com")
        assert isinstance(result, list)


class TestAppstoreTools:
    def test_lookup_returns_dict(self):
        with patch("tools.connectors.appstore_tools.subprocess.run",
                   return_value=_mock_subprocess('{"trackName": "TestApp", "userRatingCount": 1000}')):
            result = appstore_lookup("123456789")
        assert "trackName" in result


class TestKgTools:
    def test_reconcile_returns_dict(self):
        with patch("tools.connectors.kg_tools.subprocess.run",
                   return_value=_mock_subprocess('{"qid": "Q123", "label": "Test"}')):
            result = wikidata_reconcile("Test Entity")
        assert "qid" in result


class TestLedgerTools:
    def test_record_returns_dict(self):
        with patch("tools.connectors.ledger_tools.subprocess.run",
                   return_value=_mock_subprocess('{"status": "recorded"}')):
            result = ledger_record("test-target", "test-source", '{"metric": 42}')
        assert result["status"] == "recorded"

    def test_diff_returns_dict(self):
        with patch("tools.connectors.ledger_tools.subprocess.run",
                   return_value=_mock_subprocess('{"delta": 10.5}')):
            result = ledger_diff("test-target", "test-source")
        assert "delta" in result


class TestExperimentTools:
    def test_proportion_returns_dict(self):
        with patch("tools.connectors.experiment_tools.subprocess.run",
                   return_value=_mock_subprocess('{"z_stat": 1.96, "p_value": 0.05}')):
            result = experiment_proportion(10, 100, 15, 100)
        assert "z_stat" in result


class TestPsiTools:
    def test_pagespeed_returns_dict(self):
        with patch("tools.connectors.psi_tools.subprocess.run",
                   return_value=_mock_subprocess('{"lighthouse_score": 85, "fcp": 1200}')):
            result = pagespeed_insights("https://example.com")
        assert "lighthouse_score" in result


class TestFediverseTools:
    def test_mastodon_trends_returns_dict(self):
        with patch("tools.connectors.fediverse_tools.subprocess.run",
                   return_value=_mock_subprocess('{"tags": [{"name": "test", "url": "x"}]}')):
            result = mastodon_trends("mastodon.social")
        assert "tags" in result


class TestDiscourseTools:
    def test_latest_returns_dict(self):
        with patch("tools.connectors.discourse_tools.subprocess.run",
                   return_value=_mock_subprocess('{"topics": [{"id": 1, "title": "x"}]}')):
            result = discourse_latest("https://forum.example.com")
        assert "topics" in result
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_connector_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.connectors'`

**Step 3: Write the connector tool pattern**

Every connector tool module follows the same pattern. Here's the complete `youtube_tools.py` — the other 16 modules follow this exact structure with different script names and function signatures.

```python
# tools/connectors/youtube_tools.py
"""CrewAI tools wrapping youtube.py connector for creator metrics."""

import json
import subprocess
from functools import wraps
from pathlib import Path
from typing import Any

from loguru import logger

try:
    from crewai.tools import tool
except ImportError:
    def tool(fn):  # type: ignore[misc]
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper.name = fn.__name__
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
```

**Create the remaining 16 modules** following the same pattern. For each, use the corresponding script in `marketing-skills/scripts/connectors/`:

| Module | Script | Functions |
|---|---|---|
| `bluesky_tools.py` | `bluesky.py` | `bluesky_profile(handle)`, `bluesky_feed(handle)`, `bluesky_actors(query)` |
| `tavily_tools.py` | `tavily.py` | `tavily_search(query, max_results=5)`, `tavily_extract(url)` |
| `firecrawl_tools.py` | `firecrawl.py` | `firecrawl_search(query, limit=10)`, `firecrawl_scrape(url)`, `firecrawl_map(domain)` |
| `gdelt_tools.py` | `gdelt.py` | `gdelt_news_mentions(query, days=30)` |
| `pageviews_tools.py` | `pageviews.py` | `wikipedia_pageviews(article, months=12)` |
| `hn_tools.py` | `hn.py` | `hn_search(query)`, `hn_rank(item_id)` |
| `rss_tools.py` | `rss_monitor.py` | `rss_monitor_feed(feed_url)` |
| `doh_tools.py` | `doh.py` | `dns_auth_records(domain)`, `dns_query(name, record_type="TXT")` |
| `wayback_tools.py` | `wayback.py` | `wayback_history(url)` |
| `appstore_tools.py` | `appstore.py` | `appstore_lookup(app_id)`, `appstore_charts(country="us")` |
| `kg_tools.py` | `kg.py` | `wikidata_reconcile(name)` |
| `ledger_tools.py` | `ledger.py` | `ledger_record(target, source, data_json)`, `ledger_diff(target, source)` |
| `experiment_tools.py` | `experiment.py` | `experiment_proportion(control_success, control_n, variant_success, variant_n)` |
| `psi_tools.py` | `psi.py` | `pagespeed_insights(url)` |
| `fediverse_tools.py` | `fediverse.py` | `mastodon_trends(instance)`, `mastodon_tag(instance, tag)`, `lemmy_search(query)` |
| `discourse_tools.py` | `discourse.py` | `discourse_latest(base_url)`, `discourse_topic(base_url, topic_id)`, `discourse_health(base_url)` |

Each module:
1. Imports `tool`, `subprocess`, `json`, `logger`
2. Defines `_CONNECTOR_SCRIPT` pointing to the corresponding `.py` in `marketing-skills/scripts/connectors/`
3. Defines `_run_connector(args)` helper (identical to youtube_tools pattern)
4. Exports `@tool`-decorated functions that call `_run_connector([...])` with the right CLI args
5. Returns `{"error": "..."}` on failure, never raises

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_connector_tools.py -v`
Expected: PASS (all 20 tests)

**Step 5: Commit**

```bash
git add tools/connectors/ tests/test_connector_tools.py
git commit -m "feat(tools): add 17 connector tool modules wrapping marketing-skills scripts"
```

---

### Task 4: Scout Phase Agents (4 agents + 4 prompts + 4 tests)

**Files:**
- Create: `agents/scout/__init__.py` (empty)
- Create: `agents/scout/audience_mapper.py`
- Create: `agents/scout/trend_spotter.py`
- Create: `agents/scout/influencer_discovery.py`
- Create: `agents/scout/fit_scorer.py`
- Create: `prompts/audience_mapper_prompt.txt`
- Create: `prompts/trend_spotter_prompt.txt`
- Create: `prompts/influencer_discovery_prompt.txt` (enriches existing `prompts/discovery_prompt.txt`)
- Create: `prompts/fit_scorer_prompt.txt`
- Create: `tests/test_audience_mapper.py`
- Create: `tests/test_trend_spotter.py`
- Create: `tests/test_influencer_discovery.py`
- Create: `tests/test_fit_scorer.py`

**Step 1: Write the failing tests**

Each agent test follows this pattern. Here's `test_audience_mapper.py`:

```python
# tests/test_audience_mapper.py
"""Tests for the Audience Mapper agent (Scout phase)."""

from unittest.mock import MagicMock, patch

import pytest


class TestAudienceMapperAgent:
    def test_factory_returns_agent(self, mocker):
        mocker.patch("agents.scout.audience_mapper.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.scout.audience_mapper.Agent", side_effect=lambda **kw: type("Agent", (), kw)())
        from agents.scout.audience_mapper import get_audience_mapper_agent
        agent = get_audience_mapper_agent()
        assert agent is not None
        assert hasattr(agent, "role")
        assert hasattr(agent, "goal")
        assert hasattr(agent, "tools")
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_factory_uses_scout_audience_model(self, mocker):
        mock_llm = MagicMock()
        mocker.patch("agents.scout.audience_mapper.get_fireworks_llm", return_value=mock_llm)
        mocker.patch("agents.scout.audience_mapper.Agent", side_effect=lambda **kw: type("Agent", (), kw)())
        mocker.patch("agents.scout.audience_mapper.MODEL_SCOUT_AUDIENCE", "accounts/fireworks/test-model")
        from agents.scout.audience_mapper import get_audience_mapper_agent
        get_audience_mapper_agent()
        mock_llm.assert_called_once_with("accounts/fireworks/test-model")

    def test_task_has_expected_output(self, mocker):
        mocker.patch("agents.scout.audience_mapper.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.scout.audience_mapper.Agent", side_effect=lambda **kw: type("Agent", (), kw)())
        mocker.patch("agents.scout.audience_mapper.Task", side_effect=lambda **kw: type("Task", (), kw)())
        from agents.scout.audience_mapper import get_audience_mapper_agent, get_audience_mapper_task
        agent = get_audience_mapper_agent()
        task = get_audience_mapper_task("test brief", agent)
        assert hasattr(task, "expected_output")
        assert isinstance(task.expected_output, str)
        assert len(task.expected_output) > 10
```

Write equivalent tests for `test_trend_spotter.py`, `test_influencer_discovery.py`, `test_fit_scorer.py` — same 3 test classes each, substituting the agent name and model var.

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_audience_mapper.py tests/test_trend_spotter.py tests/test_influencer_discovery.py tests/test_fit_scorer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agents.scout'`

**Step 3: Write the prompt files**

Each prompt file is distilled from the corresponding SKILL.md. Format:

```
## Role
[Role name from SKILL.md displayName, e.g. "Audience Mapper · Target Audience Profiler"]

## Goal
[One paragraph from SKILL.md summary + description, focused on what this agent does]

## Backstory
[2-3 paragraphs from SKILL.md Instructions + Skill Contract, describing the procedure the agent follows, the data sources it reads, the outputs it produces, and the boundaries (what adjacent skills own)]
```

For `influencer_discovery_prompt.txt`, enrich the existing `discovery_prompt.txt` with the marketing-skills' screening steps, tiered shortlist format, and registry proposal behavior.

For `fit_scorer_prompt.txt`, incorporate the STAR Suitability scoring rubric from `references/star-benchmark.md`.

**Step 4: Write the agent files**

Each agent file follows the `agents/discovery.py` pattern. Here's `audience_mapper.py`:

```python
# agents/scout/audience_mapper.py
"""Audience Mapper agent — profiles target audience and micro-community (Scout phase).

Read-only: uses scraper tools and connector tools. Does NOT write to AGENTS_DB.
"""

from functools import wraps
from pathlib import Path

from config import MODEL_SCOUT_AUDIENCE
from llm_client import get_fireworks_llm
from tools.scraper_tools import query_creators
from tools.connectors.tavily_tools import tavily_search
from tools.connectors.pageviews_tools import wikipedia_pageviews

try:
    from crewai import Agent, Task
except ImportError:
    class Agent:  # type: ignore[no_redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    class Task:  # type: ignore[no_redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

try:
    from crewai.tools import tool
except ImportError:
    def tool(fn):  # type: ignore[misc]
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper.name = fn.__name__
        return wrapper

_PROMPT_SECTIONS = ("Role", "Goal", "Backstory")


def _parse_prompt_sections(text: str) -> dict:
    sections = {name: "" for name in _PROMPT_SECTIONS}
    current = None
    lines = []
    for line in text.splitlines():
        header = line.strip().removeprefix("## ").removeprefix("# ")
        if header in _PROMPT_SECTIONS:
            if current is not None:
                sections[current] = "\n".join(lines).strip()
                lines = []
            current = header
        elif current is not None:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines).strip()
    return sections


def _load_audience_mapper_prompt() -> dict:
    path = Path(__file__).resolve().parent.parent.parent / "prompts" / "audience_mapper_prompt.txt"
    text = path.read_text(encoding="utf-8")
    return _parse_prompt_sections(text)


def get_audience_mapper_agent() -> Agent:
    """Return a CrewAI Agent for profiling target audience and micro-community."""
    prompt = _load_audience_mapper_prompt()
    return Agent(
        role=prompt.get("Role") or "Audience Mapper · Target Audience Profiler",
        goal=prompt.get("Goal") or "Profile the target audience and map its subculture before partnering with creators.",
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_SCOUT_AUDIENCE),
        tools=[query_creators, tavily_search, wikipedia_pageviews],
        verbose=True,
        allow_delegation=False,
    )


def get_audience_mapper_task(brief_text: str, agent: Agent) -> Task:
    """Return a CrewAI Task that produces an audience profile as JSON."""
    return Task(
        description=(
            f"Brand brief:\n{brief_text}\n\n"
            "Analyze the brief to profile the target audience: demographics, "
            "interests, micro-community, cultural context, and platform preferences."
        ),
        expected_output=(
            "A valid JSON object with keys:\n"
            "- audience_profile: string — demographics, interests, values\n"
            "- micro_community: string — subculture or niche community name\n"
            "- platform_preferences: array — preferred platforms (instagram, youtube, tiktok, etc.)\n"
            "- cultural_context: string — regional/cultural notes for outreach\n"
            "- recommended_niche_filters: object — suggested filters for creator discovery\n"
            "Return only valid JSON, no commentary."
        ),
        agent=agent,
    )
```

Write the other 3 scout agents following the same pattern:
- `trend_spotter.py` — tools: `tavily_search`, `wikipedia_pageviews`, `gdelt_news_mentions`; model: `MODEL_SCOUT_TREND`
- `influencer_discovery.py` — tools: `query_creators`, `get_creator_details`, `youtube_channel_stats`, `bluesky_profile`, `tavily_search`, `registry_get`, `registry_propose`; model: `MODEL_SCOUT_DISCOVERY`
- `fit_scorer.py` — tools: `calculate_fit_score` (wrapped @tool like existing `discovery.py`), `registry_get`; model: `MODEL_SCOUT_FIT`

**Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_audience_mapper.py tests/test_trend_spotter.py tests/test_influencer_discovery.py tests/test_fit_scorer.py -v`
Expected: PASS (12 tests)

**Step 6: Run existing tests to verify no regressions**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All existing 117 tests still pass (new agents are additive)

**Step 7: Commit**

```bash
git add agents/scout/ prompts/*scout* tests/test_audience_mapper.py tests/test_trend_spotter.py tests/test_influencer_discovery.py tests/test_fit_scorer.py
git commit -m "feat(agents): add 4 Scout phase agents with enriched marketing-skills prompts"
```

---

### Task 5: Target Phase Agents (4 agents + 4 prompts + 4 tests)

**Files:**
- Create: `agents/target/__init__.py` (empty)
- Create: `agents/target/competitor_tracker.py`
- Create: `agents/target/campaign_planner.py`
- Create: `agents/target/brief_generator.py`
- Create: `agents/target/budget_optimizer.py`
- Create: `prompts/competitor_tracker_prompt.txt`
- Create: `prompts/campaign_planner_prompt.txt`
- Create: `prompts/brief_generator_prompt.txt`
- Create: `prompts/budget_optimizer_prompt.txt`
- Create: `tests/test_competitor_tracker.py`
- Create: `tests/test_campaign_planner.py`
- Create: `tests/test_brief_generator.py`
- Create: `tests/test_budget_optimizer.py`

**Pattern:** Identical to Task 4. Write 4 tests (same 3-class pattern each), 4 prompt files (distilled from `marketing-skills/influencer/target/*/SKILL.md`), 4 agent files.

Tool assignments:
- `competitor_tracker.py` — `gdelt_news_mentions`, `youtube_channel_stats`, `tavily_search`, `hn_search`; model: `MODEL_TARGET_COMPETITOR`
- `campaign_planner.py` — `query_creators`, `tavily_search`, `registry_get`; model: `MODEL_TARGET_PLANNER`
- `brief_generator.py` — `registry_get` (narrative canon), `query_creators`; model: `MODEL_TARGET_BRIEF`
- `budget_optimizer.py` — `calculate_fit_score` (wrapped), `registry_get`; model: `MODEL_TARGET_BUDGET`

**Commit:**
```bash
git add agents/target/ prompts/*target* tests/test_competitor_tracker.py tests/test_campaign_planner.py tests/test_brief_generator.py tests/test_budget_optimizer.py
git commit -m "feat(agents): add 4 Target phase agents with enriched marketing-skills prompts"
```

---

### Task 6: Activate Phase Agents (4 agents + 4 prompts + 4 tests)

**Files:**
- Create: `agents/activate/__init__.py` (empty)
- Create: `agents/activate/outreach_manager.py`
- Create: `agents/activate/creator_content_auditor.py`
- Create: `agents/activate/contract_helper.py`
- Create: `agents/activate/content_amplifier.py`
- Create: `prompts/outreach_manager_prompt.txt`
- Create: `prompts/creator_content_auditor_prompt.txt`
- Create: `prompts/contract_helper_prompt.txt`
- Create: `prompts/content_amplifier_prompt.txt`
- Create: `tests/test_outreach_manager.py`
- Create: `tests/test_creator_content_auditor.py`
- Create: `tests/test_contract_helper.py`
- Create: `tests/test_content_amplifier.py`

**Pattern:** Identical to Task 4. The `outreach_manager.py` agent is the enriched version of the existing `agents/outreach.py` — it incorporates the marketing-skills outreach-manager playbook (personalization points, multi-touch follow-up cadence, negotiation scripts, pipeline tracking) plus the existing Instagram DM plumbing + consent registry check.

Tool assignments:
- `outreach_manager.py` — `send_instagram_dm`, `get_creator_language`, `save_conversation`, `log_dm`, `check_dm_quota`, `registry_get` (consent check before send), `registry_propose` (closed-cycle rates); model: `MODEL_ACTIVATE_OUTREACH`
- `creator_content_auditor.py` — `registry_get` (claims/narrative), `tavily_extract` (content URL); model: `MODEL_ACTIVATE_AUDITOR`. This is the STAR gate — output includes SHIP/FIX/BLOCK verdict.
- `contract_helper.py` — `get_conversation_details`, `get_brand_brief`, `save_contract`, `registry_get` (creator rates/rights); model: `MODEL_ACTIVATE_CONTRACT`
- `content_amplifier.py` — `tavily_search`, `firecrawl_scrape`; model: `MODEL_ACTIVATE_AMPLIFIER`

The `outreach_manager.py` must support a `send: bool` parameter like the existing `outreach.py`, and must check `registry_get("consent", creator_id)` before sending any DM — if suppressed, skip and log.

**Commit:**
```bash
git add agents/activate/ prompts/*activate* tests/test_outreach_manager.py tests/test_creator_content_auditor.py tests/test_contract_helper.py tests/test_content_amplifier.py
git commit -m "feat(agents): add 4 Activate phase agents with enriched marketing-skills prompts"
```

---

### Task 7: Report Phase Agents (4 agents + 4 prompts + 4 tests)

**Files:**
- Create: `agents/report/__init__.py` (empty)
- Create: `agents/report/landing_optimizer.py`
- Create: `agents/report/performance_analyzer.py`
- Create: `agents/report/roi_calculator.py`
- Create: `agents/report/report_generator.py`
- Create: `prompts/landing_optimizer_prompt.txt`
- Create: `prompts/performance_analyzer_prompt.txt`
- Create: `prompts/roi_calculator_prompt.txt`
- Create: `prompts/report_generator_prompt.txt`
- Create: `tests/test_landing_optimizer.py`
- Create: `tests/test_performance_analyzer.py`
- Create: `tests/test_roi_calculator.py`
- Create: `tests/test_report_generator.py`

**Pattern:** Identical to Task 4. Distill prompts from `marketing-skills/influencer/report/*/SKILL.md`.

Tool assignments:
- `landing_optimizer.py` — `firecrawl_scrape`, `pagespeed_insights`, `tavily_extract`; model: `MODEL_REPORT_LANDING`
- `performance_analyzer.py` — `registry_get` (creator baselines), `tavily_search` (sentiment); model: `MODEL_REPORT_PERFORMANCE`
- `roi_calculator.py` — `registry_get` (creator rates), `experiment_proportion` (attribution); model: `MODEL_REPORT_ROI`
- `report_generator.py` — `registry_get` (all registries for summary), `ledger_diff`; model: `MODEL_REPORT_GENERATOR`

**Commit:**
```bash
git add agents/report/ prompts/*report* tests/test_landing_optimizer.py tests/test_performance_analyzer.py tests/test_roi_calculator.py tests/test_report_generator.py
git commit -m "feat(agents): add 4 Report phase agents with enriched marketing-skills prompts"
```

---

### Task 8: Protocol Phase Agents (8 agents + 8 prompts + 8 tests)

**Files:**
- Create: `agents/protocol/__init__.py` (empty)
- Create: `agents/protocol/entity_registry.py`
- Create: `agents/protocol/creator_registry.py`
- Create: `agents/protocol/offer_claims_registry.py`
- Create: `agents/protocol/consent_registry.py`
- Create: `agents/protocol/launch_registry.py`
- Create: `agents/protocol/channel_registry.py`
- Create: `agents/protocol/narrative_registry.py`
- Create: `agents/protocol/memory_management.py`
- Create: `prompts/entity_registry_prompt.txt`
- Create: `prompts/creator_registry_prompt.txt`
- Create: `prompts/offer_claims_registry_prompt.txt`
- Create: `prompts/consent_registry_prompt.txt`
- Create: `prompts/launch_registry_prompt.txt`
- Create: `prompts/channel_registry_prompt.txt`
- Create: `prompts/narrative_registry_prompt.txt`
- Create: `prompts/memory_management_prompt.txt`
- Create: `tests/test_entity_registry.py`
- Create: `tests/test_creator_registry.py`
- Create: `tests/test_offer_claims_registry.py`
- Create: `tests/test_consent_registry.py`
- Create: `tests/test_launch_registry.py`
- Create: `tests/test_channel_registry.py`
- Create: `tests/test_narrative_registry.py`
- Create: `tests/test_memory_management.py`

**Pattern:** Identical to Task 4 but all 8 agents use `MODEL_PROTOCOL_REGISTRY` and tools: `registry_get`, `registry_propose`, `registry_verify`. Distill prompts from `marketing-skills/protocol/*/SKILL.md`.

Key differences from STAR agents:
- Protocol agents are **utility agents** — they don't have `get_*_task()` functions (they're called inline by STAR agents or via a separate `registry_cli.py`)
- Each protocol agent's prompt emphasizes the registry event protocol, the owner-append capability model, and the consent safety path (for `consent_registry.py`)
- `consent_registry.py` is safety-critical — its prompt must emphasize the deny-only suppression path and the data-subject erasure authority requirements

**Commit:**
```bash
git add agents/protocol/ prompts/*protocol* prompts/*registry* prompts/memory_management* tests/test_*_registry.py tests/test_memory_management.py
git commit -m "feat(agents): add 8 Protocol registry agents with NDJSON event protocol prompts"
```

---

### Task 9: Thin Shims for Backward Compatibility

**Files:**
- Modify: `agents/discovery.py` (replace with shim re-exporting from `agents/scout/influencer_discovery.py`)
- Modify: `agents/proposal.py` (replace with shim re-exporting from `agents/target/campaign_planner.py`)
- Modify: `agents/outreach.py` (replace with shim re-exporting from `agents/activate/outreach_manager.py`)
- Modify: `agents/negotiator.py` (replace with shim re-exporting from `agents/activate/outreach_manager.py`)
- Modify: `agents/contract.py` (replace with shim re-exporting from `agents/activate/contract_helper.py`)
- Create: `tests/test_shim_compat.py`

**Step 1: Write the failing test**

```python
# tests/test_shim_compat.py
"""Tests that old agent imports still work through thin shims."""


def test_discovery_shim_exports():
    from agents.discovery import get_discovery_agent, get_discovery_task
    assert callable(get_discovery_agent)
    assert callable(get_discovery_task)


def test_proposal_shim_exports():
    from agents.proposal import get_proposal_agent, get_proposal_task
    assert callable(get_proposal_agent)
    assert callable(get_proposal_task)


def test_outreach_shim_exports():
    from agents.outreach import get_outreach_agent, get_outreach_task
    assert callable(get_outreach_agent)
    assert callable(get_outreach_task)


def test_negotiator_shim_exports():
    from agents.negotiator import get_negotiator_agent
    assert callable(get_negotiator_agent)


def test_contract_shim_exports():
    from agents.contract import get_contract_agent
    assert callable(get_contract_agent)
```

**Step 2: Run test to verify it fails (or passes — existing code already exports these)**

Run: `python -m pytest tests/test_shim_compat.py -v`
Expected: PASS (existing code already exports these functions — the test verifies the shim preserves them after modification)

**Step 3: Replace each existing agent file with a thin shim**

```python
# agents/discovery.py
"""Thin shim — re-exports from agents.scout.influencer_discovery for backward compat.

The enriched Discovery agent now lives at agents/scout/influencer_discovery.py.
This file preserves the existing import path: from agents.discovery import get_discovery_agent.
"""

from agents.scout.influencer_discovery import (
    get_influencer_discovery_agent as get_discovery_agent,
    get_influencer_discovery_task as get_discovery_task,
)

__all__ = ["get_discovery_agent", "get_discovery_task"]
```

```python
# agents/proposal.py
"""Thin shim — re-exports from agents.target.campaign_planner for backward compat."""

from agents.target.campaign_planner import (
    get_campaign_planner_agent as get_proposal_agent,
    get_campaign_planner_task as get_proposal_task,
)

__all__ = ["get_proposal_agent", "get_proposal_task"]
```

```python
# agents/outreach.py
"""Thin shim — re-exports from agents.activate.outreach_manager for backward compat."""

from agents.activate.outreach_manager import (
    get_outreach_manager_agent as get_outreach_agent,
    get_outreach_manager_task as get_outreach_task,
)

__all__ = ["get_outreach_agent", "get_outreach_task"]
```

```python
# agents/negotiator.py
"""Thin shim — re-exports from agents.activate.outreach_manager for backward compat.

The Negotiator role is the outreach_manager agent in negotiation mode.
"""

from agents.activate.outreach_manager import get_outreach_manager_agent as get_negotiator_agent

__all__ = ["get_negotiator_agent"]
```

```python
# agents/contract.py
"""Thin shim — re-exports from agents.activate.contract_helper for backward compat."""

from agents.activate.contract_helper import get_contract_helper_agent as get_contract_agent

__all__ = ["get_contract_agent"]
```

**Note:** The shim function signatures must match the old ones. If `get_outreach_manager_agent(send=False)` doesn't match `get_outreach_agent(send=False)`, adjust the wrapper. Same for `get_discovery_task(brief_text, agent)` vs `get_influencer_discovery_task(brief_text, agent)`.

**Step 4: Run shim tests + all existing tests**

Run: `python -m pytest tests/test_shim_compat.py tests/test_discovery.py tests/test_proposal.py tests/test_outreach.py tests/test_negotiator.py tests/test_contract.py tests/test_crew.py -v`
Expected: PASS — existing tests that import from `agents.discovery` etc. still work through the shims

**Step 5: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests pass (117 existing + new)

**Step 6: Commit**

```bash
git add agents/discovery.py agents/proposal.py agents/outreach.py agents/negotiator.py agents/contract.py tests/test_shim_compat.py
git commit -m "refactor(agents): replace 5 existing agents with thin shims re-exporting from STAR phases"
```

---

### Task 10: StarCrew Orchestration (`crew.py` upgrade)

**Files:**
- Modify: `crew.py` (add `StarCrew` class with phase sub-crews, keep `InfluencerCampaignCrew` as alias)
- Test: `tests/test_star_crew.py`

**Step 1: Write the failing test**

```python
# tests/test_star_crew.py
"""Tests for StarCrew phase routing and orchestration."""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestStarCrewPhaseRouting:
    def test_scout_phase_runs_4_agents(self, mocker):
        """Scout phase should build a crew with 4 scout agents."""
        mocker.patch("crew.Crew", side_effect=lambda **kw: type("Crew", (), {**kw, "kickoff": lambda self: MagicMock(raw="[]", token_usage={})})())
        mocker.patch("crew.Process", sequential="sequential")
        from crew import StarCrew
        crew = StarCrew()
        result = crew.run_phase("scout", brief_text="test brief")
        assert "phase" in result
        assert result["phase"] == "scout"

    def test_invalid_phase_raises(self):
        from crew import StarCrew
        crew = StarCrew()
        with pytest.raises(ValueError):
            crew.run_phase("invalid_phase", brief_text="test")

    def test_all_phases_callable(self, mocker):
        mocker.patch("crew.Crew", side_effect=lambda **kw: type("Crew", (), {**kw, "kickoff": lambda self: MagicMock(raw="[]", token_usage={})})())
        mocker.patch("crew.Process", sequential="sequential")
        from crew import StarCrew
        crew = StarCrew()
        for phase in ["scout", "target", "activate", "report"]:
            result = crew.run_phase(phase, brief_text="test")
            assert result["phase"] == phase


class TestStarCrewBackwardCompat:
    def test_influencer_campaign_crew_still_exists(self):
        from crew import InfluencerCampaignCrew
        assert InfluencerCampaignCrew is not None

    def test_kickoff_still_works(self, mocker):
        mocker.patch("crew.Crew", side_effect=lambda **kw: type("Crew", (), {**kw, "kickoff": lambda self: MagicMock(raw="[]", token_usage={})})())
        mocker.patch("crew.Process", sequential="sequential")
        from crew import InfluencerCampaignCrew
        crew = InfluencerCampaignCrew()
        summary = crew.kickoff(brief_text="test", send=False, approve_each=False, max_creators=5)
        assert "brief_id" in summary
        assert "dry_run" in summary
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_star_crew.py -v`
Expected: FAIL with `ImportError: cannot import name 'StarCrew' from 'crew'`

**Step 3: Write the implementation**

Add `StarCrew` class to `crew.py` (keep existing `InfluencerCampaignCrew` class for backward compat). The `StarCrew` class:

```python
class StarCrew:
    """Orchestrates the 24-agent STAR pipeline with phase routing.

    Phases: scout → target → activate → report.
    Protocol agents are utility agents called within phases, not pipeline stages.
    """

    PHASES = ("scout", "target", "activate", "report")

    def __init__(self):
        self._db: Optional[Database] = None
        self._total_tokens: int = 0
        self._phase_results: dict[str, dict] = {}

    def _get_db(self) -> Database:
        if self._db is None:
            self._db = Database(AGENTS_DB_PATH)
            self._db.init_db()
        return self._db

    def _track_tokens(self, usage: dict) -> None:
        added = usage.get("total_tokens", 0) if isinstance(usage, dict) else 0
        self._total_tokens += added
        if self._total_tokens > MAX_TOTAL_TOKENS_PER_RUN:
            logger.warning("Token budget exceeded: %d / %d", self._total_tokens, MAX_TOTAL_TOKENS_PER_RUN)

    @staticmethod
    def _safe_json_parse(text: str) -> list:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        return []

    def run_phase(self, phase: str, brief_text: str, **kwargs) -> dict:
        """Run a single STAR phase. Returns a phase result dict."""
        if phase not in self.PHASES:
            raise ValueError(f"Invalid phase '{phase}'. Must be one of: {self.PHASES}")

        db = self._get_db()
        self._total_tokens = 0

        # Insert brief if this is the first phase
        brief_id = kwargs.get("brief_id")
        if brief_id is None:
            try:
                brief_id = db.insert_brief(raw_brief=brief_text)
            except Exception as exc:
                logger.error("Failed to insert brand brief: %s", exc)
                brief_id = None

        phase_method = getattr(self, f"_run_{phase}_phase")
        result = phase_method(brief_text, brief_id, **kwargs)
        result["phase"] = phase
        result["brief_id"] = brief_id
        result["total_tokens"] = self._total_tokens
        self._phase_results[phase] = result
        return result

    def run_all(self, brief_text: str, send: bool = False, approve_each: bool = False, max_creators: int = 10) -> dict:
        """Run all 4 STAR phases sequentially. Returns a combined summary."""
        db = self._get_db()
        self._total_tokens = 0
        self._phase_results = {}

        try:
            brief_id = db.insert_brief(raw_brief=brief_text)
        except Exception as exc:
            logger.error("Failed to insert brand brief: %s", exc)
            brief_id = None

        scout_result = self._run_scout_phase(brief_text, brief_id)
        target_result = self._run_target_phase(brief_text, brief_id, scout_result=scout_result)
        activate_result = self._run_activate_phase(brief_text, brief_id, target_result=target_result, send=send, approve_each=approve_each)
        report_result = self._run_report_phase(brief_text, brief_id, activate_result=activate_result)

        return {
            "brief_id": brief_id,
            "scout": scout_result,
            "target": target_result,
            "activate": activate_result,
            "report": report_result,
            "total_tokens": self._total_tokens,
            "dry_run": not send,
        }

    def _run_scout_phase(self, brief_text: str, brief_id: Optional[int], **kwargs) -> dict:
        """Run Scout: audience_mapper → trend_spotter → influencer_discovery → fit_scorer."""
        creators_found = 0
        try:
            from agents.scout.audience_mapper import get_audience_mapper_agent, get_audience_mapper_task
            from agents.scout.trend_spotter import get_trend_spotter_agent, get_trend_spotter_task
            from agents.scout.influencer_discovery import get_influencer_discovery_agent, get_influencer_discovery_task
            from agents.scout.fit_scorer import get_fit_scorer_agent, get_fit_scorer_task

            # Run each scout agent sequentially
            for get_agent, get_task, name in [
                (get_audience_mapper_agent, get_audience_mapper_task, "audience_mapper"),
                (get_trend_spotter_agent, get_trend_spotter_task, "trend_spotter"),
                (get_influencer_discovery_agent, get_influencer_discovery_task, "influencer_discovery"),
                (get_fit_scorer_agent, get_fit_scorer_task, "fit_scorer"),
            ]:
                agent = get_agent()
                task = get_task(brief_text, agent)
                self.crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
                result = self.crew.kickoff()
                self._track_tokens(getattr(result, "token_usage", {}) or {})
                if name == "influencer_discovery":
                    ranked = self._safe_json_parse(getattr(result, "raw", "[]"))
                    creators_found = len(ranked)
                    self._phase_results["scout_creators"] = ranked

        except Exception as exc:
            logger.error("Scout phase failed: %s", exc)

        return {"creators_found": creators_found}

    def _run_target_phase(self, brief_text: str, brief_id: Optional[int], **kwargs) -> dict:
        """Run Target: competitor_tracker → campaign_planner → brief_generator → budget_optimizer."""
        # Similar pattern to _run_scout_phase
        # ... (follows same try/except + sequential crew pattern)
        return {"proposals_generated": 0}

    def _run_activate_phase(self, brief_text: str, brief_id: Optional[int], **kwargs) -> dict:
        """Run Activate: outreach_manager → creator_content_auditor → contract_helper → content_amplifier."""
        send = kwargs.get("send", False)
        # Similar pattern, with send flag passed to outreach_manager
        return {"dms_sent": 0, "dry_run": not send}

    def _run_report_phase(self, brief_text: str, brief_id: Optional[int], **kwargs) -> dict:
        """Run Report: landing_optimizer → performance_analyzer → roi_calculator → report_generator."""
        # Similar pattern
        return {"report_generated": False}


# Backward compat: InfluencerCampaignCrew delegates to StarCrew
class InfluencerCampaignCrew(StarCrew):
    """Backward-compatible alias. kickoff() runs all phases like the old pipeline."""

    def kickoff(self, brief_text: str, send: bool = False, approve_each: bool = False, max_creators: int = 10) -> dict:
        """Run the full STAR pipeline (backward compat with old crew.py)."""
        result = self.run_all(brief_text, send=send, approve_each=approve_each, max_creators=max_creators)
        # Flatten to old summary shape for backward compat
        scout = result.get("scout", {})
        activate = result.get("activate", {})
        return {
            "brief_id": result.get("brief_id"),
            "creators_found": scout.get("creators_found", 0),
            "suggestions_saved": scout.get("suggestions_saved", 0),
            "dms_attempted": activate.get("dms_attempted", 0),
            "dms_sent": activate.get("dms_sent", 0),
            "dry_run": result.get("dry_run", True),
            "total_tokens": result.get("total_tokens", 0),
        }
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_star_crew.py -v`
Expected: PASS (5 tests)

**Step 5: Run existing crew tests**

Run: `python -m pytest tests/test_crew.py -v`
Expected: PASS (backward compat maintained)

**Step 6: Commit**

```bash
git add crew.py tests/test_star_crew.py
git commit -m "feat(crew): add StarCrew with phase routing + backward-compat InfluencerCampaignCrew"
```

---

### Task 11: main.py Phase Routing

**Files:**
- Modify: `main.py` (add `--phase` argument, route to StarCrew)
- Test: `tests/test_main_star.py`

**Step 1: Write the failing test**

```python
# tests/test_main_star.py
"""Tests for main.py --phase argument."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestMainPhaseArg:
    def test_parse_args_has_phase(self):
        from main import parse_args
        args = parse_args(["test brief", "--phase", "scout"])
        assert args.phase == "scout"

    def test_parse_args_default_phase_all(self):
        from main import parse_args
        args = parse_args(["test brief"])
        assert args.phase == "all"

    def test_parse_args_phase_choices(self):
        from main import parse_args
        for p in ["scout", "target", "activate", "report", "all"]:
            args = parse_args(["test brief", "--phase", p])
            assert args.phase == p
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main_star.py -v`
Expected: FAIL with `AttributeError: Namespace object has no attribute 'phase'`

**Step 3: Add --phase to parse_args and route in main()**

Add to `parse_args()`:
```python
    parser.add_argument(
        "--phase",
        type=str,
        default="all",
        choices=["scout", "target", "activate", "report", "all"],
        help="Run a specific STAR phase (default: all = full pipeline).",
    )
```

Replace the pipeline section in `main()`:
```python
    # ── Pipeline ──────────────────────────────────────────────────────────
    from crew import StarCrew

    crew = StarCrew()

    if args.phase == "all":
        summary = crew.run_all(
            brief_text=args.brief,
            send=args.send,
            approve_each=args.approve_each,
            max_creators=args.max_creators,
        )
    else:
        summary = crew.run_phase(
            args.phase,
            brief_text=args.brief,
            send=args.send,
            approve_each=args.approve_each,
            max_creators=args.max_creators,
        )
```

**Step 4: Run tests to verify**

Run: `python -m pytest tests/test_main_star.py tests/test_star_crew.py -v`
Expected: PASS

**Step 5: Run full suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All pass

**Step 6: Commit**

```bash
git add main.py tests/test_main_star.py
git commit -m "feat(cli): add --phase flag to main.py for STAR phase routing"
```

---

### Task 12: check_replies.py Enrichment

**Files:**
- Modify: `check_replies.py` (update imports to use activate agents + add consent registry check)
- Test: `tests/test_check_replies_star.py`

**Step 1: Write the failing test**

```python
# tests/test_check_replies_star.py
"""Tests that check_replies.py uses enriched activate agents."""

from unittest.mock import MagicMock, patch


def test_run_negotiator_imports_from_activate(mocker):
    """Negotiator should now import from agents.activate.outreach_manager."""
    mocker.patch("crew.Crew", side_effect=lambda **kw: type("Crew", (), {**kw, "kickoff": lambda self: MagicMock(raw='{"action":"wait"}', token_usage={})})())
    mocker.patch("crew.Process", sequential="sequential")
    mocker.patch("agents.activate.outreach_manager.get_fireworks_llm", return_value=MagicMock())

    import importlib
    import check_replies
    importlib.reload(check_replies)

    conv = {"id": 1, "creator_username": "test", "status": "outreach_sent", "last_message_count": 0}
    result = check_replies.run_negotiator(conv, dry_run=True)
    assert "action" in result
```

**Step 2: Update check_replies.py imports**

Change:
```python
from agents.negotiator import get_negotiator_agent
```
to:
```python
from agents.activate.outreach_manager import get_outreach_manager_agent as get_negotiator_agent
```

Change:
```python
from agents.contract import get_contract_agent
```
to:
```python
from agents.activate.contract_helper import get_contract_helper_agent as get_contract_agent
```

These work through the shims from Task 9, so the change is transparent — but updating the imports directly is cleaner.

**Step 3: Run tests**

Run: `python -m pytest tests/test_check_replies_star.py tests/test_check_replies.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add check_replies.py tests/test_check_replies_star.py
git commit -m "refactor(check_replies): update imports to use enriched activate agents"
```

---

### Task 13: Final Verification

**Step 1: Run the full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests pass (117 existing + ~85 new = ~202 total)

**Step 2: Verify backward compatibility**

```bash
# Old CLI commands still work
python main.py "Looking for Gujarati food creators with 10k-50k followers for a spice brand campaign, budget 50000 INR"

# New phase commands work
python main.py "same brief" --phase scout
python main.py "same brief" --phase report

# check_replies still works
python check_replies.py --dry-run
```

**Step 3: Verify import paths**

```python
python -c "from agents.discovery import get_discovery_agent; print('shim OK')"
python -c "from agents.scout.influencer_discovery import get_influencer_discovery_agent; print('star OK')"
python -c "from crew import StarCrew, InfluencerCampaignCrew; print('crew OK')"
python -c "from tools.registry_tools import registry_get, registry_propose; print('registry OK')"
python -c "from tools.connectors.youtube_tools import youtube_channel_stats; print('connector OK')"
```

**Step 4: Update AGENTS.md**

Update `AGENTS.md` to document the 24-agent STAR structure, the `--phase` flag, and the new directory layout. Update `agents/AGENTS.md` and `tools/AGENTS.md` similarly.

**Step 5: Final commit**

```bash
git add AGENTS.md agents/AGENTS.md tools/AGENTS.md
git commit -m "docs: update AGENTS.md for 24-agent STAR framework with phase routing"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-07-14-star-agents-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
