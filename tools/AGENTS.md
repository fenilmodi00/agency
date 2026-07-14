# tools/ — CrewAI Tool Functions

## OVERVIEW

A comprehensive toolset for the STAR framework, featuring 17 specialized connector modules for external data/APIs and registry tools for system state management. All tools use the `_Tool` callable wrapper pattern.

## WHERE TO LOOK

| File | Tools | Wraps |
|------|-------|-------|
| `connectors/` | 17 specialized modules | Scraper DB, Instagram API, Database CRUD, Calculations, LLM utilities |
| `registry_tools.py` | Registry access tools | Protocol registry for STAR framework state and routing |
| `scraper_tools.py` | `query_creators`, `get_creator_details`, etc. | External scraper DB (`SCRAPER_DB_PATH`) or REST API (`SCRAPER_API_URL`) |
| `calculation_tools.py` | `calculate_fit_score`, `estimated_rate`, etc. | Pure math, no I/O |
| `instagram_tools.py` | `send_instagram_dm`, `read_instagram_threads`, etc. | `ig_client.get_ig_client()` singleton |
| `database_tools.py` | `save_conversation`, `log_dm`, `save_contract`, etc. | `database.Database` via `set_database()` injection |
| `llm_tools.py` | `call_fireworks_llm`, `generate_gujarati_text` | `llm_client.call_fireworks_chat()` |
| `__init__.py` | (empty) | Package marker |

## CONVENTIONS

- **`@tool` import pattern**: `try: from crewai.tools import tool` / `except ImportError:` defines a local `_Tool` class (from `scraper_tools.py`) or a pass-through decorator. Both produce callables with `.name`, `.description`, `.run()`.
- **`set_database(db)`**: Must be called before any `database_tools` function. Auto-initializes `:memory:` if skipped. Tests must call it explicitly.
- **Scraper dual-backend**: `scraper_tools` checks `SCRAPER_DB_PATH` first, falls back to `SCRAPER_API_URL`. Returns empty list/dict if neither is set.

## ANTI-PATTERNS

- **No raw SQL from agent output.** All `database_tools` functions delegate to parameterized queries in `database.py`. Never construct SQL from agent-generated strings.
- **No additional instagrapi Client instances.** Always use `get_ig_client()` from `ig_client.py`. Creating a second `Client()` breaks the serial lock and rate limiter.
- **No real LLM calls inside tools.** `llm_tools.py` wraps `llm_client`, which handles the Fireworks API. Don't import `openai` or `requests` directly in tool functions to call LLMs.
- **No network I/O in `calculation_tools.py`.** Pure functions only. Fit scoring must be deterministic and testable without mocks.
