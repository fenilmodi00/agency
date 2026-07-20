# PROJECT KNOWLEDGE BASE

**Generated:** 2026-07-20
**Commit:** 0e225b2
**Branch:** instagrapi-mvp

## OVERVIEW

Monorepo with three components sharing one Instagram/instagrapi core:

1. **Agent pipeline** (root `*.py` + `agents/` + `tools/`) — Python CLI CrewAI system: 24-agent STAR framework (16 execution agents across Scout/Target/Activate/Report + 8 protocol registry agents) that discovers Instagram creators from a scraper DB, sends Gujarati/Hindi outreach DMs via instagrapi, negotiates rates, and drafts ASCI-compliant contracts. Fireworks AI LLM, SQLite state, loguru logging.
2. **`api/`** — FastAPI backend for the creator dashboard MVP: Clerk JWT auth, per-user instagrapi sessions, Appwrite profile sync.
3. **`app/`** — Expo SDK 57 mobile app ("creator-workspace"): expo-router, Tamagui, Clerk + Appwrite + the FastAPI backend.

`marketing-skills/` is a vendored stdlib-only connector library invoked via subprocess from `tools/connectors/`.

## STRUCTURE

```
001/  (repo root = Python package root, no wrapper dir)
├── main.py              # CLI entry — dry-run default, --send for real DMs, --phase scout|target|activate|report|all
├── check_replies.py     # Reply processing — Negotiator + Contract agents
├── run.py               # Autonomous runner — polls check_replies on a fixed interval
├── crew.py              # StarCrew orchestration (4 phases x 4 agents, sequential)
├── config.py            # .env loader — thresholds, model paths, token budgets
├── database.py          # SQLite CRUD — 5 tables, WAL mode
├── ig_client.py         # instagrapi singleton — session, jittered delays, rate limiter, serial lock
├── llm_client.py        # Fireworks AI wrapper — CrewAI LLM factory + OpenAI SDK + token tracking
├── agents/              # STAR framework: _base.py + scout/ target/ activate/ report/ protocol/ + 5 legacy shims
├── tools/               # CrewAI tools: scraper/instagram/database/calculation/registry + connectors/ (17 subprocess wrappers)
├── prompts/             # 25 plain-text prompt files with output JSON schemas
├── tests/               # 343 pytest tests, 43 files — all mocked, no real network/LLM
├── db/schema.sql        # CREATE TABLE + PRAGMA WAL
├── api/                 # FastAPI dashboard backend (Clerk JWT, Appwrite, SessionManager)
├── app/                 # Expo SDK 57 app (expo-router, Tamagui, Clerk, Appwrite) — bun, not npm
├── marketing-skills/    # Vendored connector scripts (stdlib-only) + registry-events.py
└── data/                # Runtime: agents.db, ig session json, run.log
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add a new agent | `agents/<phase>/` + `prompts/` | 4 agents per phase; wire into `crew.py::_run_<phase>_phase` |
| Add a new tool | `tools/` | Use `_Tool` class from `scraper_tools.py` — callable + `.run()` + `.name` |
| Add a connector | `tools/connectors/*_tools.py` wrapping a `marketing-skills` script | Subprocess + JSON stdout; timeout via `CONNECTOR_TIMEOUT_SECONDS` |
| Change DM rate limits | `.env` → `MAX_DMS_PER_DAY`, `DM_DELAY_SECONDS`, `DM_DELAY_JITTER` | Loaded in `config.py` |
| Change LLM model | `.env` → `MODEL_DISCOVERY`, `MODEL_PROPOSAL`, etc. | Full Fireworks paths (e.g. `accounts/fireworks/models/glm-5p2`) |
| Add API route | `api/main.py` | Every route except `/health` requires Clerk JWT via `require_clerk_user_id` |
| Add app screen | `app/src/app/` | expo-router file-based; placeholders in `(tabs)/(messages)`, `(tabs)/(profile)` |
| Debug a failed run | `data/run.log` | Loguru, rotates 10 MB, 1 week retention |
| Fix Instagram session | Delete `data/ig_session.json` → re-run with `--send` | Fresh login via `IG_USERNAME`/`IG_PASSWORD` |
| Add a test | `tests/` | pytest + pytest-mock, `:memory:` DB; app tests: `app/src/__tests__/` (jest-expo) |
| Understand DB schema | `db/schema.sql` | 5 tables: brand_briefs, campaign_suggestions, conversations, contracts, dm_log |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `StarCrew` | class | crew.py:37 | 4-phase orchestrator: `run_all()` = scout→target→activate→report; `run_phase()` for one |
| `Database` | class | database.py | SQLite CRUD for 5 tables; `:memory:` safe |
| `get_ig_client` | func | ig_client.py:53 | Singleton instagrapi wrapper (16 callers) |
| `get_fireworks_llm` | func | llm_client.py:18 | CrewAI LLM factory for Fireworks (40 callers) |
| `format_model_path` | func | llm_client.py:8 | Aliases (`glm-5.2`) → full Fireworks paths |
| `_Tool` | class | tools/scraper_tools.py:12 | Callable wrapper: `__call__` + `.run()` + `.name` + `.description` |
| `set_database` | func | tools/database_tools.py:42 | Global DB injection for tools; tests must call it |
| `calculate_fit_score` | func | tools/calculation_tools.py | Weighted 0-100 score: niche+language+region+budget+engagement |
| `run_negotiator` | func | check_replies.py:141 | Negotiator Crew run; dry-run returns `wait` without LLM |
| `get_session_manager` | func | api/session_manager.py | Per-Clerk-user instagrapi registry, LRU evict at 50 |
| `get_clerk_user_id` | func | api/auth.py | Clerk JWT (HS256) verification for FastAPI deps |
| `get_appwrite_client` | func | api/appwrite_client.py | Appwrite Server SDK singleton — creator profile upserts |

Phase agent order (each sub-agent runs as its own sequential Crew):
scout: audience_mapper → trend_spotter → influencer_discovery → fit_scorer · target: competitor_tracker → campaign_planner → brief_generator → budget_optimizer · activate: outreach_manager → creator_content_auditor → contract_helper → content_amplifier · report: landing_optimizer → performance_analyzer → roi_calculator → report_generator

Legacy shims in `agents/`: discovery→scout.influencer_discovery, proposal→target.campaign_planner, outreach+negotiator→activate.outreach_manager, contract→activate.contract_helper.

## CONVENTIONS

- **`_Tool` class, not `@tool`**: `tools/scraper_tools.py` defines a local `_Tool` — crewai's decorator returns non-callable `Tool` objects; `_Tool` is callable AND has `.run()`. `database_tools.py`/`instagram_tools.py` use `try: from crewai.tools import tool` with a `_Tool` fallback; `agents/_base.py` uses a simpler pass-through decorator fallback.
- **CrewAI stubs everywhere**: `crew.py` (Crew/Process/MockCrewOutput) and `agents/_base.py` (Agent/Task/tool) define stubs on ImportError — every module imports without crewai installed.
- **Dry-run default**: `main.py` never sends DMs without `--send`. `check_replies.py` hits Instagram only without `--dry-run`. Negotiator/Contract run only from `check_replies.py`, never in the main crew.
- **Loguru everywhere**: 28 files use `from loguru import logger`; zero stdlib `logging`; `print()` only in `test_dm.py` and vendored `marketing-skills/`.
- **Model paths in .env**: Full Fireworks paths (e.g. `accounts/fireworks/models/glm-5p2`). Aliases resolved by `format_model_path()`.
- **Token budgets**: `MAX_TOKENS_PER_AGENT=4000`, `MAX_TOTAL_TOKENS_PER_RUN=25000`. Exceeding logs a warning, does not abort.
- **Randomized delays**: `DM_DELAY_SECONDS ± DM_DELAY_JITTER` (default 5±3 → 2-8s) via `random.uniform(DM_DELAY_MIN, DM_DELAY_MAX)`.
- **Session file 0600**: `ig_client.py` does `os.chmod(session_path, 0o600)` after login (no-op on Windows); path is gitignored.

## ANTI-PATTERNS (THIS PROJECT)

- **NO `print()` in pipeline code** — loguru only (`test_dm.py` and `marketing-skills/` CLIs are the sanctioned exceptions)
- **NO stdlib `logging`** — loguru exclusively
- **NO bare `except:`** — always name the exception type
- **NO Instagram scraping** — creator data comes from the external scraper via `SCRAPER_DB_PATH` or `SCRAPER_API_URL`
- **NO fixed-interval delays against Instagram** — always `random.uniform(DM_DELAY_MIN, DM_DELAY_MAX)`. Fixed `time.sleep()` is fine for the `run.py` polling loop.
- **NO second instagrapi Client** — always `get_ig_client()` (pipeline) or `SessionManager` (api/); a second Client breaks the serial lock + rate limiter
- **NO hardcoded secrets** — all credentials in `.env`, loaded by `config.py` / per-package env files
- **NO raw SQL from agent output** — `database_tools` delegates to parameterized queries in `database.py` only
- **NO edits inside `marketing-skills/`** — vendored library; change the `tools/connectors/` wrappers instead
- **NO Docker, Celery, MQTT** — CLI + one FastAPI server (`api/`). The agent pipeline stays CLI; `api/run.py` is the only web entry.

## UNIQUE STYLES

- **`_Tool` callable wrapper**: see CONVENTIONS — the canonical copy lives in `tools/scraper_tools.py`.
- **Crew fallback stubs**: modules stay importable without crewai — tests mock `crew.Crew` with `side_effect` lambdas.
- **`format_model_path()` alias mapping**: friendly names → full Fireworks paths; `.env.example` uses full paths directly.
- **`set_database()` injection**: `tools/database_tools.py` global `_db`; auto-initializes `:memory:` if unset. Tests must call it explicitly.
- **Connector subprocess bridge**: `tools/connectors/*_tools.py` run `marketing-skills/scripts/connectors/*.py` as `subprocess.run(["python", script, ...])` and parse JSON stdout — agents never import connectors directly.
- **Phase result passing**: `StarCrew._phase_results` dict carries `scout_creators`/`target_proposals` between phases; activate falls back to scout when target produced nothing.

## COMMANDS

```bash
# ── Agent pipeline (root venv) ──
pip install -r requirements.txt
python main.py "brief text"                        # dry-run (no DMs)
python main.py "brief text" --send                 # live DMs
python main.py "brief text" --send --approve-each  # confirm each DM
python main.py "brief text" --phase scout          # one phase only
python check_replies.py --dry-run                  # reply check, no IG calls
python check_replies.py                            # live reply processing
python run.py                                      # autonomous polling loop

# ── Tests ──
python -m pytest tests/ -v        # 343 tests
python test_agents.py             # runner script

# ── API backend ──
pip install -r api/requirements.txt
python api/run.py                 # uvicorn on :8000, reload

# ── Mobile app ──
cd app && bun install
bun start        # expo dev server (android/ios/web variants in package.json)
bun test         # jest-expo
bun lint         # tsc --noEmit
```

## NOTES

- **CrewAI emoji on Windows**: CrewAI 1.15.x emits emoji in event-bus output; on `charmap` consoles this raises cosmetic UnicodeEncodeError — the pipeline still completes.
- **Fireworks key required**: without `FIREWORKS_API_KEY`, LLM calls 401; the crew catches and returns empty results, so dry-run still summarizes with zero counts.
- **Instagram 2FA**: instagrapi may prompt for a verification code on fresh login — watch the console.
- **ASCI compliance**: contract templates carry `#ad`/`#sponsored` placeholders + "seek legal counsel" disclaimer. Templates, not legal documents.
- **`InfluencerCampaignCrew(StarCrew)`**: backward-compat subclass whose `kickoff()` flattens the 4-phase result to the old summary shape (creators_found, suggestions_saved, dms_attempted, dms_sent, dry_run, total_tokens).
- **No CI/build config**: no `.github/`, Makefile, pyproject.toml, pytest.ini, or conftest.py anywhere — pytest runs on defaults; fixtures are per-file.
- **Runtime session files**: pipeline default is `data/ig_session.json`; the api/ SessionManager writes per-user files to `data/sessions/{clerk_user_id}.json`.
- **App state**: only the Home (IG connect) screen is built; Messages/Profile are placeholders with hooks ready (`useThreads`, `useMessages`, `useCreatorProfile`, `useDashboard`).

<!-- BEGIN opencode-rag -->
## Code Navigation

ALWAYS use OpenCodeRAG tools before reading or editing:
- **Search first** — `search_semantic(query)` instead of grep/glob
- **Skeleton before read** — `get_file_skeleton(filePath)` then read specific lines
- **Usages before edit** — `find_usages(symbolName)` before modifying any symbol
- **Images via describe** — `describe_image(filePath)` — never read raw bytes

If no results, run `opencode-rag index`.
<!-- END opencode-rag -->
