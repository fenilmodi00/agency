# tools/ — CrewAI Tool Functions

Toolset for the STAR framework: creator DB access, Instagram DM ops, state CRUD, pure calculations, protocol-registry access, and 17 subprocess wrappers around the vendored `marketing-skills/` connector scripts.

## WHERE TO LOOK

| File | Tools | Wraps |
|------|-------|-------|
| `scraper_tools.py` | `query_creators`, `get_creator_details` | External scraper via `SCRAPER_DB_PATH` (SQLite) or `SCRAPER_API_URL` (REST) |
| `instagram_tools.py` | `send_instagram_dm`, `read_thread_messages` | `ig_client.get_ig_client()` singleton |
| `database_tools.py` | `save_conversation`, `log_dm`, `check_dm_quota`, `update_conversation_status` | `database.Database` via `set_database()` injection |
| `calculation_tools.py` | `calculate_fit_score`, `estimated_rate`, `calculate_engagement_rate` | Pure math, no I/O |
| `registry_tools.py` | Protocol registry read/write | subprocess → `marketing-skills/scripts/registry-events.py` |
| `connectors/*_tools.py` | 17 modules: appstore, bluesky, discourse, doh, experiment, fediverse, firecrawl, gdelt, hn, kg, ledger, pageviews, psi, rss, tavily, wayback, youtube | subprocess → `marketing-skills/scripts/connectors/*.py` |

## CONVENTIONS

- **`_Tool` callable wrapper**: canonical `_Tool` class in `scraper_tools.py` (`__call__` + `.run()` + `.name` + `.description`). `database_tools.py`/`instagram_tools.py` use `try: from crewai.tools import tool` with an identical `_Tool` fallback. crewai's real decorator returns non-callable objects — never use it bare.
- **Connector bridge**: each `connectors/*_tools.py` resolves its script path and runs `subprocess.run(["python", script] + args, timeout=CONNECTOR_TIMEOUT_SECONDS)`, parsing JSON stdout. Default timeout 30s (`config.py`).
- **Scraper dual-backend**: DB path first, REST API fallback; empty result when neither is set.
- **`set_database(db)`** must be called before any `database_tools` function. Auto-initializes `:memory:` if skipped. Tests must call it explicitly.

## ANTI-PATTERNS

- **No raw SQL from agent output** — all `database_tools` delegate to parameterized queries in `database.py`.
- **No additional instagrapi Client instances** — always `get_ig_client()`; a second `Client()` breaks the serial lock and rate limiter.
- **No real LLM calls inside tools** — LLM access goes through `llm_client.py` only; don't import `openai` here.
- **No network I/O in `calculation_tools.py`** — pure, deterministic, mock-free testable.
- **No importing `marketing-skills/` scripts directly** — subprocess only; keeps the vendored library decoupled.
