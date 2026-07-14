---
slug: vernacular-creator-agents
status: drafting
intent: clear
review_required: true
pending-action: write .omo/plans/vernacular-creator-agents.md
approach: Build a pure-Python CLI CrewAI crew with five agents (discovery, proposal, outreach, negotiator, contract) backed by Fireworks AI LLMs and a local SQLite state DB; integrate to an external scraper repo via SQLite or HTTP; send/read Instagram DMs through instagrapi with session persistence, rate limiting, and dry-run safety.
---

# Draft: vernacular-creator-agents

[Updated: plan written at .omo/plans/vernacular-creator-agents.md]

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
| id | outcome | status | evidence path |
| --- | --- | --- | --- |
| C1 | Project bootstrap: repo layout, env, deps, gitignore | active | `.env.example`, `requirements.txt`, `README.md`, `.gitignore` |
| C2 | Configuration + LLM client for Fireworks | active | `config.py`, `llm_client.py` |
| C3 | SQLite state database schema and CRUD | active | `db/schema.sql`, `database.py` |
| C4 | instagrapi wrapper with sessions, DMs, threads, exceptions, rate limiting | active | `ig_client.py` |
| C5 | Scraper integration (SQLite path + HTTP API) | active | `tools/scraper_tools.py` |
| C6 | CrewAI tools layer | active | `tools/*.py` |
| C7 | Five CrewAI agents | active | `agents/*.py` |
| C8 | Crew orchestration + CLI runners | active | `crew.py`, `main.py`, `check_replies.py` |
| C9 | Test suite | active | `tests/*.py`, `test_agents.py` |
| C10 | Documentation | active | `AGENTS.md`, `README.md`, `docs/research.md` |

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
| assumption | adopted default | rationale | reversible? |
| --- | --- | --- | --- |
| Fireworks model IDs in `.env.example` | Use actual Fireworks paths: `glm-5p2`, `qwen3p7-plus`; keep deepseek-v4-pro as-is | Fireworks UI lists `glm-5p2` and `qwen3p7-plus`; user wrote `glm-5.2`/`qwen3.7-plus` as aliases | yes via `.env` |
| Real-time MQTT reply detection | Deferred to post-MVP TODO | Marked optional by user; scheduled polling is simpler and safer | yes later |
| Multi-account rotation | Single account + env placeholders for backups; rotation logic deferred | User mentioned backups but single account in `.env.example`; rotation adds scope | yes later |
| Proxy support | `cl.set_proxy()` wired from env, but no proxy required for local dev | Production best practice; can be empty in dev | yes via `.env` |

## Findings (cited - path:lines)
- CrewAI v1.15+ supports both direct `Agent`/`Task`/`Crew` classes and the newer annotation/JSON-first `crewai create crew` style. The proposed repo uses direct classes, which is still supported and matches the user's spec.
- `@tool` decorator is the simplest CrewAI custom-tool pattern; accepts docstring as description and type hints for schema. BaseTool subclassing is an alternative.
- Custom LLM with Fireworks: CrewAI `LLM(model="fireworks/...", api_key=..., base_url=...)` is the expected pattern, or pass an `OpenAI` client wrapper.
- instagrapi session persistence is critical: `load_settings()` must run **before** `login()`; otherwise device fingerprints regenerate and Instagram triggers `challenge_required`. Re-login should reuse dumped settings.
- instagrapi is **not thread-safe** and Instagram flags parallel requests from one session; plan must enforce serial-per-account execution and a single `Client` instance with locks.
- Fireworks pricing confirms GLM 5.2 ($1.40/$4.40 per 1M), Qwen3.7 Plus ($0.40/$1.60), DeepSeek-V4 Pro ($1.74/$3.48). Budget target of <$2/run is feasible with short prompts and the specified cheap models for bulk tasks.
- ASCI guidelines require disclosure labels (#Ad, #Sponsored, #Collaboration, #Partnership, #Free gift, etc.) for any material connection (money, free product, barter, discount, trip, gift). Disclosure must be upfront, prominent, and in English or the language of the advertisement. Contracts must include disclosure clauses.

## Decisions (with rationale)
- Decision: Keep the project as a pure Python CLI (no web server, no Docker, no Celery) — matches user constraints.
- Decision: SQLite WAL mode for `agents.db` — matches user spec, simple, reliable.
- Decision: Separate scraper data source: read-only from `SCRAPER_DB_PATH` SQLite or `SCRAPER_API_URL` HTTP — no scraping in this repo.
- Decision: Use loguru for all logging, never print — matches user constraint.
- Decision: qwen3.7-plus (Fireworks path `qwen3p7-plus`) for Gujarati/Hindi generation — matches user research.

## Scope IN
- All 5 agents (Discovery, Proposal, Outreach, Negotiator, Contract) with the tools/processes specified.
- SQLite schema for `brand_briefs`, `campaign_suggestions`, `conversations`, `contracts`, `dm_log`.
- instagrapi DM send/read with session persistence, challenge handling, rate limiting, exception handling.
- Fireworks LLM integration via OpenAI-compatible SDK, models swappable via `.env`.
- CLI: `main.py` for brief→discover→propose→outreach, `check_replies.py` for scheduled reply→negotiate→contract.
- Test suite with mocked Instagram and LLM clients.
- ASCI-compliant contract clauses.

## Scope OUT (Must NOT have)
- No Instagram scraping or follower harvesting in this repo.
- No web frontend, FastAPI server, Docker, Celery.
- No real-time MQTT reply detection in MVP (documented as future TODO).
- No multi-account rotation logic in MVP (documented as future TODO).
- No payment gateway integration.

## Open questions
<!-- Owner-decision forks survive here until answered. -->
1. DM safety mode: Should `main.py` default to a dry-run that prints DMs without sending, requiring an explicit `--send` flag for real Instagram dispatch? (Recommended: yes — prevents accidental unsolicited outreach.)
2. Human approval gate: Should an `--approve-each` flag prompt for per-creator confirmation before every real DM send? (Recommended: opt-in flag for cautious production use.)
3. Scraper integration scope: Implement both SQLite-path and HTTP-API integrations now, or only SQLite for MVP with HTTP as an extension point? (Recommended: both now; HTTP mode is a thin abstraction over SQLite mode and future-proofs the scraper repo.)

## Last Metis findings (folded into plan)
<!-- F1-F12 from gap analysis. Critical items promoted to Scope/Acceptance. -->

## Approval gate
status: approved
review_round: 2-complete
momus_verdict: APPROVE
oracle_verdict: APPROVE
approach-verified: answers received for all 3 questions (1=yes, 2=recommended, 3=recommended)
fixes_applied_round_1:
  - Renumbered and merged todos; removed stub tasks 9/10
  - Added concrete acceptance criteria and happy/failure QA to every todo
  - Rewrote dependency matrix to match todo IDs and crew flow
  - Added get_brand_brief and update_conversation_negotiation tools
  - Added conversations.last_message_count column for reply detection
  - Added randomized delay (3-8s) and DM_DELAY_JITTER env var
  - Added MAX_TOKENS_PER_AGENT and MAX_TOTAL_TOKENS_PER_RUN config and acceptance criteria
  - Made CLI importable/testable without InstagramClient init in dry-run mode
fixes_applied_round_2:
  - Aligned dependency matrix: Wave 4 agents parallel, crew orchestration blocks CLI/reply checker
  - Fixed calculate_fit_score to use estimated_rate(creator) instead of undefined suggested_rate
  - Added brief_id column to conversations table and all insert/update/tool paths
  - Added get_conversation_details acceptance criterion verifying brand_brief join
review_receipts:
  momus_session: ses_0a37eedd8ffeti8TjI0wnmUBur
  oracle_session: ses_0a38193b8ffe7bwTPhG4fjm7oP
  summary: Both reviewers verified all round-1 and round-2 blockers are resolved. Plan is decision-complete.
accepted-scope-decisions:
  DM safety mode: dry-run default, --send required for real dispatch
  Per-DM human approval: --approve-each available as opt-in flag
  Scraper integration: both SQLite-path and HTTP-API modes
  All DM operations execute serially on one Client instance with lock
  Credential/session files use 0600 permissions, outside repo by default
  Rate limiting: 20 DMs/day (env-configurable), randomized 3-8s delay between calls
  Cost: full dry-run under 25K tokens / ~$2 with logged token counts
  ACSI scope: template includes disclosure placeholders, not legal review
  Multi-account rotation: deferred, env vars as comments only
