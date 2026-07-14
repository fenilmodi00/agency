# tools/ — CrewAI Tool Functions

## OVERVIEW

Six modules exposing `@tool`-decorated functions for scraper queries, fit scoring, Instagram DMs, database CRUD, and LLM calls. All use the `_Tool` callable wrapper pattern.

## WHERE TO LOOK

| File | Tools | Wraps |
|------|-------|-------|
| `scraper_tools.py` | `query_creators`, `get_creator_details`, `get_creator_content_summary`, `get_creator_language`, `get_creator_recent_posts` | External scraper DB (`SCRAPER_DB_PATH`) or REST API (`SCRAPER_API_URL`) |
| `calculation_tools.py` | `calculate_fit_score`, `estimated_rate`, `calculate_engagement_rate`, `calculate_reach_ratio` | Pure math, no I/O |
| `instagram_tools.py` | `send_instagram_dm`, `read_instagram_threads`, `read_thread_messages`, `get_profile` | `ig_client.get_ig_client()` singleton |
| `database_tools.py` | `save_conversation`, `update_conversation_status`, `update_conversation_negotiation`, `get_conversation_history`, `get_conversations_by_status`, `get_brand_budget`, `get_brand_brief`, `get_conversation_details`, `save_contract`, `check_dm_quota`, `log_dm` | `database.Database` via `set_database()` injection |
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
