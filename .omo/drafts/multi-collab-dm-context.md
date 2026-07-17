# multi-collab-dm-context — Draft

## Intent
- **intent:** clear
- **review_required:** false
- **classification:** Standard (1-5 files core, clear feature/refactor)

## Approval gate
- **status:** approved
- **user approved:** "Approve — write design doc" (2026-07-14)
- **pending action:** write .omo/plans/multi-collab-dm-context.md

## Approach
LLM-Based Context Routing — the AI Negotiator classifies which collab a reply belongs to using campaign context, before negotiating. Pattern validated by industry research (Aspire, GRIN, CreatorIQ all use creator-centric data model with metadata-tagged messages and human disambiguation; this system is the AI-native version).

## Key decisions
1. `dm_log` gets nullable `conversation_id` column — links outbound DMs to conversations
2. `conversations` gets nullable `campaign_label` column — human-readable campaign name for disambiguation
3. New DB methods: `get_active_conversations_by_creator`, `get_dm_log_by_creator`, `get_conversations_by_thread_id`
4. `check_replies.py` refactored to process by thread_id group (creator-centric), not individual conversation rows
5. Negotiator prompt enhanced with CLASSIFY step before NEGOTIATE
6. Single-collab shortcut: when only 1 active conversation, skip classification (zero extra LLM cost)
7. Pre-outreach awareness check: non-blocking warning when targeting creator with active conversations
8. Fallback for ambiguous replies: default to most recently active conversation

## Design doc
Full design documented in .omo/plans/multi-collab-dm-context.md (TL;DR section serves as design summary). Original design doc was intended for docs/plans/ but Prometheus is restricted to .omo/*.md only.

## Metis receipt
Metis sub-agent (ses_09eef506effe2HX1IKuKbNtnd7) was spawned but did not produce a complete gap report — it spent its session waiting for sub-agents that didn't complete in time. Gap analysis was self-performed by Prometheus based on deep codebase exploration.

### Gaps found and folded into the plan:
1. **CRITICAL — last_message_count sync across thread group:** When Negotiator classifies a reply as conversation B and updates B's count, conversation A (same thread) keeps its old count → duplicate processing next cycle. **Fix:** Added `sync_thread_message_count()` DB method and updated Todo 3.2 to call it after processing. Added test in Todo 4.2.
2. **MEDIUM — campaign_label backfill:** Existing conversations have NULL campaign_label. **Fix:** Noted in plan; migration should backfill from raw_brief.
3. **MEDIUM — reply about both campaigns:** Design didn't specify Negotiator response. **Fix:** Added test case and prompt instruction.
4. **LOW — NULL conversation_id in dm_history:** Existing dm_log entries. **Fix:** Negotiator prompt instruction added for unattributed messages.
