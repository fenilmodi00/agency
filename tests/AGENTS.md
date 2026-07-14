# tests/

## OVERVIEW

117 pytest tests covering all 5 agents, the IG client, database CRUD, and crew orchestration. Fully mocked, zero network or LLM calls.

## WHERE TO LOOK

| File | Tests | Key classes |
|------|-------|-------------|
| `test_database.py` | DB CRUD for all 5 tables + edge cases | `TestBrandBriefs`, `TestConversations`, `TestContracts`, `TestDmLog`, `TestConversationDetails`, `TestEdgeCases` |
| `test_ig_client.py` | Login, send_dm, read_threads, locking, quota | `TestLogin`, `TestSendDm`, `TestLock`, `TestReadThreads`, `TestDmQuota` |
| `test_discovery.py` | Fit score math, output shape, mocked scraper | `TestFitScore`, `TestEstimatedRate`, `TestEngagementRate`, `TestDiscoveryOutputShape`, `TestMockedScraper` |
| `test_proposal.py` | Proposal JSON shape, mocked content tools | `TestProposalOutputShape`, `TestMockedContentTools` |
| `test_outreach.py` | Dry-run safety, send mode, quota enforcement | `TestDryRun`, `TestSendMode`, `TestQuota`, `TestOutreachOutputShape` |
| `test_negotiator.py` | Budget overrun logic, round limits, output shape | `TestBudgetOverrun`, `TestRoundLimit`, `TestNegotiatorOutputShape`, `TestMockedNegotiator` |
| `test_contract.py` | ASCI disclosures, legal disclaimers, output shape | `TestContractContent`, `TestContractOutputShape`, `TestMockedContract` |
| `test_crew.py` | Kickoff summary shape, token tracking, full pipeline | `TestKickoffSummary`, `TestTotalTokens`, `TestMockedCrew` |

## CONVENTIONS

- **pytest-mock everywhere.** `mocker.patch("tools.scraper_tools.get_creator_content_summary")` style. Never import real IG, LLM, or scraper modules.
- **`:memory:` SQLite.** `test_database.py` uses a `db` fixture returning `Database(":memory:")`. No file-based DB in tests.
- **`set_database(db)` before DB tool tests.** `tools/database_tools.py` uses a module-level `_db`. Any test exercising DB tools must call `set_database(db)` first or tools hit a stale default.
- **Output shape tests.** Each agent test file has a `Test*OutputShape` class validating required JSON keys, types, and serializability. Add one when adding an agent.
- **Mocked tool tests.** Each agent test file has a `TestMocked*` class patching the agent's tools and asserting return values. Proves tool wiring without running the crew.
- **`test_agents.py` in root.** Runner script that imports and executes all test modules. Not a test file itself.
