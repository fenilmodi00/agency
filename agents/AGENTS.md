# agents/ — CrewAI Agent Definitions

Five agents, each in its own file. Discovery and Proposal run in the main crew pipeline (`crew.py`). Negotiator and Contract run separately via `check_replies.py` when creators reply to outreach DMs.

`__init__.py` is empty. It exists so the directory is importable as a package.

## WHERE TO LOOK

| File | Role | Model Config | Tools | Output Shape |
|------|------|-------------|-------|-------------|
| `discovery.py` | Creator Discovery Specialist | `MODEL_DISCOVERY` | `query_creators`, `get_creator_details`, `calculate_fit_score` | JSON array: `[{username, fit_score, match_reason}]` sorted by fit_score desc |
| `proposal.py` | Proposal Strategist | `MODEL_PROPOSAL` | `get_creator_content_summary`, `get_creator_recent_posts` | JSON array: `[{creator_username, campaign_ideas, deliverables, suggested_budget, timeline, notes}]` |
| `outreach.py` | Vernacular Creator Outreach Specialist | `MODEL_OUTREACH` | `send_instagram_dm`, `get_creator_language`, `save_conversation`, `log_dm`, `check_dm_quota` | JSON: `{results: [{username, thread_id, language, message, sent, dry_run}], quota_exceeded}` |
| `negotiator.py` | Rate Negotiator | `MODEL_NEGOTIATOR` | `read_instagram_threads`, `read_thread_messages`, `send_instagram_dm`, `get_conversation_history`, `update_conversation_negotiation`, `get_brand_budget`, `check_dm_quota`, `log_dm` | JSON: `{action, response, agreed_rate, round_number, status}` |
| `contract.py` | Contract Drafter | `MODEL_CONTRACT` | `get_conversation_details`, `get_brand_brief`, `save_contract` | JSON: `{contract_text, gujarati_summary, contract_type, deliverables, usage_rights, timeline, asci_compliant}` |

## CONVENTIONS

- **Factory pattern**: every file exports `get_*_agent()` returning a CrewAI `Agent`. Discovery, Proposal, and Outreach also export `get_*_task()`. Negotiator and Contract are task-less. Their tasks are built inline by `check_replies.py`.
- **Prompts from files**: `discovery.py` and `negotiator.py` load role/goal/backstory from `prompts/*.txt` via `Path.read_text()`. `outreach.py` uses an inline `OUTREACH_PROMPT` template with `.format()` placeholders for `send` and `brief_id`. `proposal.py` and `contract.py` hardcode role/goal/backstory strings directly.
- **Tool wrapping**: `discovery.py` and `proposal.py` wrap raw scraper/calc functions with `@tool` to produce CrewAI-compatible `BaseTool` instances. Outreach, Negotiator, and Contract import pre-wrapped tools directly from `tools/`.
- **`send` flag on outreach**: `get_outreach_agent(send=False)` controls whether the agent can call `send_instagram_dm`. Default is dry-run. The flag is baked into the prompt template as `SEND_MODE`.
- **All agents set `verbose=True` and `allow_delegation=False`**. Contract agent also sets `max_iter=5`.

## ANTI-PATTERNS

- **No direct DB writes.** Agents must never import `database.py` or call `Database` methods. All persistence goes through `tools/database_tools.py` functions (`save_conversation`, `log_dm`, `save_contract`, `update_conversation_negotiation`).
- **No direct Instagram access.** Agents must never import `ig_client.py`. All Instagram interaction goes through `tools/instagram_tools.py` functions (`send_instagram_dm`, `read_instagram_threads`, `read_thread_messages`).
- **No cross-agent imports.** Agents don't call each other's factories. Orchestration happens in `crew.py` and `check_replies.py`.
- **No inline prompt editing.** Discovery and Negotiator prompts live in `prompts/*.txt`. Don't hardcode their role/goal/backstory in the agent file. Edit the prompt file instead.
