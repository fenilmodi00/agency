# STAR Agents Design — Vernacular Creator Agents v2

**Date:** 2026-07-14
**Status:** Approved (user deferred orchestration decision; Approach C selected by recommendation)
**Branch:** main
**Commit:** 286dccd

## Decision Summary

Five forks were resolved through brainstorming before this design was written:

| Fork | Decision | Rationale |
|---|---|---|
| Integration approach | Enrich the CrewAI agents | Translate marketing-skills playbooks into richer prompts, tools, and new CrewAI agents inside the existing Python framework |
| Agent scope | All 16 influencer + 8 protocol = 24 agents | Full fidelity to the marketing-skills STAR system |
| State layer | Full NDJSON event system | Use the existing `registry-events.py` (1805-line runtime) with 7 append-only event streams |
| Connector tools | Wire all bundled connectors as tools | ~17 new tool modules wrapping `scripts/connectors/` as CrewAI `@tool` functions |
| Orchestration | Approach C: hybrid (upgrade main.py + phase flags) | Backward compatible, one entry point, token-budget-friendly phase routing |

## Architecture

Five-layer model:

1. **STAR Execution Agents (16)** — 4 per phase (scout/target/activate/report), each a CrewAI `Agent` with enriched prompts distilled from the corresponding SKILL.md playbook
2. **Protocol Registry Agents (8)** — utility agents called *within* phases (e.g. Scout calls `creator-registry` to dedupe against roster)
3. **Tools** — existing 5 tool modules + 17 new connector tool modules wrapping `scripts/connectors/` + new `registry_tools.py` wrapping `registry-events.py`
4. **State** — dual: existing SQLite (campaign state) + new NDJSON event streams (registry truth) under `data/memory/`
5. **Orchestration** — `main.py` with `--phase` flag (default `all` = full backward-compatible STAR loop)

```
                          main.py "brief" [--phase scout|target|activate|report|all]
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              --phase all     --phase scout    --phase report
              (default)       (just scout)     (just report)
                    │
                    ▼
            ┌── STAR Crew ──┐
            │               │
     ┌──────┼──────┐  ┌─────┼──────┐
     ▼      ▼      ▼  ▼     ▼      ▼
  SCOUT  TARGET  ACTIVATE  REPORT  PROTOCOL
  (4)    (4)     (4)       (4)     (8 utility)
     │      │        │       │        │
     │      │        │       │        ▼
     │      │        │       │   data/memory/events/*.ndjson
     │      │        │       │   (registry-events.py)
     │      │        │       │
     └──────┴────────┴───────┘
                    │
                    ▼
              SQLite (existing)
              data/agents.db
```

### Backward Compatibility

`python main.py "brief"` still works — it now runs Scout→Target→Activate (enriched) instead of Discovery→Proposal→Outreach. `python check_replies.py` still works — it now runs the enriched outreach-manager (negotiation mode) + contract-helper. Existing 117 tests stay green; new tests cover the new agents/phases.

The 5 existing agent files become **thin shims** that re-export from the new locations, so any code importing `from agents.discovery import get_discovery_agent` keeps working during migration.

## Components — The 24 Agents

### Directory structure

```
agents/
├── scout/
│   ├── __init__.py
│   ├── audience_mapper.py        # Profile target audience + micro-community
│   ├── trend_spotter.py          # Campaign timing, hashtags, sounds, cultural moments
│   ├── influencer_discovery.py   # Multi-platform candidate pool, screening, tiered shortlist
│   └── fit_scorer.py             # Weighted STAR Suitability score (replaces calculate_fit_score)
├── target/
│   ├── __init__.py
│   ├── competitor_tracker.py     # Competitor creators, campaigns, estimated reach/spend
│   ├── campaign_planner.py       # Campaign/program plan, tentpole, always-on
│   ├── brief_generator.py        # Standardized influencer briefs + templates
│   └── budget_optimizer.py       # Allocate spend across tiers/platforms, ROI projection
├── activate/
│   ├── __init__.py
│   ├── outreach_manager.py       # Pitch, follow-up, negotiation, pipeline tracking
│   ├── creator_content_auditor.py # STAR gate: pre-publish SHIP/FIX/BLOCK verdict
│   ├── contract_helper.py        # Draft/review agreements, usage rights, exclusivity
│   └── content_amplifier.py      # Extend creator content with paid spend, repurpose UGC
├── report/
│   ├── __init__.py
│   ├── landing_optimizer.py      # Landing pages for creator/paid traffic
│   ├── performance_analyzer.py   # Evaluate creator results, compare, sentiment
│   ├── roi_calculator.py         # Measure/project ROI, defend budgets
│   └── report_generator.py       # Written stakeholder reports
├── protocol/
│   ├── __init__.py
│   ├── entity_registry.py        # Brand/entity canonical facts
│   ├── creator_registry.py       # Creator roster: identity, rates, rights, exclusivity
│   ├── offer_claims_registry.py  # Claims/offers canonical truth
│   ├── consent_registry.py       # Consent/suppression (safety-critical)
│   ├── launch_registry.py        # Launch lifecycle state
│   ├── channel_registry.py       # Channel state transitions
│   ├── narrative_registry.py     # Narrative canon (L1 strategy)
│   └── memory_management.py      # HOT/WARM/COLD lifecycle, tombstone/erase
├── discovery.py                  # THIN SHIM → re-exports from scout/influencer_discovery.py
├── proposal.py                   # THIN SHIM → re-exports from target/campaign_planner.py
├── outreach.py                   # THIN SHIM → re-exports from activate/outreach_manager.py
├── negotiator.py                 # THIN SHIM → re-exports from activate/outreach_manager.py (negotiation mode)
└── contract.py                   # THIN SHIM → re-exports from activate/contract_helper.py
```

### Agent factory pattern (per file)

Each agent file follows the existing convention — `get_*_agent()` + `get_*_task()` — but enriched:

```python
# agents/scout/influencer_discovery.py
def get_influencer_discovery_agent() -> Agent:
    prompt = _load_prompt("influencer_discovery_prompt.txt")
    return Agent(
        role=prompt["Role"],
        goal=prompt["Goal"],
        backstory=prompt["Backstory"],
        llm=get_fireworks_llm(MODEL_SCOUT_DISCOVERY),
        tools=[query_creators, get_creator_details, youtube_channel_stats,
               bluesky_profile, tavily_search, registry_propose, registry_get],
        verbose=True,
        allow_delegation=False,
    )

def get_influencer_discovery_task(brief_text, agent) -> Task:
    ...
```

### Model config additions (`.env`)

```
# Scout phase
MODEL_SCOUT_AUDIENCE=accounts/fireworks/models/glm-5p2
MODEL_SCOUT_TREND=accounts/fireworks/models/glm-5p2
MODEL_SCOUT_DISCOVERY=accounts/fireworks/models/glm-5p2
MODEL_SCOUT_FIT=accounts/fireworks/models/glm-5p2
# Target phase
MODEL_TARGET_COMPETITOR=accounts/fireworks/models/glm-5p2
MODEL_TARGET_PLANNER=accounts/fireworks/models/glm-5p2
MODEL_TARGET_BRIEF=accounts/fireworks/models/glm-5p2
MODEL_TARGET_BUDGET=accounts/fireworks/models/glm-5p2
# Activate phase
MODEL_ACTIVATE_OUTREACH=accounts/fireworks/models/glm-5p2
MODEL_ACTIVATE_AUDITOR=accounts/fireworks/models/glm-5p2
MODEL_ACTIVATE_CONTRACT=accounts/fireworks/models/glm-5p2
MODEL_ACTIVATE_AMPLIFIER=accounts/fireworks/models/glm-5p2
# Report phase
MODEL_REPORT_LANDING=accounts/fireworks/models/glm-5p2
MODEL_REPORT_PERFORMANCE=accounts/fireworks/models/glm-5p2
MODEL_REPORT_ROI=accounts/fireworks/models/glm-5p2
MODEL_REPORT_GENERATOR=accounts/fireworks/models/glm-5p2
# Protocol phase
MODEL_PROTOCOL_REGISTRY=accounts/fireworks/models/glm-5p2
```

Existing `MODEL_DISCOVERY`, `MODEL_PROPOSAL`, etc. kept as aliases for backward compat.

### Prompt files (`prompts/`)

24 new prompt files, each translated from the corresponding SKILL.md:

```
prompts/
├── audience_mapper_prompt.txt
├── trend_spotter_prompt.txt
├── influencer_discovery_prompt.txt
├── fit_scorer_prompt.txt
├── competitor_tracker_prompt.txt
├── campaign_planner_prompt.txt
├── brief_generator_prompt.txt
├── budget_optimizer_prompt.txt
├── outreach_manager_prompt.txt
├── creator_content_auditor_prompt.txt
├── contract_helper_prompt.txt
├── content_amplifier_prompt.txt
├── landing_optimizer_prompt.txt
├── performance_analyzer_prompt.txt
├── roi_calculator_prompt.txt
├── report_generator_prompt.txt
├── entity_registry_prompt.txt
├── creator_registry_prompt.txt
├── offer_claims_registry_prompt.txt
├── consent_registry_prompt.txt
├── launch_registry_prompt.txt
├── channel_registry_prompt.txt
├── narrative_registry_prompt.txt
├── memory_management_prompt.txt
├── discovery_prompt.txt          # existing — kept for shim
├── proposal_prompt.txt           # existing
├── negotiator_prompt.txt         # existing
└── contract_prompt.txt           # existing
```

Each prompt file follows the existing `## Role / ## Goal / ## Backstory` format. The content is distilled from the SKILL.md playbook (the Skill Contract, Instructions, Data Sources, output schemas). The marketing-skills' rich procedures (screening steps, negotiation scripts, STAR scoring rubric, registry event protocol) become the agent's role/goal/backstory.

## Components — New Tools

### Connector tools (`tools/connectors/`)

One Python module per connector, each exposing a `_Tool`-wrapped function:

```
tools/
├── connectors/
│   ├── __init__.py
│   ├── youtube_tools.py         # youtube.py channel/videos/rss → @tool
│   ├── bluesky_tools.py         # bluesky.py profile/feed/actors → @tool
│   ├── fediverse_tools.py       # fediverse.py trends/tag/account → @tool
│   ├── discourse_tools.py       # discourse.py latest/topic/health → @tool
│   ├── firecrawl_tools.py       # firecrawl.py search/scrape/map → @tool
│   ├── tavily_tools.py          # tavily.py search/extract → @tool
│   ├── gdelt_tools.py           # gdelt.py news mentions → @tool
│   ├── pageviews_tools.py       # pageviews.py Wikipedia attention → @tool
│   ├── hn_tools.py              # hn.py search/rank → @tool
│   ├── rss_tools.py             # rss_monitor.py feed watch → @tool
│   ├── doh_tools.py             # doh.py DNS auth records → @tool
│   ├── wayback_tools.py         # wayback.py history → @tool
│   ├── appstore_tools.py        # appstore.py lookup/charts → @tool
│   ├── kg_tools.py              # kg.py Wikidata reconcile → @tool
│   ├── ledger_tools.py          # ledger.py record/diff → @tool
│   ├── experiment_tools.py      # experiment.py stats → @tool
│   └── psi_tools.py             # psi.py PageSpeed → @tool
├── registry_tools.py            # Wraps registry-events.py: propose, get, verify, project
├── scraper_tools.py             # existing
├── instagram_tools.py           # existing
├── database_tools.py            # existing
├── calculation_tools.py         # existing (fit_scorer agent may wrap this)
└── llm_tools.py                 # existing
```

### Registry tools (`tools/registry_tools.py`)

Three tool functions wrapping `registry-events.py`:

```python
@tool
def registry_propose(registry: str, aggregate_id: str, payload: dict,
                     source: str, actor_id: str) -> dict:
    """Submit an operation:propose event to a registry NDJSON stream."""

@tool
def registry_get(registry: str, aggregate_id: str) -> dict:
    """Read current projected state for an aggregate from a registry."""

@tool
def registry_verify(registry: str) -> dict:
    """Verify a registry's event stream integrity (offset/hash/idempotency)."""
```

These shell out to `python scripts/registry-events.py propose/get/verify` — the existing 1805-line runtime does the real work (hash chains, idempotency, capability checks).

### Memory directory structure

```
data/
├── agents.db                    # existing SQLite
├── ig_session.json              # existing
├── run.log                      # existing
└── memory/                      # NEW — registry state
    ├── events/
    │   ├── entities.ndjson
    │   ├── creators.ndjson
    │   ├── claims.ndjson
    │   ├── consent.ndjson
    │   ├── launches.ndjson
    │   ├── channels.ndjson
    │   └── narrative.ndjson
    ├── projections/
    │   ├── entities.json
    │   ├── creators.json
    │   ├── claims.json
    │   ├── consent.json
    │   ├── launches.json
    │   ├── channels.json
    │   └── narrative.json
    ├── creators/                # human views (regenerated from projections)
    ├── entities/
    ├── claims/
    ├── consent/
    ├── hot-cache.md
    ├── open-loops.md
    ├── decisions.md
    └── archive/
```

Added to `.gitignore` (runtime state, like `ig_session.json`).

## Data Flow

### Full STAR loop (`--phase all` or default)

```
1. SCOUT phase (4 agents, sequential)
   audience_mapper → trend_spotter → influencer_discovery → fit_scorer
   ├─ audience_mapper: reads brief, profiles target audience
   │   └─ writes: data/memory/influencer/audience-mapper/YYYY-MM-DD-*.md
   ├─ trend_spotter: reads niche, identifies timing/themes
   │   └─ writes: data/memory/influencer/trend-spotter/YYYY-MM-DD-*.md
   ├─ influencer_discovery: queries scraper DB + youtube/bluesky connectors
   │   ├─ reads: data/memory/projections/creators.json (dedupe against roster)
   │   ├─ proposes: creators.ndjson (new candidates via registry_propose)
   │   └─ writes: data/memory/influencer/influencer-discovery/YYYY-MM-DD-*.md
   └─ fit_scorer: scores shortlist with STAR Suitability rubric
       ├─ reads: discovery output + calculate_fit_score tool
       └─ writes: data/memory/influencer/fit-scorer/YYYY-MM-DD-*.md

2. TARGET phase (4 agents, sequential)
   competitor_tracker → campaign_planner → brief_generator → budget_optimizer
   ├─ competitor_tracker: maps competitor creators (gdelt, youtube RSS)
   ├─ campaign_planner: builds campaign plan from scored shortlist
   ├─ brief_generator: generates standardized briefs per creator
   │   └─ reads: data/memory/projections/narrative.json (if canon exists)
   └─ budget_optimizer: allocates budget across tiers, projects ROI

3. ACTIVATE phase (4 agents, sequential)
   outreach_manager → creator_content_auditor → contract_helper → content_amplifier
   ├─ outreach_manager: composes + sends DMs (existing IG plumbing)
   │   ├─ reads: data/memory/projections/consent.json (check suppression before send)
   │   ├─ reads: data/memory/projections/creators.json (confirmed contact path)
   │   ├─ sends: Instagram DMs (if --send) or dry-run
   │   └─ proposes: creators.ndjson (closed-cycle rates/outcomes)
   ├─ creator_content_auditor: STAR gate on creator submissions (SHIP/FIX/BLOCK)
   ├─ contract_helper: drafts ASCI-compliant contracts
   └─ content_amplifier: repurpose UGC across paid/web/email

4. REPORT phase (4 agents, sequential)
   landing_optimizer → performance_analyzer → roi_calculator → report_generator
   ├─ landing_optimizer: optimize landing pages for creator traffic
   ├─ performance_analyzer: evaluate creator results, sentiment
   ├─ roi_calculator: measure ROI, defend budgets
   └─ report_generator: written stakeholder report
```

### Protocol agents (called as utilities, not pipeline stages)

Protocol agents don't run in the main pipeline. They're invoked *by* STAR agents when registry state is needed:

- Scout's `influencer_discovery` calls `registry_get("creators", id)` to check the roster, and `registry_propose("creators", ...)` to submit new candidates
- Activate's `outreach_manager` calls `registry_get("consent", id)` to check suppression before sending a DM
- The 8 protocol agents are also independently callable: `python registry_cli.py creators review-pending` to accept/reject proposals

### `check_replies.py` (Activate reply loop, enriched)

```
read IG threads → outreach_manager (negotiation mode) → contract_helper
  ├─ outreach_manager: reads replies, decides action (accept/counter/wait/escalate)
  │   └─ proposes: creators.ndjson (agreed rate), consent.ndjson (if creator opts out)
  └─ contract_helper: generates ASCI-compliant contract when deal accepted
```

### Phase routing in `main.py`

```python
def main():
    brief = args.brief
    phase = args.phase  # default: "all"

    if phase in ("all", "scout"):
        run_scout_phase(brief)
    if phase in ("all", "target"):
        run_target_phase(brief, scout_results)
    if phase in ("all", "activate"):
        run_activate_phase(brief, target_results, send=args.send)
    if phase in ("all", "report"):
        run_report_phase(brief, activate_results)
```

Each `run_*_phase()` builds a sub-Crew with that phase's 4 agents + their tasks, runs it sequentially, and passes results to the next phase.

## Error Handling

**Existing patterns preserved:**
- Every agent wrapped in try/except in the crew — failure logs error, continues to next phase
- `_safe_json_parse()` for agent output — malformed JSON returns `[]`, not crash
- Token budget tracking (`_track_tokens`) — exceeding `MAX_TOTAL_TOKENS_PER_RUN` warns but doesn't abort

**New patterns:**

- **Connector tools fail gracefully:** each connector tool catches `subprocess.CalledProcessError` / `TimeoutExpired` and returns `{"error": "...", "data": None}` — the agent treats it as Unknown (per skill-contract: missing evidence is Unknown, not a crash)
- **Registry proposals are non-blocking:** `registry_propose()` failure logs a warning but the agent continues — proposals are pending anyway, the owner ritual accepts later
- **Phase isolation:** if Scout fails completely, Target/Activate/Report still run with empty scout results (the agent gets an empty shortlist and reports "no candidates found")
- **Consent safety check before every DM:** `outreach_manager` calls `registry_get("consent", creator_id)` before sending — if suppressed, the DM is skipped and logged. This is the safety-critical path from the state model.
- **Connector subprocess timeout:** 30s default, configurable via `CONNECTOR_TIMEOUT_SECONDS` in `.env`
- **NDJSON write safety:** `registry-events.py` already enforces hash chains, idempotency, capability checks, and Git-ignore preflight — the tools just shell out to it

## Testing

**Existing 117 tests stay green.** The 5 thin shims re-export from the new locations, so `from agents.discovery import get_discovery_agent` still works. Tests that mock `get_discovery_agent()` continue to work unchanged.

**New test files:**

```
tests/
├── test_audience_mapper.py          # Agent factory + task output schema
├── test_trend_spotter.py
├── test_influencer_discovery.py     # (enriches existing discovery tests)
├── test_fit_scorer.py
├── test_competitor_tracker.py
├── test_campaign_planner.py
├── test_brief_generator.py
├── test_budget_optimizer.py
├── test_outreach_manager.py         # (enriches existing outreach tests)
├── test_creator_content_auditor.py
├── test_contract_helper.py          # (enriches existing contract tests)
├── test_content_amplifier.py
├── test_landing_optimizer.py
├── test_performance_analyzer.py
├── test_roi_calculator.py
├── test_report_generator.py
├── test_entity_registry.py
├── test_creator_registry.py
├── test_offer_claims_registry.py
├── test_consent_registry.py
├── test_launch_registry.py
├── test_channel_registry.py
├── test_narrative_registry.py
├── test_memory_management.py
├── test_registry_tools.py           # registry_propose/get/verify (mocked subprocess)
├── test_connector_tools.py          # youtube/bluesky/tavily/etc (mocked subprocess)
├── test_star_crew.py                # Phase routing, --phase flag, phase isolation
└── test_shim_compat.py              # Verify old imports still work through shims
```

**Testing conventions (from existing suite):**
- All mocked — no real network, no real LLM, no real Instagram
- `:memory:` SQLite for DB tests
- `pytest-mock` for mocking `subprocess.run` (connector + registry tools)
- Each agent test: verify factory returns `Agent`, task `expected_output` is valid, tool list is correct
- Phase tests: mock all 4 agents in a phase, verify sequential execution and result passing

## File Inventory

| Component | Count | Location |
|---|---|---|
| New agent files | 24 | `agents/{scout,target,activate,report,protocol}/*.py` |
| Thin shims (existing agents) | 5 | `agents/{discovery,proposal,outreach,negotiator,contract}.py` |
| New prompt files | 24 | `prompts/*_prompt.txt` |
| New connector tool modules | 17 | `tools/connectors/*.py` |
| New registry tools module | 1 | `tools/registry_tools.py` |
| New memory directory | 1 | `data/memory/` with events/projections/views |
| Updated `main.py` | 1 | `--phase` flag + phase routing |
| Updated `crew.py` | 1 | `StarCrew` class with phase sub-crews |
| Updated `config.py` | 1 | 19 new model config vars |
| Updated `.env.example` | 1 | New config vars |
| Updated `.gitignore` | 1 | `data/memory/` |
| New test files | 28 | `tests/test_*.py` |
| **Total new/modified files** | ~103 | |

## Constraints

- **No `print()`** — use `logger.info()` / `logger.error()` from loguru
- **No stdlib `logging`** — use `from loguru import logger` exclusively
- **No Instagram scraping** — scraper data comes from external repo via `SCRAPER_DB_PATH` or `SCRAPER_API_URL`
- **No web server, Docker, Celery, MQTT** — CLI only, scheduled polling only
- **No multi-account rotation** — single instagrapi Client with serial lock
- **No `as any`, `@ts-ignore`** — Python equivalent: no bare `except:`
- **No fixed-interval delays** — always use `random.uniform(DM_DELAY_MIN, DM_DELAY_MAX)`
- **No hardcoded secrets** — all credentials in `.env`, loaded by `config.py`
- **Dry-run default** — `main.py` never sends DMs without `--send`
- **Token budgets** — `MAX_TOKENS_PER_AGENT=4000` per call, `MAX_TOTAL_TOKENS_PER_RUN=25000` per pipeline run
- **Registry event protocol** — ordinary skills may only `propose`; only owner-capability principals may `accept`/`reject`/`upsert`/`transition`

## Next Step

Transition to the `writing-plans` skill to create a detailed implementation plan from this design.
