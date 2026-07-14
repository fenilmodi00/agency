# vernacular-creator-agents - Work Plan

## TL;DR (For humans)

**What you'll get:** A pure-Python CLI toolchain that takes a brand brief in plain language (e.g., "thali restaurant in Ahmedabad, budget ₹15K"), automatically discovers matching Instagram creators from a companion scraper database, generates personalized Gujarati/Hindi outreach DMs, negotiates rates via Instagram DMs, and drafts ASCI-compliant collaboration contracts. All DMs are dry-run by default — you must pass `--send` to actually dispatch them.

**Why this approach:** CrewAI handles agent orchestration with zero infrastructure; instagrapi provides the only reliable Python interface to Instagram DMs; Fireworks AI gives high-quality multilingual LLM generation at $0.40–1.74/M input tokens, keeping a full campaign run well under $2 when token caps are enforced.

**What it will NOT do:** Scrape Instagram profiles (separate scraper repo), run a web server, use Docker or Celery, implement real-time MQTT reply detection (scheduled polling only), or support multi-account rotation (future).

**Effort:** Large (17+ files, 5 CrewAI agents, 2 database schemas, instagrapi integration, full test suite)
**Risk:** Medium — Instagram DMs can trigger account flags; session persistence, jittered delays, and rate limits mitigate this; dry-run default prevents accidental sends.
**Decisions to sanity-check:**
1. Dry-run-by-default with `--send` flag for actual dispatch.
2. `--approve-each` opt-in flag for per-creator confirmation.
3. Both SQLite-path and HTTP-API scraper integrations.
4. Single instagrapi `Client` with serial lock (not thread-safe).
5. Credential/session files use 0600 permissions, outside repo.
6. Rate limiting: 20 DMs/day (env-configurable), randomized 3–8s delay between calls.
7. Budget acceptance criterion: full dry-run under 25K total tokens / <$2 with logged token counts.
8. ACSI scope: contract templates include disclosure placeholders (not legal review).

Your next move: **Approve this plan** so a worker can start building. Alternatively, run another high-accuracy review round.

---

> TL;DR (machine): Large | Medium | 17+ files, 5 CrewAI agents, 2 DBs, instagrapi DMs, Fireworks LLMs, dry-run safety, ASCI contracts, token-budget enforcement. CLI only.

## Scope
### Must have
- Project bootstrap: git init, .env.example, .gitignore, requirements.txt, directory structure
- `config.py`: load all env vars, model config per agent, safety thresholds, **token-budget constants**
- `llm_client.py`: Fireworks AI wrapper via `openai` SDK with custom `base_url`; CrewAI `LLM` factory; **token-usage logging helper**
- `database.py` + `db/schema.sql`: SQLite with WAL mode, 5 tables including `conversations.last_message_count`
- `ig_client.py`: instagrapi singleton wrapper — session load/save, login with challenge handler, `direct_send()`, `direct_threads()`, `direct_thread()`, `user_id_from_username()`; exception handling; **randomized delay 3–8s**; token-bucket rate limiter; serial lock; 0600 session file permissions
- `tools/`: CrewAI `@tool` decorated functions
  - `instagram_tools.py`: send_dm, read_threads, read_thread_messages, get_profile
  - `database_tools.py`: save_conversation, update_conversation_status, **update_conversation_negotiation**, **get_brand_brief**, get_conversation_details, get_conversation_history, get_conversations_by_status, get_brand_budget, save_contract, check_dm_quota, log_dm
  - `scraper_tools.py`: query_creators, get_creator_details, get_creator_content_summary, get_creator_language, get_creator_recent_posts
  - `calculation_tools.py`: calculate_fit_score, calculate_engagement
  - `llm_tools.py`: Fireworks LLM call helpers with token tracking
- 5 CrewAI agents:
  1. `agents/discovery.py`: parse brand brief → query scraper → filter/rank → return ranked list
  2. `agents/proposal.py`: get creator content → generate campaign ideas → suggest budget/timeline
  3. `agents/outreach.py`: generate Gujarati/Hindi DM → dry-run check → send via instagrapi → log
  4. `agents/negotiator.py`: read replies → analyze sentiment → respond in creator's language → update status
  5. `agents/contract.py`: read agreed terms → generate contract with ASCI disclosure placeholders → save
- Prompts in `prompts/` dir (5 prompt files referenced by agents), each with explicit output schema
- `crew.py`: sequential Crew chaining Discovery → Proposal → Outreach
- `main.py`: CLI entry — dry-run default, `--send` for real dispatch, `--approve-each` for per-creator confirmation
- `check_replies.py`: scheduled script — reads conversations, detects new replies via `last_message_count`, runs Negotiator, runs Contract for accepted deals
- `test_agents.py` + `tests/` with mocked instagrapi Client and mocked Fireworks LLM responses
- `AGENTS.md` + `README.md` + `docs/research.md`
- Single instagrapi `Client` instance with a thread lock; serial-per-account execution enforced.
- Session/credential files stored with 0600/0400 permissions, never inside repo.
- Token-budget enforcement: `MAX_TOKENS_PER_AGENT` default 4000; crew dry-run under 25K total tokens.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- NO Instagram scraping or follower harvesting
- NO web frontend, FastAPI server, Docker, Celery, async workers
- NO real-time MQTT reply detection (scheduled polling only)
- NO multi-account rotation logic (single account; rotation env vars as comments only)
- NO payment gateway integration
- NO actual legal review of contracts (templates include disclosure placeholders only)
- NO modification of the external scraper repo's data
- NO `print()` statements — all logging via loguru
- NO hardcoded secrets in source files
- NO fixed-interval delays against Instagram (must use randomized jitter)
- NO crew execution that exceeds token budget without logging and warning

## Verification strategy
> Zero human intervention — all verification is agent-executed.
- **Test decision**: tests-after for infrastructure (config, database, ig_client), TDD for agents
- **Framework**: pytest with pytest-mock
- **Evidence**: `.omo/evidence/vernacular-creator-agents/task-<N>.<ext>`
- **Cost gate**: every test that exercises LLM tooling uses a mocked client; token usage assertions run against mock counters.

## Execution strategy
### Parallel execution waves
- **Wave 1** (5 todos, parallel): Project setup, Config/LLM client, Database schema+CRUD, instagrapi wrapper, Scraper tools, Calculation tools
- **Wave 2** (3 todos, parallel after Wave 1): Instagram tools, Database tools, LLM tools
- **Wave 3** (1 todo, parallel after Wave 2): Agent prompts
- **Wave 4** (5 todos, parallel after Wave 3): 5 agents — Discovery, Proposal, Outreach, Negotiator, Contract (file-level implementation is parallel; runtime chain is enforced by Crew orchestration in Task 16)
- **Wave 5** (2 todos, parallel after Wave 4): Crew orchestration, CLI runner
- **Wave 6** (2 todos, parallel after Wave 5): Reply checker, Test suite
- **Wave 7** (1 todo, parallel after Wave 6): Documentation
- **Final Wave**: F1-F4 parallel reviewers

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Project bootstrap | — | 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20 | — |
| 2. Config + LLM client | — | 4,7,8,9,10,11,12,13,14,15,16,17,18,19 | 1,3,4,5,6 |
| 3. Database schema + CRUD | — | 4,7,8,10,12,13,14,15,16,17,18,19 | 1,2,4,5,6 |
| 4. instagrapi wrapper | 2 | 7,13,14,16,19 | 1,2,3,5,6 |
| 5. Scraper tools | 3 | 11,19 | 1,2,3,4,6 |
| 6. Calculation tools | — | 11,19 | 1,2,3,4,5 |
| 7. Instagram tools | 4,3 | 13,14,16,18,19 | 8,9 |
| 8. Database tools | 3 | 11,12,13,14,15,16,17,18,19 | 7,9 |
| 9. LLM tools | 2 | 11,12,13,14,15,16,17,18,19 | 7,8 |
| 10. Agent prompts | — | 11,12,13,14,15,19 | 7,8,9 |
| 11. Discovery agent | 5,6,8,9,10 | 16,19 | 12,13,14,15 |
| 12. Proposal agent | 8,9,10 | 16,19 | 11,13,14,15 |
| 13. Outreach agent | 7,8,9,10 | 16,19 | 11,12,14,15 |
| 14. Negotiator agent | 7,8,9,10 | 16,18,19 | 11,12,13,15 |
| 15. Contract agent | 8,9,10 | 16,18,19 | 11,12,13,14 |
| 16. Crew orchestration | 11,12,13 | 17,18,19 | — |
| 17. CLI runner (main.py) | 2,3,16 | 19 | — |
| 18. Reply checker | 3,7,14,15,16 | 19 | — |
| 19. Test suite | 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18 | 20 | — |
| 20. Documentation | 19 | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->

### WAVE 1 — Foundation (parallel)

- [x] 1. Project bootstrap — create directory tree, .env.example, .gitignore, requirements.txt
  What to do / Must NOT do:
    - mkdir: project root, then subdirs `tools/`, `agents/`, `prompts/`, `db/`, `data/`, `tests/`, `docs/`
    - Write `.env.example` with every required env var:
      - FIREWORKS_API_KEY, FIREWORKS_BASE_URL
      - MODEL_DISCOVERY, MODEL_PROPOSAL, MODEL_OUTREACH, MODEL_NEGOTIATOR, MODEL_CONTRACT (defaults: accounts/fireworks/models/glm-5p2, qwen3p7-plus, deepseek-v4-pro as applicable)
      - IG_USERNAME, IG_PASSWORD, IG_SESSION_FILE
      - SCRAPER_DB_PATH, SCRAPER_API_URL
      - AGENTS_DB_PATH
      - MAX_DMS_PER_DAY=20, DM_DELAY_SECONDS=5, DM_DELAY_JITTER=3 (randomized delay = DM_DELAY_SECONDS ± DM_DELAY_JITTER)
      - MAX_NEGOTIATION_ROUNDS=3, BUDGET_OVERRUN_PERCENT=120, MAX_PROFILE_FETCHES_PER_RUN=50
      - MAX_TOKENS_PER_AGENT=4000, MAX_TOTAL_TOKENS_PER_RUN=25000
      - LOG_LEVEL=INFO
    - Write `.gitignore`: `.env`, `data/*.db`, `data/ig_session.json`, `__pycache__/`, `.python-version`, `.omo/evidence/`, `.pytest_cache/`
    - Write `requirements.txt`: crewai>=1.15.0, instagrapi>=2.5.0, openai>=1.0, python-dotenv>=1.0, requests>=2.31, loguru>=0.7, pytest, pytest-mock
    - Create `data/.gitkeep` and empty `db/` directory
    - Must NOT create any Python logic files in this todo
  Parallelization: Wave 1 | Blocked by: — | Blocks: 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20
  References: spec `.env.example` block; spec `requirements.txt` block; spec `PROJECT STRUCTURE` tree
  Acceptance criteria:
    - `ls tools agents prompts db data tests docs` exits 0
    - `.env.example` contains every env var listed above
    - `python -c "from dotenv import dotenv_values; d=dotenv_values('.env.example'); print(sorted(d.keys()))"` prints all keys
    - `.gitignore` contains `.env`, `data/ig_session.json`, `__pycache__/`
  QA scenarios:
    - happy: fresh clone can `pip install -r requirements.txt` without error
    - failure: missing required key in `.env.example` causes a key lookup error
  Evidence: .omo/evidence/vernacular-creator-agents/task-1.txt
  Commit: Y | chore(init): scaffold project structure and dependencies

- [x] 2. Config + LLM client — `config.py` and `llm_client.py`
  What to do / Must NOT do:
    - `config.py`:
      - Load `.env` with python-dotenv; export typed constants via dataclasses or module-level constants
      - Constants: all env vars from Task 1
      - Parse numeric safety constants with fallback defaults
      - Export `DM_DELAY_MIN = DM_DELAY_SECONDS - DM_DELAY_JITTER` and `DM_DELAY_MAX = DM_DELAY_SECONDS + DM_DELAY_JITTER`, clamped to >=0
      - Add `MAX_TOKENS_PER_AGENT`, `MAX_TOTAL_TOKENS_PER_RUN`
    - `llm_client.py`:
      - `get_fireworks_llm(model_name: str) -> crewai.LLM` using `LLM(model=model_name, api_key=..., base_url=...)`
      - `get_token_usage(response) -> dict` extracts prompt_tokens, completion_tokens, total_tokens from OpenAI response object
      - `format_model_path(alias: str) -> str` maps friendly aliases like "glm-5.2" to real Fireworks paths "accounts/fireworks/models/glm-5p2"
      - Direct `openai` SDK convenience function `call_fireworks_chat(...)` returning (content, usage_dict)
    - Must NOT call any LLM during module import
  Parallelization: Wave 1 | Blocked by: — | Blocks: 4,7,8,9,10,11,12,13,14,15,16,17,18
  References: spec FIREWORKS AI section; CrewAI custom LLM docs at https://docs.crewai.com/v1.15.1/en/learn/custom-llm; https://docs.fireworks.ai/tools-sdks/openai-compatibility
  Acceptance criteria:
    - `python -c "from config import MAX_DMS_PER_DAY, DM_DELAY_MIN, DM_DELAY_MAX, MAX_TOKENS_PER_AGENT; assert MAX_DMS_PER_DAY == 20; assert 2 <= DM_DELAY_MIN < DM_DELAY_MAX <= 10; assert MAX_TOKENS_PER_AGENT == 4000"`
    - `python -c "from llm_client import get_fireworks_llm, format_model_path; assert format_model_path('glm-5.2') == 'accounts/fireworks/models/glm-5p2'; llm = get_fireworks_llm('accounts/fireworks/models/glm-5p2'); assert llm is not None"`
  QA scenarios:
    - happy: config loads with defaults when env file is empty; LLM factory returns LLM instance
    - failure: missing FIREWORKS_API_KEY logs a clear error at runtime (not import)
  Evidence: .omo/evidence/vernacular-creator-agents/task-2.txt
  Commit: Y | feat(core): add config and Fireworks LLM client with token tracking

- [x] 3. Database schema + CRUD — `db/schema.sql` and `database.py`
  What to do / Must NOT do:
    - `db/schema.sql`: exact CREATE TABLE statements with columns:
      - `brand_briefs`: id INTEGER PRIMARY KEY, raw_brief TEXT NOT NULL, parsed_brief TEXT (JSON), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      - `campaign_suggestions`: id INTEGER PRIMARY KEY, brief_id INTEGER NOT NULL REFERENCES brand_briefs(id), creator_username TEXT NOT NULL, fit_score REAL, match_reason TEXT, outreach_message TEXT, campaign_ideas TEXT (JSON), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      - `conversations`: id INTEGER PRIMARY KEY, brief_id INTEGER NOT NULL REFERENCES brand_briefs(id), creator_username TEXT NOT NULL, thread_id TEXT, status TEXT NOT NULL CHECK(status IN ('outreach_sent','replied','negotiating','declined','accepted','contract_sent')), last_message_text TEXT, last_message_direction TEXT CHECK(last_message_direction IN ('sent','received')), negotiation_history TEXT (JSON), agreed_rate REAL, last_message_count INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      - `contracts`: id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL REFERENCES conversations(id), creator_username TEXT NOT NULL, brand_name TEXT, contract_text TEXT NOT NULL, contract_type TEXT CHECK(contract_type IN ('barter','paid','affiliate')), deliverables TEXT (JSON), usage_rights TEXT, timeline TEXT, asci_compliant INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      - `dm_log`: id INTEGER PRIMARY KEY, creator_username TEXT NOT NULL, thread_id TEXT, message_text TEXT, direction TEXT CHECK(direction IN ('sent','received')), sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      - PRAGMA journal_mode=WAL at top of schema
    - `database.py`:
      - `Database` class with `db_path`, `init_db()`, context-managed connections
      - `insert_brief(raw_brief, parsed_brief) -> int`
      - `get_brief(brief_id) -> dict`
      - `insert_suggestion(brief_id, creator_username, fit_score, match_reason, outreach_message, campaign_ideas) -> int`
      - `get_suggestions_by_brief(brief_id) -> list[dict]`
      - `insert_conversation(brief_id, creator_username, thread_id, status, last_message_text, last_message_direction, last_message_count=0) -> int`
      - `get_conversation(conversation_id) -> dict`
      - `get_conversations_by_status(status) -> list[dict]`
      - `update_conversation_status(conversation_id, status, agreed_rate=None, negotiation_history=None) -> bool`
      - `update_conversation_negotiation(conversation_id, negotiation_history, last_message_count) -> bool`
      - `insert_contract(...all columns...) -> int`
      - `get_contract(contract_id) -> dict`
      - `insert_dm_log(creator_username, thread_id, message_text, direction) -> int`
      - `get_todays_dm_count() -> int`
    - Must NOT use ORM
    - Must NOT leak connections
  Parallelization: Wave 1 | Blocked by: — | Blocks: 4,7,8,10,12,13,14,15,16,17,18
  References: spec DATABASE TABLES section
  Acceptance criteria:
    - `python -c "from database import Database; db = Database(':memory:'); db.init_db(); print('ok')"` succeeds
    - Insert a brand_brief with `raw_brief='test'`, read it back, assert `raw_brief=='test'` and `parsed_brief` is None or JSON
    - Insert a conversation with `brief_id=1, last_message_count=5`, call `update_conversation_negotiation`, read back `last_message_count==5`
    - `get_conversation_details(1)` returns dict with both `creator_username` and `raw_brief` after inserting a brand_brief and conversation
    - `get_todays_dm_count()` returns 0 on empty dm_log
  QA scenarios:
    - happy: full CRUD round-trip for brand_briefs, conversations, contracts, dm_log
    - failure: inserting campaign_suggestion with invalid brief_id raises IntegrityError
  Evidence: .omo/evidence/vernacular-creator-agents/task-3.txt
  Commit: Y | feat(db): add SQLite schema and CRUD operations

- [x] 4. instagrapi wrapper — `ig_client.py`
  What to do / Must NOT do:
    - `InstagramClient` class with lazy singleton accessor `get_ig_client()`
    - `__init__` only creates `instagrapi.Client()`; does NOT call `login()` unless explicitly requested
    - `login()`: load settings from `IG_SESSION_FILE` BEFORE calling `login()`; if missing, login with username/password then dump settings; chmod session file to 0o600
    - Challenge resolver: implement `challenge_code_handler(username, choice)` logging the choice and prompting for code (for interactive use)
    - `send_dm(user_id: int, message: str) -> dict`: wait randomized `random.uniform(DM_DELAY_MIN, DM_DELAY_MAX)` seconds, call `cl.direct_send`, return `{success: bool, thread_id: str|None, error: str|None}`
    - `read_threads(amount=20) -> list`: rate-limited, returns raw thread list or []
    - `read_thread(thread_id, amount=50) -> list`: rate-limited, returns messages or []
    - `user_id_from_username(username) -> int | None`: rate-limited
    - Wrap every `cl.*` call with `threading.Lock` and exception handling for `ChallengeRequired`, `LoginRequired`, `UserNotFound`, `DirectThreadNotFound`, rate limits
    - On `LoginRequired`: re-login with session, retry once
    - On `PleaseWaitFewMinutes` / rate limit: exponential backoff up to 60s
    - Token-bucket rate limiter: allow at most `MAX_DMS_PER_DAY` per 24h window, enforced in `send_dm`
    - Must NOT scrape profiles or posts
    - Must NOT create more than one Client instance per process
  Parallelization: Wave 1 | Blocked by: 2 | Blocks: 7,15,16
  References: instagrapi docs: https://subzeroid.github.io/instagrapi/usage-guide/direct.html, https://subzeroid.github.io/instagrapi/usage-guide/challenge_resolver.html, https://subzeroid.github.io/instagrapi/usage-guide/handle-exception.html, https://subzeroid.github.io/instagrapi/usage-guide/best-practices.html
  Acceptance criteria:
    - `python -c "from ig_client import get_ig_client; cl = get_ig_client(); print(type(cl))"` succeeds without env vars (no login attempted)
    - Mock test: `cl.send_dm(123, 'hello')` with mocked `cl.direct_send` calls it exactly once and returns success dict
    - Delay test: two sequential `send_dm` calls are separated by at least `DM_DELAY_MIN` seconds (use `time.monotonic()` in test)
    - Lock test: a thread trying `send_dm` while another holds the lock waits
  QA scenarios:
    - happy: login with existing session file, send DM, read threads
    - failure: `ChallengeRequired` triggers challenge handler and retries; `UserNotFound` returns `{success: False, error: 'UserNotFound'}`
  Evidence: .omo/evidence/vernacular-creator-agents/task-4.txt
  Commit: Y | feat(ig): add instagrapi wrapper with sessions, jittered delays, and rate limiting

- [x] 5. Scraper tools — `tools/scraper_tools.py`
  What to do / Must NOT do:
    - CrewAI `@tool` decorated functions
    - `query_creators(filters: dict) -> list[dict]`:
      - If `SCRAPER_DB_PATH` exists and is file: open SQLite, SELECT creators WHERE follower_count BETWEEN ? AND ? AND avg_reel_views >= ? AND is_active = ? AND (region=? OR ? IS NULL) AND (niche=? OR ? IS NULL) AND (detected_language=? OR ? IS NULL)
      - Elif `SCRAPER_API_URL` set: GET `{SCRAPER_API_URL}/creators` with query params
      - Else: log error, return []
      - Default filters: follower_min=8000, follower_max=50000, min_reel_views=60000, is_active=true
    - `get_creator_details(username) -> dict | None`
    - `get_creator_content_summary(username) -> str | None`
    - `get_creator_language(username) -> str | None`
    - `get_creator_recent_posts(username) -> list[dict]`: API GET `/creators/{username}/posts?limit=5` or SQLite SELECT posts
    - Must NOT modify scraper data
    - Must NOT crash if scraper unreachable
  Parallelization: Wave 1 | Blocked by: 3 | Blocks: 11
  References: spec DATA SOURCE section, expected creator data shape
  Acceptance criteria:
    - `python -c "from tools.scraper_tools import query_creators; r = query_creators({}); assert isinstance(r, list)"`
    - Mock SQLite: create temp scraper DB with `creators` table matching expected schema, insert row, `query_creators({'region': 'ahmedabad'})` returns that row
    - API mode: mock `requests.get`, assert URL contains `/creators` and params
  QA scenarios:
    - happy: query with filters returns matching rows
    - failure: missing `SCRAPER_DB_PATH` and empty `SCRAPER_API_URL` logs error and returns []
  Evidence: .omo/evidence/vernacular-creator-agents/task-5.txt
  Commit: Y | feat(scraper): add scraper DB/API integration tools

- [x] 6. Calculation tools — `tools/calculation_tools.py`
  What to do / Must NOT do:
    - `calculate_fit_score(creator: dict, brief: dict) -> float`:
      - niche_match: 25 if creator['detected_niche'] == brief['product_category'] else 0
      - language_match: 20 if creator['detected_language'] in brief['target_language'] or brief['target_language'] in creator['detected_language'] else 0
      - region_match: 20 if creator['detected_region'] == brief['target_location'] else 0
      - budget_fit: 15 if brief['budget_max'] >= estimated_rate(creator) else 0, where `estimated_rate(creator)` = follower_count * 0.5 (₹0.50 per follower, capped at budget_max) — a simple heuristic, logged
      - brand_experience: 10 if creator['has_brand_experience'] else 0
      - engagement_rate: 5 if calculate_engagement_rate(...) >= 3.0 else 0
      - reach_ratio: 5 if calculate_reach_ratio(...) >= 3.0 else 0
      - Return sum / 100.0
    - `estimated_rate(creator: dict) -> float`: follower_count * 0.5, safe return 0.0 if follower_count missing or 0
    - `calculate_engagement_rate(followers, avg_likes, avg_comments) -> float`: safe division, return 0.0 if followers==0
    - `calculate_reach_ratio(avg_reel_views, followers) -> float`: safe division
    - Must NOT access network or database
  Parallelization: Wave 1 | Blocked by: — | Blocks: 11
  References: spec Discovery agent process
  Acceptance criteria:
    - `calculate_fit_score({'detected_niche':'food','detected_language':'gujarati','detected_region':'ahmedabad','has_brand_experience':True,'follower_count':10000,'avg_likes':600,'avg_comments':60,'avg_reel_views':50000}, {'product_category':'food','target_language':'gujarati','target_location':'ahmedabad','budget_max':15000})` returns 1.0
    - `estimated_rate({'follower_count': 10000})` returns 5000.0
    - `calculate_engagement_rate(10000, 500, 50)` returns 5.5
    - `calculate_engagement_rate(0, 500, 50)` returns 0.0
  QA scenarios:
    - happy: perfect match returns 1.0, zero match returns 0.0
    - failure: division by zero handled, missing keys handled gracefully
  Evidence: .omo/evidence/vernacular-creator-agents/task-6.txt
  Commit: Y | feat(calc): add fit score and engagement calculation tools

### WAVE 2 — Tool layer (parallel after Wave 1)

- [x] 7. Instagram tools — `tools/instagram_tools.py`
  What to do / Must NOT do:
    - `@tool` decorated functions using `get_ig_client()` singleton
    - `send_instagram_dm(creator_username: str, message: str) -> dict`: resolve user_id, call `get_ig_client().send_dm(user_id, message)`, return `{success, thread_id, error}`
    - `read_instagram_threads(amount=20) -> list[dict]`
    - `read_thread_messages(thread_id: str, amount=50) -> list[dict]`
    - `get_profile(username: str) -> dict | None`
    - Must NOT create additional Client instances
  Parallelization: Wave 2 | Blocked by: 4,3 | Blocks: 13,14
  References: spec `tools/instagram_tools.py`, instagrapi docs
  Acceptance criteria:
    - `python -c "from tools.instagram_tools import send_instagram_dm; from crewai.tools import BaseTool; assert isinstance(send_instagram_dm, BaseTool) or callable(send_instagram_dm)"`
    - Mock test: monkeypatch `get_ig_client().send_dm` to return success; `send_instagram_dm.run('alice', 'hi')` returns dict with `success=True`
  QA scenarios:
    - happy: successful DM returns thread_id
    - failure: `UserNotFound` returns dict with `success=False, error='UserNotFound'`
  Evidence: .omo/evidence/vernacular-creator-agents/task-7.txt
  Commit: Y | feat(tools): add Instagram DM/thread tools

- [x] 8. Database tools — `tools/database_tools.py`
  What to do / Must NOT do:
    - `@tool` decorated functions wrapping `Database` methods
    - `save_conversation(brief_id, creator_username, thread_id, status='outreach_sent', last_message_text='', last_message_direction='sent', last_message_count=0) -> int`
      - Insert into conversations table with `brief_id`, return id
    - `update_conversation_status(conversation_id, status, agreed_rate=None, negotiation_history=None) -> bool`
    - `update_conversation_negotiation(conversation_id, negotiation_history, last_message_count) -> bool`
    - `get_conversation_history(conversation_id) -> dict | None`
    - `get_conversations_by_status(status) -> list[dict]`
    - `get_brand_budget(brief_id) -> tuple[float|None, float|None]` — parse budget string like "5000-25000" or "₹15,000"
    - `get_brand_brief(brief_id) -> dict | None`
    - `get_conversation_details(conversation_id) -> dict | None` — joins conversation + brand_brief on `conversations.brief_id = brand_briefs.id`
    - `save_contract(conversation_id, creator_username, brand_name, contract_text, contract_type, deliverables, usage_rights, timeline, asci_compliant) -> int`
    - `check_dm_quota() -> tuple[int, int]` — (sent_today, max_per_day)
    - `log_dm(creator_username, thread_id, message_text, direction) -> int`
    - Must NOT accept SQL strings from agent output
  Parallelization: Wave 2 | Blocked by: 3 | Blocks: 11,12,13,14,15,16,17,18
  References: spec DATABASE TABLES section, `database.py`
  Acceptance criteria:
    - Each function is a valid CrewAI tool with `.name` and `.description`
    - Mock DB test: `save_conversation.run(1,'alice','123')` returns int > 0; `get_brand_brief.run(1)` returns dict with `raw_brief`; `get_conversation_details.run(1)` returns dict containing both `creator_username` and `raw_brief`
    - `get_brand_budget.run(1)` with parsed_brief `{"budget_max": 15000}` returns `(0, 15000)`
    - `check_dm_quota` returns `(0, MAX_DMS_PER_DAY)` on empty dm_log
  QA scenarios:
    - happy: full round-trip for save/update/get of conversation, contract, dm_log
    - failure: invalid conversation_id returns None or False, not exception
  Evidence: .omo/evidence/vernacular-creator-agents/task-8.txt
  Commit: Y | feat(tools): add database CRUD tools including negotiation and brand-brief tools

- [x] 9. LLM tools — `tools/llm_tools.py`
  What to do / Must NOT do:
    - `@tool` decorated standalone LLM helpers
    - `call_fireworks_llm(prompt: str, model: str = None, temperature: float = 0.2, max_tokens: int = None) -> str`:
      - Uses `llm_client.call_fireworks_chat`
      - Logs total tokens via loguru
      - Default `max_tokens` falls back to `MAX_TOKENS_PER_AGENT`
    - `generate_gujarati_text(prompt: str) -> str`: uses `MODEL_OUTREACH` model
    - Must NOT replace CrewAI agent LLM routing
  Parallelization: Wave 2 | Blocked by: 2 | Blocks: 11,12,13,14,15,16,17,18
  References: https://docs.fireworks.ai/guides/function-calling, https://docs.fireworks.ai/tools-sdks/openai-compatibility
  Acceptance criteria:
    - `python -c "from tools.llm_tools import call_fireworks_llm; assert hasattr(call_fireworks_llm, 'name')"`
    - Mock test: monkeypatch `call_fireworks_chat` to return `('hello', {'prompt_tokens':10,'completion_tokens':5,'total_tokens':15})`; `call_fireworks_llm.run('hi')` returns 'hello' and logs 15 tokens
  QA scenarios:
    - happy: returns generated text and logs token usage
    - failure: API error returns error string, logs exception
  Evidence: .omo/evidence/vernacular-creator-agents/task-9.txt
  Commit: Y | feat(tools): add Fireworks LLM call tools with token tracking

### WAVE 3 — Agent prompts

- [x] 10. Agent prompts — `prompts/*.txt`
  What to do / Must NOT do:
    - Create 5 plain-text prompt files with explicit output schema sections
    - `prompts/discovery_prompt.txt`: role/goal/backstory, instruct agent to parse brief into JSON `{business_type, product_category, target_location, target_language, target_audience, budget_min, budget_max, content_preference, tone}`, query creators, score, output JSON array `[{username, fit_score, match_reason}]`
    - `prompts/proposal_prompt.txt`: output JSON `{creator_username, campaign_ideas: [...], deliverables: [...], suggested_budget: {min, max}, timeline, notes}`
    - `prompts/outreach_prompt.txt`: output JSON `{creator_username, message, language}`; message must be warm, reference creator content, include brand intro + collab proposal + ask for rate
    - `prompts/negotiator_prompt.txt`: output JSON `{action, response, agreed_rate, round_number, status}`; rules: max 3 rounds, never exceed 120% budget, respond in creator's language
    - `prompts/contract_prompt.txt`: output JSON `{contract_text, gujarati_summary, contract_type, deliverables, usage_rights, timeline, asci_compliant}`; include ASCI disclosure clauses and "seek legal counsel" disclaimer
    - Must NOT include actual secrets or example credentials
  Parallelization: Wave 3 | Blocked by: — | Blocks: 11,12,13,14,15
  References: spec AGENT sections, ASCI guidelines: https://www.ascionline.in/social/wp-content/uploads/2025/04/ASCI-Influencer-Guidelines.pdf
  Acceptance criteria:
    - All 5 files exist, each > 20 lines
    - Each file contains an "Output JSON schema" section listing the required keys
    - Grep for `#ad` or `#sponsored` in contract prompt returns at least one match
    - Grep for "seek legal counsel" in contract prompt returns one match
  QA scenarios:
    - happy: prompts are parseable text with placeholders
    - failure: missing file raises FileNotFoundError
  Evidence: .omo/evidence/vernacular-creator-agents/task-10.txt
  Commit: Y | feat(prompts): add all 5 agent prompts with output schemas

### WAVE 4 — Agents (parallel after Wave 3)

- [x] 11. Discovery Agent — `agents/discovery.py`
  What to do / Must NOT do:
    - `get_discovery_agent() -> crewai.Agent` with model from `MODEL_DISCOVERY`, tools=[query_creators, get_creator_details, calculate_fit_score]
    - `get_discovery_task(brief_text: str, agent: Agent) -> crewai.Task`
    - Task expected_output: valid JSON array with keys `username, fit_score, match_reason`
    - Agent must NOT write to AGENTS_DB
  Parallelization: Wave 4 | Blocked by: 5,6,8,9,10 | Blocks: 16 (crew)
  References: spec Agent 1, `prompts/discovery_prompt.txt`
  Acceptance criteria:
    - `python -c "from agents.discovery import get_discovery_agent, get_discovery_task; a = get_discovery_agent(); t = get_discovery_task('test', a); assert a.role; assert 'JSON array' in t.expected_output"`
    - Mock tools: `query_creators` returns 2 creators; `calculate_fit_score` returns 0.85; task output parses as JSON list of length 2
  QA scenarios:
    - happy: agent/task instantiate with correct tools and prompt
    - failure: missing prompt file raises FileNotFoundError; malformed tool output returns error dict
  Evidence: .omo/evidence/vernacular-creator-agents/task-11.txt
  Commit: Y | feat(agent): add Discovery agent

- [x] 12. Proposal Agent — `agents/proposal.py`
  What to do / Must NOT do:
    - `get_proposal_agent() -> Agent` with model `MODEL_PROPOSAL`, tools=[get_creator_content_summary, get_creator_recent_posts]
    - `get_proposal_task(creators_json: str, agent: Agent) -> Task`
    - Output JSON array: `[{creator_username, campaign_ideas, deliverables, suggested_budget, timeline, notes}]`
    - Agent must NOT write to AGENTS_DB
  Parallelization: Wave 4 | Blocked by: 8,9,10 | Blocks: 16
  References: spec Agent 2, `prompts/proposal_prompt.txt`
  Acceptance criteria:
    - `python -c "from agents.proposal import get_proposal_agent, get_proposal_task; a = get_proposal_agent(); t = get_proposal_task('[]', a); assert 'campaign_ideas' in t.expected_output"`
    - Mock tools: content summary returns "food blogger"; recent posts returns 5 posts; task output parses as JSON list with required keys
  QA scenarios:
    - happy: proposal generated for each creator
    - failure: empty creators list returns `[]`
  Evidence: .omo/evidence/vernacular-creator-agents/task-12.txt
  Commit: Y | feat(agent): add Proposal agent

- [x] 13. Outreach Agent — `agents/outreach.py`
  What to do / Must NOT do:
    - `get_outreach_agent(send: bool = False) -> Agent` with model `MODEL_OUTREACH`, tools=[send_instagram_dm, get_creator_language, save_conversation, log_dm, check_dm_quota]
    - `get_outreach_task(proposals_json: str, agent: Agent, send: bool = False) -> Task`
    - Process enforced by agent prompt + crew context:
      1. Check DM quota; fail fast if exceeded
      2. Get creator language
      3. Generate DM in creator's language
      4. If `send=False`: log DM and return without calling `send_instagram_dm`
      5. If `send=True`: call `send_instagram_dm`, save conversation, log DM
    - Output JSON: `{username, thread_id, language, sent: bool, dry_run: bool}`
    - Must NOT send if quota exceeded regardless of `send` flag
    - Must save conversation with the current `brief_id` from crew context
  Parallelization: Wave 4 | Blocked by: 7,8,9,10 | Blocks: 16
  References: spec Agent 3, `prompts/outreach_prompt.txt`
  Acceptance criteria:
    - `python -c "from agents.outreach import get_outreach_agent; a = get_outreach_agent(send=False); assert a is not None"`
    - Mock test with `send=False`: `send_instagram_dm` is never called; output JSON has `sent=False, dry_run=True`
    - Mock test with quota exceeded: `send_instagram_dm` is never called even if `send=True`
    - Mock test: `save_conversation` receives `brief_id=1` when crew context provides brief_id=1
  QA scenarios:
    - happy: send=True with quota available calls send_instagram_dm and returns sent=True
    - failure: quota exceeded returns sent=False with error reason
  Evidence: .omo/evidence/vernacular-creator-agents/task-13.txt
  Commit: Y | feat(agent): add Outreach agent with dry-run and quota safety

- [x] 14. Negotiator Agent — `agents/negotiator.py`
  What to do / Must NOT do:
    - `get_negotiator_agent() -> Agent` with model `MODEL_NEGOTIATOR`, tools=[read_instagram_threads, read_thread_messages, send_instagram_dm, get_conversation_history, update_conversation_negotiation, get_brand_budget, check_dm_quota, log_dm]
    - Output JSON: `{action, response, agreed_rate, round_number, status}`
    - Rules in prompt:
      - Never exceed 120% of brand budget without action='escalate'
      - If barter: evaluate product value >= creator's typical rate
      - Always respond in creator's language
      - Max 3 rounds; if `round_number >= MAX_NEGOTIATION_ROUNDS`, action='give_up'
    - Must NOT send counter-offer if quota exceeded
  Parallelization: Wave 4 | Blocked by: 7,8,9,10 | Blocks: 18
  References: spec Agent 4, `prompts/negotiator_prompt.txt`
  Acceptance criteria:
    - `python -c "from agents.negotiator import get_negotiator_agent; a = get_negotiator_agent(); assert a is not None"`
    - Mock test: budget 15000, creator asks 20000 → action='counter' with agreed_rate <= 18000 (120%)
    - Mock test: round_number=3 → action='give_up'
    - Mock test: quota exceeded → action='defer' and no DM sent
  QA scenarios:
    - happy: new reply detected, counter-offer sent, status updated
    - failure: budget overrun beyond 120% returns escalate action
  Evidence: .omo/evidence/vernacular-creator-agents/task-14.txt
  Commit: Y | feat(agent): add Negotiator agent with budget and round limits

- [x] 15. Contract Agent — `agents/contract.py`
  What to do / Must NOT do:
    - `get_contract_agent() -> Agent` with model `MODEL_CONTRACT`, tools=[get_conversation_details, get_brand_brief, save_contract]
    - Output JSON: `{contract_text, gujarati_summary, contract_type, deliverables, usage_rights, timeline, asci_compliant}`
    - Contract must include sections: parties, campaign description, deliverables, usage rights, timeline, compensation, content guidelines, exclusivity, termination, ASCI disclosure
    - Include "This is a template. Seek legal counsel before signing."
    - `asci_compliant` must be True
  Parallelization: Wave 4 | Blocked by: 8,9,10 | Blocks: 18
  References: spec Agent 5, `prompts/contract_prompt.txt`, ASCI guidelines
  Acceptance criteria:
    - `python -c "from agents.contract import get_contract_agent; a = get_contract_agent(); assert a is not None"`
    - Mock test: contract output JSON contains `#ad` or `#sponsored` in contract_text, contains "seek legal counsel", has all required keys
  QA scenarios:
    - happy: accepted conversation generates contract and saves to DB
    - failure: missing conversation details returns error JSON
  Evidence: .omo/evidence/vernacular-creator-agents/task-15.txt
  Commit: Y | feat(agent): add Contract agent with ASCI disclosure templates

### WAVE 5 — Orchestration (parallel after Wave 4)

- [x] 16. Crew orchestration — `crew.py`
  What to do / Must NOT do:
    - `InfluencerCampaignCrew` class
    - Sequential process: Discovery Task → Proposal Task → Outreach Task
    - `kickoff(brief_text: str, send: bool = False, approve_each: bool = False) -> dict`:
      1. Insert brand brief into AGENTS_DB, get brief_id
      2. Run Discovery, capture ranked creators JSON
      3. Insert campaign_suggestions rows
      4. Run Proposal on ranked creators
      5. Run Outreach on proposals with `send` flag and `brief_id`; if `approve_each`, prompt user Y/N per creator before sending
      6. Return summary dict: `{brief_id, creators_found, suggestions_saved, dms_attempted, dms_sent, dry_run: not send, total_tokens}`
    - Track total tokens across all LLM calls via `get_token_usage`; if `total_tokens > MAX_TOTAL_TOKENS_PER_RUN`, log warning but continue
    - Errors in any step logged; crew does not crash on single-creator failure
    - Must NOT include Negotiator/Contract in this flow
  Parallelization: Wave 5 | Blocked by: 11,12,13 | Blocks: 17
  References: CrewAI sequential process: https://docs.crewai.com/v1.15.1/en/learn/sequential-process
  Acceptance criteria:
    - `python -c "from crew import InfluencerCampaignCrew; c = InfluencerCampaignCrew(); print(type(c.crew))"` — Crew instance
    - Mock all agents and DB: `c.kickoff('test brief', send=False)` returns summary dict with `dry_run=True`, `dms_attempted >= 0`
    - Token tracking: summary contains `total_tokens` integer >= 0
  QA scenarios:
    - happy: full dry-run crew completes all 3 steps
    - failure: discovery returns invalid JSON → log error, proposal/outreach skipped
  Evidence: .omo/evidence/vernacular-creator-agents/task-16.txt
  Commit: Y | feat(crew): add sequential crew orchestration with token tracking

- [x] 17. CLI runner — `main.py`
  What to do / Must NOT do:
    - Argument parsing with argparse: `python main.py "brief text" [--send] [--approve-each] [--max-creators N] [--dry-run]`
    - Default is dry-run; `--send` required for real dispatch
    - `--approve-each` prompts before each real DM
    - Initialize Database; only initialize `InstagramClient` if `send=True`
    - Configure loguru: stdout + `data/run.log`, level from `LOG_LEVEL`
    - Call `InfluencerCampaignCrew().kickoff(...)` and print summary JSON
    - Must NOT call `login()` when `--send` is absent
  Parallelization: Wave 5 | Blocked by: 2,3,16 | Blocks: 19
  References: spec main.py, CLI section
  Acceptance criteria:
    - `python main.py --help` exits 0 and prints usage including `--send`, `--approve-each`
    - `python main.py "test brief"` runs dry-run and prints summary JSON without Instagram login
    - `python main.py "test brief" --send` requires valid IG credentials (documented in README)
  QA scenarios:
    - happy: dry-run CLI completes and prints JSON summary
    - failure: missing brief argument prints argparse error and exits 2
  Evidence: .omo/evidence/vernacular-creator-agents/task-17.txt
  Commit: Y | feat(cli): add main.py CLI with dry-run safety

### WAVE 6 — Scheduled runner + tests (parallel after Wave 5)

- [x] 18. Reply checker — `check_replies.py`
  What to do / Must NOT do:
    - `python check_replies.py [--dry-run] [--limit N]`
    - Process:
      1. Query `conversations` for status in ('outreach_sent','replied') and `last_message_count > 0` or thread_id set
      2. For each: call `read_thread_messages(thread_id)`
      3. Count messages; if count > `last_message_count`, new reply exists
      4. If new reply: run Negotiator agent; update conversation via `update_conversation_negotiation`
      5. If action='accept': run Contract agent; save contract
      6. Log received messages to dm_log
    - If `--dry-run`, do not call `read_instagram_threads`/`read_thread_messages`; use mocked/last-known data
    - Respect DM quota before sending any counter-offer
    - Output summary JSON: `{checked, new_replies, counter_offers_sent, accepted, contracts_generated}`
    - Must NOT crash if no conversations to check
  Parallelization: Wave 6 | Blocked by: 3,7,14,15,16 | Blocks: 19
  References: spec check_replies.py, spec CREW ORCHESTRATION steps 4-7
  Acceptance criteria:
    - `python check_replies.py --dry-run` exits 0 and prints summary
    - Mock DB with conversation `brief_id=1, last_message_count=2`; mock thread returns 3 messages → summary `new_replies=1`
    - `get_conversation_details` in Negotiator tool returns `raw_brief` for contract context
    - Quota exceeded: no counter-offer sent even if new reply exists
  QA scenarios:
    - happy: new reply detected, negotiator runs, contract generated on accept
    - failure: thread read error logs exception and continues
  Evidence: .omo/evidence/vernacular-creator-agents/task-18.txt
  Commit: Y | feat(sched): add check_replies.py for scheduled reply processing

- [x] 19. Test suite — `tests/test_discovery.py`, `tests/test_proposal.py`, `tests/test_outreach.py`, `tests/test_negotiator.py`, `tests/test_contract.py`, `tests/test_ig_client.py`, `tests/test_database.py`, `tests/test_crew.py`, `test_agents.py`
  What to do / Must NOT do:
    - `test_agents.py` runner imports and runs all test modules
    - `test_discovery.py`: mock scraper DB, assert fit score math, assert Discovery task output JSON shape
    - `test_proposal.py`: mock creator content tools, assert proposal JSON has campaign_ideas, suggested_budget
    - `test_outreach.py`: mock InstagramClient and quota; assert dry-run does NOT call send_dm; assert send=True calls send_dm; assert DM language matches creator language
    - `test_negotiator.py`: mock conversations and budget; assert budget overrun returns escalate; assert round 3 returns give_up
    - `test_contract.py`: mock conversation details; assert contract_text contains #ad/#sponsored and legal disclaimer
    - `test_ig_client.py`: mock instagrapi Client; assert delay between calls, assert lock, assert exception handling
    - `test_database.py`: use `:memory:` DB; assert all CRUD operations
    - `test_crew.py`: mock all agents; assert kickoff summary has required keys and total_tokens
    - All tests use pytest and pytest-mock; NO real network or LLM calls
  Parallelization: Wave 6 | Blocked by: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18 | Blocks: 20
  References: spec tests/ directory, pytest docs
  Acceptance criteria:
    - `pytest tests/ -v` exits 0 with all tests passed
    - `pytest tests/ --cov` (if pytest-cov installed) shows coverage >= 70%
    - `grep -r "print(" tests/` returns no results
  QA scenarios:
    - happy: full test suite passes
    - failure: a test with mocked bad data fails with clear assertion message
  Evidence: .omo/evidence/vernacular-creator-agents/task-19.txt
  Commit: Y | test(agents): add full test suite with mocked dependencies

### WAVE 7 — Documentation

- [x] 20. Documentation — `README.md`, `AGENTS.md`, `docs/research.md`
  What to do / Must NOT do:
    - `README.md`:
      - Project overview for a non-technical founder
      - Setup: clone, `pip install -r requirements.txt`, copy `.env.example` to `.env`, fill credentials
      - Usage: `python main.py "brief" --dry-run`, then `python main.py "brief" --send`
      - Safety: dry-run default, --approve-each, rate limits, session file permissions
      - Architecture ASCII diagram
    - `AGENTS.md`:
      - Each agent: role, goal, tools, input/output format, failure modes
      - Operational guidance: how to restart, how to handle Instagram challenges, how to read logs
    - `docs/research.md`:
      - CrewAI v1.15+ API summary with links
      - instagrapi session/DM best practices
      - Fireworks model IDs and pricing
      - ASCI disclosure requirements
    - Must NOT duplicate inline code comments at length
  Parallelization: Wave 7 | Blocked by: 19 | Blocks: —
  References: spec AGENTS.md, README.md, docs/research.md
  Acceptance criteria:
    - `wc -l README.md AGENTS.md docs/research.md` each >= 50 lines
    - `README.md` contains "--dry-run", "--send", "Fireworks", "instagrapi", "ASCI"
    - `AGENTS.md` contains names of all 5 agents
  QA scenarios:
    - happy: docs are readable and complete
    - failure: missing required section detected by grep
  Evidence: .omo/evidence/vernacular-creator-agents/task-20.txt
  Commit: Y | docs: add README, AGENTS.md, and research docs

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit — every todo's deliverable exists, matches spec scope, no scope creep, acceptance criteria are falsifiable
- [x] F2. Code quality review — `lsp_diagnostics` on all `.py` files (zero errors), `pytest tests/ -v` passes, `grep -r "print(" *.py` returns zero hits
- [x] F3. Real manual QA — run `python main.py "test brief" --dry-run`, verify JSON summary; run `python check_replies.py --dry-run`, verify summary
- [x] F4. Scope fidelity — no scraper logic, no web server, no Docker, no Celery, no multi-account rotation code; loguru used everywhere; session file permissions 0600

## Commit strategy
- One atomic commit per todo with conventional commit format: `type(scope): message`
- Types: feat, chore, test, docs, fix
- No squashing — each commit is independently verifiable
- Final wave produces no commits (verification only)

## Success criteria
1. `python main.py "I have a thali restaurant in Satellite, Ahmedabad. Want local food creators who speak Gujarati. Budget ₹15,000."` runs discovery → proposal → outreach in dry-run mode, prints summary JSON, logs to conversations table. No real DMs sent.
2. `python main.py "..." --send` dispatches real DMs via Instagram when valid IG credentials are set.
3. `python check_replies.py` reads new DM replies via `last_message_count`, negotiates within budget/round limits, generates contracts for accepted deals.
4. All instagrapi calls have proper exception handling and rate limiting — verified by `tests/test_ig_client.py`.
5. All DMs are in the creator's detected language — verified by `tests/test_outreach.py`.
6. All contracts include ASCI disclosure placeholders (#ad/#sponsored) and a "seek legal counsel" disclaimer — verified by `tests/test_contract.py`.
7. All logging uses loguru — `grep -r "print(" *.py` returns zero hits.
8. All LLM calls go through Fireworks AI — configurable via `.env` MODEL_* vars.
9. Models are swappable via `.env` without code changes.
10. Scraper data is read from external repo (SQLite path or HTTP API) — no scraping in this repo.
11. Total token usage per full dry-run campaign stays under `MAX_TOTAL_TOKENS_PER_RUN` (default 25K tokens, ~$2 at Fireworks rates) — verified by crew summary output.
12. `pytest tests/ -v` — all tests pass.
13. `lsp_diagnostics` on all `.py` files — zero errors.
