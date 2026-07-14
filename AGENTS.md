# PROJECT KNOWLEDGE BASE

**Generated:** 2026-07-14
**Commit:** 286dccd
**Branch:** main

## OVERVIEW

Python CLI CrewAI system using a 24-agent STAR framework to discover Instagram creators from a scraper DB, send Gujarati/Hindi outreach DMs via instagrapi, negotiate rates, and draft ASCI-compliant contracts. The framework consists of 16 execution agents across 4 phases (Scout, Target, Activate, Report) and 8 protocol registry agents. Fireworks AI for LLM, SQLite for state, loguru for logging.

## STRUCTURE

```
vernacular-creator-agents/
├── main.py              # CLI entry — dry-run default, --send for real DMs, --phase for targeted runs
├── check_replies.py     # Scheduled reply processing — Negotiator + Contract
├── crew.py              # StarCrew orchestration (Phased execution: Scout → Target → Activate → Report)
├── config.py            # .env loader — all thresholds, model paths, token budgets
├── database.py          # SQLite CRUD — 5 tables, WAL mode, context-managed connections
├── ig_client.py         # instagrapi singleton — session, jittered delays, rate limiter, serial lock
├── llm_client.py        # Fireworks AI wrapper — OpenAI SDK + CrewAI LLM factory + token tracking
├── agents/              # STAR Framework Agents
│   ├── _base.py         # Shared utilities: Agent/Task stubs, tool decorators, prompt parsing
│   ├── scout/           # Phase 1: Discovery & Filtering
│   ├── target/          # Phase 2: Content Analysis & Strategy
│   ├── activate/        # Phase 3: Personalized Outreach
│   ├── report/          # Phase 4: Campaign Analytics & Summaries
│   └── protocol/        # 8 Protocol Registry Agents for system state and routing
├── tools/               # CrewAI @tool functions
│   ├── connectors/      # 17 specialized connector tool modules
│   └── registry_tools.py # Tools for protocol registry access
├── prompts/             # Plain-text prompt files with output JSON schemas
├── tests/               # 291 pytest tests — all mocked, no real network/LLM
├── db/schema.sql        # CREATE TABLE statements + PRAGMA WAL
├── docs/research.md     # CrewAI, instagrapi, Fireworks, ASCI research notes
└── data/                # Runtime: agents.db, ig_session.json, run.log
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add a new agent | `agents/` + `prompts/` | Follow STAR pattern: add to specific phase folder (`scout/`, `target/`, etc.) |
| Add a new tool | `tools/` | Use `_Tool` class from `scraper_tools.py` — callable + `.run()` + `.name` |
| Change DM rate limits | `.env` → `MAX_DMS_PER_DAY`, `DM_DELAY_SECONDS`, `DM_DELAY_JITTER` | Config loaded in `config.py` |
| Change LLM model | `.env` → `MODEL_DISCOVERY`, `MODEL_PROPOSAL`, etc. | Full Fireworks paths (e.g. `accounts/fireworks/models/glm-5p2`) |
| Debug a failed run | `data/run.log` | Loguru output, rotates at 10 MB, 1 week retention |
| Fix Instagram session | Delete `data/ig_session.json` → re-run with `--send` | Fresh login via `IG_USERNAME`/`IG_PASSWORD` |
| Add a test | `tests/` | pytest + pytest-mock, `:memory:` DB, no real network/LLM |
| Understand DB schema | `db/schema.sql` | 5 tables: brand_briefs, campaign_suggestions, conversations, contracts, dm_log |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `StarCrew` | class | crew.py | Orchestrates STAR Framework; supports `run_phase()` and `run_all()` |
| `Database` | class | database.py | SQLite CRUD for all 5 tables; `:memory:` safe |
| `get_ig_client` | func | ig_client.py | Singleton instagrapi Client with serial lock + rate limiter |
| `get_fireworks_llm` | func | llm_client.py | CrewAI LLM factory for Fireworks (OpenAI-compatible) |
| `format_model_path` | func | llm_client.py | Maps aliases (`glm-5.2`) → full Fireworks paths |
| `_Tool` | class | tools/scraper_tools.py | Callable wrapper: `__call__` + `.run()` + `.name` + `.description` |
| `_base.py` | module | agents/_base.py | Shared utilities: Agent/Task stubs, tool decorators, prompt parsing |
| `get_discovery_agent` | func | agents/discovery.py | Shim for backward compat; delegates to STAR scout agents |
| `get_proposal_agent` | func | agents/proposal.py | Shim for backward compat; delegates to STAR target agents |
| `get_outreach_agent` | func | agents/outreach.py | Shim for backward compat; delegates to STAR activate agents |
| `get_negotiator_agent` | func | agents/negotiator.py | Agent with 8 tools — read threads, send DM, budget, quota |
| `get_contract_agent` | func | agents/contract.py | Agent with conversation details, brand brief, save contract |
| `calculate_fit_score` | func | tools/calculation_tools.py | Weighted 0-100 score: niche + language + region + budget + engagement |
| `send_instagram_dm` | tool | tools/instagram_tools.py | Resolve username → user_id → send DM with error handling |

## CONVENTIONS

- **`_Tool` class, not `@tool`**: `tools/scraper_tools.py` defines a local `_Tool` class instead of importing `crewai.tools.tool`. The crewai decorator returns non-callable `Tool` objects; `_Tool` is both callable AND has `.run()` for CrewAI compatibility. All tool modules use this pattern or `from crewai.tools import tool` with a fallback.
- **Shared Utilities**: `agents/_base.py` provides shared Agent/Task stubs, tool decorators, and prompt parsing utilities used across all STAR agents.
- **Dry-run default**: `main.py` never sends DMs without `--send`. `check_replies.py` never calls Instagram APIs without explicit non-`--dry-run` mode.
- **Loguru everywhere**: No `print()`, no stdlib `logging`. All output via `from loguru import logger`.
- **Model paths in .env**: Full Fireworks paths (e.g. `accounts/fireworks/models/glm-5p2`). Aliases resolved by `format_model_path()`.
- **Token budgets**: `MAX_TOKENS_PER_AGENT=4000` per call, `MAX_TOTAL_TOKENS_PER_RUN=25000` per pipeline run. Exceeding logs warning but does not abort.
- **Randomized delays**: `DM_DELAY_SECONDS ± DM_DELAY_JITTER` (default 5±3 = 2-8s). Never fixed intervals against Instagram.
- **Session file 0600**: `data/ig_session.json` gets `chmod 0o600` after login. Listed in `.gitignore`.

## ANTI-PATTERNS (THIS PROJECT)

- **NO `print()`** — use `logger.info()` / `logger.error()` from loguru
- **NO stdlib `logging`** — use `from loguru import logger` exclusively
- **NO Instagram scraping** — scraper data comes from external repo via `SCRAPER_DB_PATH` or `SCRAPER_API_URL`
- **NO web server, Docker, Celery, MQTT** — CLI only, scheduled polling only
- **NO multi-account rotation** — single instagrapi Client with serial lock
- **NO `as any`, `@ts-ignore`** — not applicable (Python) but equivalent: no bare `except:`
- **NO fixed-interval delays** — always use `random.uniform(DM_DELAY_MIN, DM_DELAY_MAX)`
- **NO hardcoded secrets** — all credentials in `.env`, loaded by `config.py`

## UNIQUE STYLES

- **`_Tool` callable wrapper**: `tools/scraper_tools.py` defines `_Tool` class with `__call__`, `.run()`, `.name`, `.description`. This avoids crewai's non-callable `Tool` objects while maintaining CrewAI compatibility. Other tool modules use `from crewai.tools import tool` with a fallback `_Tool` class.
- **Crew fallback stubs**: `crew.py` defines `Crew`, `Process`, `MockCrewOutput` stubs when crewai isn't installed, allowing module import without the dependency.
- **`format_model_path()` alias mapping**: Friendly names (`glm-5.2`, `qwen3.7-plus`) → full Fireworks paths. Used by `llm_client.py` but `.env.example` uses full paths directly.
- **`set_database()` injection**: `tools/database_tools.py` uses a global `_db` set via `set_database(db)`. Tests must call this before using DB tools. Auto-initializes with `:memory:` if not set.

## COMMANDS

```bash
# Install
pip install -r requirements.txt

# Dry-run campaign (no DMs sent)
python main.py "brief text"

# Live campaign (sends real DMs)
python main.py "brief text" --send

# Per-creator approval
python main.py "brief text" --send --approve-each

# Targeted phase run (choices: scout, target, activate, report, all)
python main.py "brief text" --phase scout

# Check replies (dry-run)
python check_replies.py --dry-run

# Check replies (live)
python check_replies.py

# Run tests
python -m pytest tests/ -v

# Run all tests via runner
python test_agents.py
```

## NOTES

- **CrewAI emoji encoding on Windows**: CrewAI 1.15.2 emits emoji in event bus output. On Windows with `charmap` codec, these cause `'charmap' codec can't encode character` errors. These are cosmetic — the pipeline still works.
- **Fireworks API key required**: Without `FIREWORKS_API_KEY` in `.env`, all LLM calls fail with 401. The crew catches errors and returns empty results, so dry-run still produces a summary with zero counts.
- **Instagram 2FA**: If IG account has 2FA, `instagrapi` may prompt for verification code during login. Check console output.
- **ASCI compliance**: Contract templates include `#ad`/`#sponsored` placeholders and "seek legal counsel" disclaimer. These are templates, not legal documents.
- **`c.crew` before kickoff**: `InfluencerCampaignCrew._crew` is initialized as a placeholder Crew (or mock) in `__init__`. The real Crew is built during `kickoff()`.
- **Agent pipeline**: `main.py` runs Discovery → Proposal → Outreach. `check_replies.py` runs Negotiator → Contract separately. Negotiator and Contract are NOT in the main crew.
- **Dual Agent System**: The project uses the STAR framework for the main pipeline. Thin shims at `agents/discovery.py`, `agents/proposal.py`, and `agents/outreach.py` are maintained for backward compatibility, delegating work to the new phased STAR agents.
