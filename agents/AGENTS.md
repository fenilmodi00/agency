# agents/ — STAR Framework Agents

24 agents: 16 execution agents across 4 phases (4 each) + 8 protocol registry agents. All use `agents/_base.py` for Agent/Task stubs, tool decorator fallback, and prompt-section parsing.

## PHASES (execution order in `crew.py::StarCrew`)

| Phase | Dir | Agents (run sequentially) | Goal |
|-------|-----|---------------------------|------|
| 1 Scout | `scout/` | audience_mapper → trend_spotter → influencer_discovery → fit_scorer | Find + rank regional creators from the scraper DB |
| 2 Target | `target/` | competitor_tracker → campaign_planner → brief_generator → budget_optimizer | Tailored campaign ideas + budget per creator |
| 3 Activate | `activate/` | outreach_manager → creator_content_auditor → contract_helper → content_amplifier | Vernacular DM outreach, negotiation, contracts |
| 4 Report | `report/` | landing_optimizer → performance_analyzer → roi_calculator → report_generator | Campaign analytics and ROI |

Each sub-agent runs as its own `Crew(agents=[agent], tasks=[task], process=sequential)`. Results pass between phases via `StarCrew._phase_results`.

## PROTOCOL REGISTRY (`protocol/`)

8 agents managing system state and routing — called within phases, not pipeline stages:
channel_registry, consent_registry, creator_registry, entity_registry, launch_registry, memory_management, narrative_registry, offer_claims_registry.
Backed by `tools/registry_tools.py` → subprocess to `marketing-skills/scripts/registry-events.py`.

## BACKWARD-COMPAT SHIMS (root of agents/)

| Shim | Re-exports from |
|------|-----------------|
| `discovery.py` | `scout/influencer_discovery.py` |
| `proposal.py` | `target/campaign_planner.py` |
| `outreach.py` | `activate/outreach_manager.py` |
| `negotiator.py` | `activate/outreach_manager.py` |
| `contract.py` | `activate/contract_helper.py` |

Keep shims working — legacy tests (`test_discovery.py`, `test_proposal.py`, `test_outreach.py`, `test_negotiator.py`, `test_contract.py`, `test_shim_compat.py`) import them.

## CONVENTIONS

- **Prompts live in `prompts/<agent>_prompt.txt`** with strict JSON output schemas; parsed via `_base.py`.
- **No direct DB/IG access from agents** — everything goes through `tools/`.
- **One factory per agent**: `get_<name>_agent()` + `get_<name>_task()` pattern.
- **Negotiator/Contract are NOT in the main crew** — `check_replies.py` invokes outreach_manager (as negotiator) and contract_helper directly.

## ANTI-PATTERNS

- **No new agents outside the 4 phase dirs or protocol/** — wire new agents into `crew.py::_run_<phase>_phase`, not into the shims.
- **No crewai hard dependency at import time** — keep the `_base.py` stub fallback intact so modules import without crewai.
