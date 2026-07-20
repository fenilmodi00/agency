# tests/

343 pytest tests across 43 files — fully mocked, zero real network/LLM/Instagram calls. One `test_<module>.py` per source module.

## WHERE TO LOOK

| Area | Files | What's covered |
|------|-------|----------------|
| Core infra | `test_database.py`, `test_ig_client.py`, `test_ig_client_extended.py` | DB CRUD (5 tables, `:memory:`), login/send/read/quota/lock |
| Orchestration | `test_crew.py`, `test_star_crew.py`, `test_main_star.py`, `test_check_replies_star.py`, `test_config_star.py` | Kickoff summary shape, phase routing, `--phase` CLI, import resolution, STAR config vars |
| STAR agents | `test_<agent>.py` x16 (audience_mapper…report_generator) + `test_memory_management.py` | Agent factories, task wiring, output shapes |
| Protocol registry | `test_<name>_registry.py` x7 | Registry agents |
| Legacy shims | `test_discovery/proposal/outreach/negotiator/contract.py`, `test_shim_compat.py` | Shim exports keep working |
| Connectors | `test_connector_tools.py`, `test_registry_tools.py` | All 17 connector wrappers via mocked `subprocess.run` |
| API backend | `test_api_infrastructure.py`, `test_api_endpoints.py` | Clerk JWT auth, SessionManager LRU, Appwrite client, all 5 authed routes via FastAPI `TestClient` |

## CONVENTIONS

- **pytest-mock everywhere** — `mocker.patch(...)`. Never import real IG, LLM, or scraper modules.
- **No conftest.py** — fixtures are defined per-file. No pytest config file either; pytest runs on defaults.
- **`:memory:` SQLite** — `Database(":memory:")` fixture; no file DBs in tests.
- **`set_database(db)` before DB tool tests** — `tools/database_tools.py` holds a module-level `_db`.
- **Output shape tests** — every agent file has a `Test*OutputShape` class validating JSON keys/types/serializability. Add one per new agent.
- **Mocked tool tests** — `TestMocked*` classes patch agent tools and assert wiring without running the crew.
- **Crew mocking** — patch `crew.Crew` with `side_effect` lambdas returning `MockCrewOutput`-shaped results.
- **API tests** — `monkeypatch` for env vars, `TestClient` for HTTP, `MagicMock` for Instagram/Appwrite/SessionManager; JWT verification patched at `api.auth.jwt.decode`.
- **Connector tests** — patch `subprocess.run`, assert on args + JSON parsing.
- **Runner**: `python test_agents.py` = `pytest.main(["tests/", "-v", "--tb=short", "--no-header"])`.
