# multi-collab-dm-context - Work Plan

## TL;DR (For humans)

**What you'll get:** The system will correctly handle multiple collaborations with the same Instagram creator in the same DM thread — both sequential (one campaign finishes, then another starts) and simultaneous (two active campaigns at once). The AI Negotiator will know which campaign a creator's reply is about and negotiate accordingly.

**Why this approach:** Instagram DMs are 1:1 per (brand, creator) pair — one thread, no matter how many campaigns. Industry research (Tano.ai, Aspire, GRIN, CreatorIQ) shows all platforms use a creator-centric data model with metadata-tagged messages and human disambiguation. This design is the AI-native version: the LLM classifies which collab a reply belongs to using campaign context, instead of a human doing it. Validated by industry pattern; works WITH Instagram's unstructured DM nature rather than fighting it.

**What it will NOT do:** It will not mechanically split DM threads (fragile against Instagram API quirks). It will not block simultaneous collabs (both sequential and simultaneous are supported). It will not change the main outreach pipeline (Discovery → Proposal → Outreach) — only the reply-checking and negotiation flow.

**Effort:** 4 waves, ~12 todos. Schema migration + 4 new DB methods + check_replies.py refactor + Negotiator prompt enhancement + tests. No breaking changes — new columns are nullable, old behavior preserved when only 1 active conversation exists.

**Risk:** Medium. LLM classification accuracy on short/ambiguous replies ("ok", "yes") — mitigated by fallback to most recently active conversation. Instagram message ordering reliability — mitigated by using MAX(last_message_count) across all conversations sharing a thread.

**Gaps identified during Metis review (self-performed; Metis sub-agent did not complete):**
- **CRITICAL — last_message_count sync:** When the Negotiator classifies a reply as conversation B and updates B's `last_message_count`, conversation A (same thread) keeps its old count. Next cycle, A sees "new messages" that were already processed → duplicate processing. **Fix:** After processing, update `last_message_count` for ALL conversations in the thread group to the current thread message count, not just the classified one.
- **MEDIUM — campaign_label backfill:** Existing conversations have NULL `campaign_label`. **Fix:** Add a backfill in `_migrate()` that derives a label from the brand brief (first 60 chars of raw_brief) for existing rows where campaign_label IS NULL.
- **MEDIUM — reply about both campaigns:** Design says "classify as most recent" but doesn't specify Negotiator response. **Fix:** If the message references both campaigns, the Negotiator should address both in its response or ask for clarification.
- **LOW — NULL conversation_id in dm_history:** Existing dm_log entries have NULL conversation_id. **Fix:** Negotiator prompt includes instruction: "Messages with unattributed conversation_id are from older campaigns and provide general context."

**Decisions:**
- `dm_log.conversation_id` (nullable) links outbound DMs to conversations
- `conversations.campaign_label` (nullable) stores human-readable campaign name
- check_replies.py processes by thread_id group (creator-centric), not individual conversation rows
- Negotiator gets a CLASSIFY step before NEGOTIATE
- Single-collab shortcut: skip classification when only 1 active conversation (zero extra LLM cost)
- Pre-outreach check: non-blocking warning (doesn't prevent simultaneous collabs)

## Scope

**IN:**
- `db/schema.sql` — add `conversation_id` to dm_log, `campaign_label` to conversations
- `database.py` — migration entries, 4 new methods, updated `insert_dm_log` signature
- `tools/database_tools.py` — new @tool wrappers, updated `log_dm` signature
- `check_replies.py` — refactor main loop to process by thread group, enhanced `run_negotiator`
- `tools/instagram_tools.py` — `send_instagram_dm` passes conversation_id to `log_dm`
- `agents/activate/outreach_manager.py` — Negotiator prompt with classification step
- `agents/activate/contract_helper.py` — Contract agent gets campaign_label context
- `prompts/` — updated prompt files for Negotiator
- `tests/` — new test files for multi-collab scenarios

**OUT:**
- Main pipeline (main.py, crew.py, Discovery/Proposal/Outreach agents) — not changed
- Instagram API integration (ig_client.py) — not changed
- Contract generation logic — only prompt context enhanced
- No new CLI flags or commands

**Must-NOT-Have:**
- NO mechanical message-position tracking (fragile against Instagram API)
- NO blocking of simultaneous collabs (both sequential + simultaneous supported)
- NO changes to the main outreach pipeline flow
- NO `print()` — use `logger.info()` / `logger.error()` from loguru
- NO bare `except:` — always catch specific exceptions
- NO hardcoded secrets — all via .env

## Verification strategy

All tests mocked (no real network/LLM), consistent with existing test patterns (pytest + pytest-mock, `:memory:` DB). Each todo includes agent-executable happy + failure QA scenarios with evidence paths.

TDD approach: tests written alongside implementation in each wave. Existing 291 tests must still pass.

## Execution strategy

4 sequential waves with dependencies:
1. **Wave 1 (Schema + DB)** — foundation; all other waves depend on this
2. **Wave 2 (Outreach Enhancement)** — depends on Wave 1; can run in parallel with Wave 3
3. **Wave 3 (check_replies Refactor)** — depends on Wave 1; the core logic change
4. **Wave 4 (Tests)** — depends on Waves 1-3; comprehensive multi-collab test coverage

## Todos

### Wave 1: Schema + Database Layer

#### Todo 1.1: Add conversation_id and campaign_label columns to schema + migration

**References:**
- `db/schema.sql:21-35` (conversations table) — add `campaign_label TEXT DEFAULT NULL` after `agreed_rate`
- `db/schema.sql:51-58` (dm_log table) — add `conversation_id INTEGER REFERENCES conversations(id)` after `thread_id`
- `database.py:38-45` (`_migrate` method) — add ALTER TABLE statements for both new columns, following the existing `reminder_count` pattern

**Acceptance criteria:**
- `db/schema.sql` has `campaign_label TEXT DEFAULT NULL` in conversations table
- `db/schema.sql` has `conversation_id INTEGER REFERENCES conversations(id)` in dm_log table
- `_migrate()` checks for existing columns before adding (PRAGMA table_info pattern, same as `reminder_count`)
- Fresh `init_db()` creates tables with new columns
- Existing database with old schema migrates successfully (ALTER TABLE adds columns)
- `:memory:` database works correctly with new columns

**Happy QA:** `python -c "from database import Database; db = Database(':memory:'); db.init_db(); print('OK')"` — exits 0, prints OK
**Failure QA:** Verify migration on a pre-existing database file — `ALTER TABLE` should not fail if column already exists (idempotent check via PRAGMA table_info)
**Commit:** `feat(db): add conversation_id to dm_log and campaign_label to conversations`

#### Todo 1.2: Add new Database methods for creator-centric queries

**References:**
- `database.py:94-200` (existing conversation methods) — add new methods after `increment_reminder_count`
- `database.py:256-266` (`get_conversation_details` JOIN pattern) — follow same JOIN pattern for `get_active_conversations_by_creator`
- `database.py:236-245` (`insert_dm_log`) — update signature to accept `conversation_id` parameter

**Acceptance criteria:**
- `get_active_conversations_by_creator(creator_username: str) -> list[dict]` — returns conversations with status IN ('outreach_sent', 'replied', 'negotiating', 'accepted'), each JOINed with brand_briefs to include raw_brief + parsed_brief + campaign_label
- `get_dm_log_by_creator(creator_username: str, limit: int = 50) -> list[dict]` — returns dm_log entries for a creator, including conversation_id column
- `get_conversations_by_thread_id(thread_id: str) -> list[dict]` — returns all conversations sharing a thread_id
- `sync_thread_message_count(thread_id: str, message_count: int) -> bool` — updates `last_message_count` for ALL conversations sharing a thread_id to prevent duplicate processing (critical gap fix)
- `insert_dm_log(...)` updated to accept optional `conversation_id: Optional[int] = None` parameter, stores it in the new column
- All methods use `self._connect()` context manager pattern, return `dict` / `list[dict]`
- All methods handle empty results gracefully (return empty list or None)

**Happy QA:** `python -c "from database import Database; db = Database(':memory:'); db.init_db(); bid = db.insert_brief('test'); cid = db.insert_conversation(bid, 'user1', 'thread1', 'outreach_sent'); print(db.get_active_conversations_by_creator('user1'))"` — returns list with 1 conversation containing raw_brief
**Failure QA:** `db.get_active_conversations_by_creator('nonexistent')` — returns empty list, no exception
**Commit:** `feat(db): add creator-centric query methods for multi-collab context`

#### Todo 1.3: Add @tool wrappers in database_tools.py + update log_dm

**References:**
- `tools/database_tools.py:39-54` (`set_database`, `_get_db` pattern)
- `tools/database_tools.py:61-81` (`save_conversation` @tool pattern) — follow for new tools
- `tools/database_tools.py:224-238` (`log_dm` @tool) — update to accept `conversation_id` parameter
- `tools/database_tools.py:174-178` (`get_conversation_details` @tool) — follow pattern for `get_active_conversations_by_creator`

**Acceptance criteria:**
- New `@tool` function `get_active_conversations(creator_username: str) -> list` — wraps `db.get_active_conversations_by_creator`
- New `@tool` function `get_dm_history(creator_username: str, limit: int = 50) -> list` — wraps `db.get_dm_log_by_creator`
- New `@tool` function `get_conversations_by_thread(thread_id: str) -> list` — wraps `db.get_conversations_by_thread_id`
- `log_dm` updated to accept optional `conversation_id: int = None` parameter, passes to `db.insert_dm_log`
- `save_conversation` updated to accept optional `campaign_label: str = None` parameter, passes to `db.insert_conversation`
- All new tools have docstrings (CrewAI requires docstrings for @tool functions)
- All tools follow existing `_get_db()` pattern for database access

**Happy QA:** `python -c "from tools.database_tools import set_database, get_active_conversations; from database import Database; db = Database(':memory:'); db.init_db(); set_database(db); print(get_active_conversations('user1'))"` — returns list
**Failure QA:** Call `get_active_conversations('nonexistent')` — returns empty list
**Commit:** `feat(tools): add creator-centric @tool wrappers, update log_dm with conversation_id`

### Wave 2: Outreach Enhancement

#### Todo 2.1: Update send_instagram_dm to pass conversation_id to log_dm

**References:**
- `tools/instagram_tools.py:95-111` (`read_thread_messages`) — nearby send function
- `tools/database_tools.py:224-238` (`log_dm`) — updated in Todo 1.3 to accept conversation_id
- `tools/instagram_tools.py` — find `send_instagram_dm` function, update its `log_dm` call to include conversation_id

**Acceptance criteria:**
- `send_instagram_dm` accepts optional `conversation_id` parameter
- When `conversation_id` is provided, it's passed to `log_dm(creator_username=..., thread_id=..., message_text=..., direction='sent', conversation_id=conversation_id)`
- When `conversation_id` is None (backward compat), `log_dm` is called without it (existing behavior)
- No change to the DM sending logic itself — only the logging

**Happy QA:** Unit test: mock `get_ig_client`, call `send_instagram_dm(username='user1', message='hi', conversation_id=5)` — verify `log_dm` called with `conversation_id=5`
**Failure QA:** Call without conversation_id — verify `log_dm` called with `conversation_id=None`, no exception
**Commit:** `feat(tools): pass conversation_id to log_dm when sending outreach DMs`

#### Todo 2.2: Add pre-outreach awareness check + campaign_label extraction

**References:**
- `tools/database_tools.py` — add new `@tool` function `check_existing_conversations`
- `database.py` — `get_active_conversations_by_creator` (from Todo 1.2) used internally
- `tools/database_tools.py:148-167` (`get_brand_brief`, `get_brand_budget`) — pattern for extracting data from parsed_brief JSON
- `agents/activate/outreach_manager.py` — Outreach agent prompt, add awareness check

**Acceptance criteria:**
- New `@tool` function `check_existing_conversations(creator_username: str) -> list` — returns active conversations for a creator (wraps `get_active_conversations_by_creator`)
- When active conversations exist, the Outreach agent logs a warning: `logger.warning("Creator @{username} already has {N} active conversation(s): {campaign_labels}")`
- `campaign_label` extraction: when `save_conversation` is called, extract a short label from the brand brief (first 50 chars of raw_brief, or product name from parsed_brief if available)
- The awareness check is non-blocking — it logs a warning but does NOT prevent outreach

**Happy QA:** Unit test: insert 1 active conversation for 'user1', call `check_existing_conversations('user1')` — returns list with 1 item
**Failure QA:** Call `check_existing_conversations('never_contacted')` — returns empty list, no exception
**Commit:** `feat(tools): add pre-outreach awareness check and campaign_label extraction`

#### Todo 2.3: Enhance outreach prompt to include campaign label

**References:**
- `prompts/` directory — find outreach-related prompt files
- `agents/activate/outreach_manager.py` — Outreach agent definition and task description
- `agents/_base.py` — shared utilities for prompt parsing

**Acceptance criteria:**
- Outreach agent prompt instructs the LLM to explicitly name the campaign in the first sentence of every outreach DM
- When a creator has existing active conversations, the prompt instructs acknowledging the prior relationship (e.g., "We loved working with you on the {previous_campaign_label}...")
- Prompt includes instruction to reference campaign_label from the conversation context
- No change to the overall outreach pipeline flow — only prompt content

**Happy QA:** Verify prompt file contains campaign-naming instruction by reading the file
**Failure QA:** Verify prompt file is valid (no syntax errors in prompt template)
**Commit:** `feat(prompts): enhance outreach DM to include campaign label reference`

### Wave 3: check_replies.py Refactor

#### Todo 3.1: Refactor get_candidate_conversations to group by thread_id

**References:**
- `check_replies.py:95-111` (`get_candidate_conversations`) — refactor to group by thread_id
- `database.py` — `get_conversations_by_thread_id` (from Todo 1.2)
- `check_replies.py:100` — current `db.get_conversations_by_statuses(("outreach_sent", "replied"))` — keep this, add grouping

**Acceptance criteria:**
- `get_candidate_conversations` returns a list of thread groups: `[{thread_id, conversations: [...], creator_username}]`
- Each group contains all conversations sharing the same thread_id
- Conversations with NULL thread_id are grouped individually (one per conversation)
- Limit parameter still works (limits number of thread groups, not conversations)
- Backward compatible: if only 1 conversation per thread, behavior is same as before

**Happy QA:** Unit test: insert 2 conversations with same thread_id, call `get_candidate_conversations(db)` — returns 1 group with 2 conversations
**Failure QA:** Insert 0 conversations — returns empty list, no exception
**Commit:** `refactor(check_replies): group candidate conversations by thread_id`

#### Todo 3.2: Refactor main loop to process by thread group

**References:**
- `check_replies.py:302-407` (main loop) — refactor to iterate thread groups instead of individual conversations
- `check_replies.py:114-130` (`check_for_new_replies`) — update to use MAX(last_message_count) across all conversations in the group
- `database.py` — `get_active_conversations_by_creator`, `get_dm_log_by_creator` (from Todo 1.2)

**Acceptance criteria:**
- Main loop iterates over thread groups (not individual conversations)
- For each group: reads thread ONCE via `read_thread_messages(thread_id)`
- New message detection uses `max(c["last_message_count"] for c in group_conversations)` as the baseline
- Only processes new messages if `current_count > max_processed_count`
- Fetches active conversations for the creator via `get_active_conversations_by_creator`
- Fetches DM history via `get_dm_log_by_creator`
- Passes all context to `run_negotiator`
- After Negotiator returns, updates the SPECIFIC conversation identified by `classified_conversation_id`
- **CRITICAL:** After processing, calls `sync_thread_message_count(thread_id, current_count)` to update `last_message_count` for ALL conversations in the thread group — prevents duplicate processing on next cycle (gap fix)
- Logs received messages to dm_log with the classified conversation_id
- Summary output still works (checked, new_replies, counter_offers_sent, accepted, contracts_generated)

**Happy QA:** Unit test: 1 thread group with 1 conversation, 1 new message — processes correctly, updates conversation status
**Failure QA:** 1 thread group with 0 new messages — skips processing, logs "No new replies"
**Commit:** `refactor(check_replies): process by thread group for multi-collab support`

#### Todo 3.3: Refactor run_negotiator with enhanced prompt (classification + negotiation)

**References:**
- `check_replies.py:141-212` (`run_negotiator`) — refactor to accept full context
- `agents/activate/outreach_manager.py` — Negotiator agent definition
- `prompts/` — Negotiator prompt files

**Acceptance criteria:**
- `run_negotiator` signature updated to accept: `message_text`, `active_conversations` (list of dicts), `dm_history` (list of dicts), `creator_username`, `dry_run`
- Task description includes ALL active campaigns with their: campaign_label, raw_brief (truncated), status, agreed_rate, negotiation_history (truncated), conversation_id
- Task description includes DM history with conversation_id tags
- Task description includes the new message text
- CLASSIFY step in prompt: "Which campaign is this message about?"
- NEGOTIATE step: "Based on the classified campaign, decide next action"
- Returns JSON with: `classified_conversation_id`, `classification_confidence` (high/medium/low), `action`, `response`, `agreed_rate`, `round_number`, `status`
- When only 1 active conversation: skip classification, set `classified_conversation_id` to that conversation's id, `classification_confidence` = "high"
- Dry-run mode: returns same shape with `classified_conversation_id` set to the single active conversation (or most recent if multiple)
- JSON parsing fallback: if parse fails, returns `classified_conversation_id` = most recent conversation's id, `action` = "wait"

**Happy QA:** Unit test (mocked LLM): 2 active conversations, LLM returns classification for conversation A — verify `classified_conversation_id` = A's id
**Failure QA:** Unit test (mocked LLM returns invalid JSON): verify fallback returns most recent conversation's id, action="wait"
**Commit:** `feat(check_replies): enhance Negotiator with classification + negotiation prompt`

### Wave 4: Tests

#### Todo 4.1: Tests for new DB methods + schema migration

**References:**
- `tests/` directory — existing test patterns
- `database.py` — new methods from Todo 1.2
- `db/schema.sql` — new columns from Todo 1.1

**Acceptance criteria:**
- `test_dm_log_has_conversation_id` — verify column exists, nullable, stores correctly
- `test_conversations_has_campaign_label` — verify column exists, nullable, stores correctly
- `test_get_active_conversations_by_creator` — returns correct conversations, JOINed with briefs
- `test_get_dm_log_by_creator` — returns DM log entries with conversation_id
- `test_get_conversations_by_thread_id` — returns all conversations sharing a thread
- `test_insert_dm_log_with_conversation_id` — stores conversation_id correctly
- `test_migration_idempotent` — running _migrate() twice doesn't fail
- All tests use `:memory:` database, no real network/LLM

**Happy QA:** `python -m pytest tests/test_multi_collab_db.py -v` — all tests pass
**Failure QA:** Run tests against old schema (no new columns) — migration adds columns, tests pass
**Commit:** `test(db): add tests for multi-collab schema and DB methods`

#### Todo 4.2: Tests for multi-collab classification flow

**References:**
- `check_replies.py` — refactored main loop from Todo 3.2, `run_negotiator` from Todo 3.3
- `tests/` — existing test patterns with pytest-mock

**Acceptance criteria:**
- `test_single_collab_unchanged_behavior` — 1 active conversation, classification skipped, old behavior preserved
- `test_multi_collab_classification` — 2 active conversations, mocked LLM classifies reply to correct one
- `test_ambiguous_reply_defaults_to_recent` — short reply ("ok"), defaults to most recently active conversation
- `test_new_message_detection_uses_max_count` — reply to collab A doesn't trigger collab B's new-reply detection
- `test_thread_group_processing` — 2 conversations in same thread, processed as one group
- `test_classified_conversation_id_updates_correct_conversation` — Negotiator returns conversation B's id, only B is updated
- `test_invalid_classified_id_falls_back` — LLM returns nonexistent id, falls back to most recent
- `test_llm_json_parse_failure_fallback` — LLM returns invalid JSON, fallback returns "wait" + most recent id
- `test_thread_message_count_synced_across_group` — after processing, ALL conversations in thread group have updated last_message_count (critical gap fix)
- `test_reply_about_both_campaigns` — message references both campaigns, Negotiator addresses both or asks for clarification
- All tests mocked (no real network/LLM)

**Happy QA:** `python -m pytest tests/test_multi_collab_classification.py -v` — all tests pass
**Failure QA:** `python -m pytest tests/ -v` — all 291 existing tests still pass
**Commit:** `test(check_replies): add multi-collab classification flow tests`

#### Todo 4.3: Tests for pre-outreach check + campaign_label

**References:**
- `tools/database_tools.py` — `check_existing_conversations` from Todo 2.2
- `tools/instagram_tools.py` — `send_instagram_dm` from Todo 2.1

**Acceptance criteria:**
- `test_pre_outreach_warning_logged` — creator with active conversation, verify warning logged
- `test_pre_outreach_no_warning_for_new_creator` — creator with no active conversations, no warning
- `test_campaign_label_extraction` — verify label extracted from brand brief
- `test_campaign_label_in_dm_log` — verify conversation_id stored in dm_log when sending DM
- `test_send_dm_with_conversation_id` — verify log_dm called with correct conversation_id
- `test_send_dm_without_conversation_id` — backward compat, log_dm called with None
- All tests mocked (no real network/LLM)

**Happy QA:** `python -m pytest tests/test_pre_outreach.py -v` — all tests pass
**Failure QA:** Run full test suite — `python -m pytest tests/ -v` — all tests pass
**Commit:** `test(tools): add pre-outreach awareness and campaign_label tests`

## Final verification wave

Runs in parallel after ALL todos complete. ALL must APPROVE:

- **F1 Plan compliance audit:** Every todo's acceptance criteria met. Every file in the design changed. No file outside scope touched. Verify via `git diff --stat` against the plan's file list.
- **F2 Code quality review:** No `print()`, no bare `except:`, no stdlib `logging`, all loguru. No hardcoded secrets. Follow existing `_Tool` pattern. Run `python -m pytest tests/ -v` — all tests pass including existing 291.
- **F3 Real manual QA:** `python check_replies.py --dry-run` exits 0 with summary output. `python main.py "test brief" ` (dry-run) exits 0. Verify no import errors.
- **F4 Scope fidelity:** No changes to main.py, crew.py, ig_client.py, llm_client.py, config.py. No new CLI flags. No new dependencies in requirements.txt.

## Commit strategy

One commit per todo (12 commits total). Each commit message follows conventional commits format:
- `feat(db):` for database/schema changes
- `feat(tools):` for tool wrappers
- `refactor(check_replies):` for check_replies.py changes
- `feat(check_replies):` for new Negotiator logic
- `feat(prompts):` for prompt changes
- `test(...)` for test files

Branch: `feature/multi-collab-dm-context`

## Success criteria

1. When a creator has 2 active campaigns in the same DM thread, the Negotiator correctly classifies which campaign each reply belongs to
2. When only 1 active conversation exists, behavior is unchanged from current (zero extra LLM cost)
3. When the LLM is uncertain, it defaults to the most recently active conversation and includes the campaign name in its response
4. All 291 existing tests pass
5. All new multi-collab tests pass
6. `python check_replies.py --dry-run` works without errors
7. No breaking changes — existing conversations with NULL conversation_id in dm_log are handled gracefully
