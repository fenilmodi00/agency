# instagrapi-mvp-diversion - Work Plan

## TL;DR (For humans)

**What you'll get:** Your Expo app will let creators type their Instagram username and password directly in the app to connect their account — no browser OAuth, no Meta App Review, no waiting. The app fetches their Instagram profile, posts, and insights through a local Python backend that uses the instagrapi library (the same one your existing creator-outreach CLI already uses). Profile data gets saved to your existing Appwrite database, so all your existing app features (deal threads, messages, dashboard) keep working unchanged.

**Why this approach:** Meta's App Review is a 2-4 week blocker, and the official Graph API requires Business accounts + OAuth. The unofficial instagrapi library works with any account type, needs no review, and your Python CLI at `D:\0` already has a solid instagrapi wrapper (`ig_client.py`) with session persistence, rate limiting, and DM capabilities. A thin FastAPI layer on top of that wrapper gives the Expo app an HTTP API to call — extending what already works instead of building from scratch. Your existing Appwrite Functions (OAuth + API proxy) stay deployed untouched, ready to switch back when Meta approves you.

**What it will NOT do:**
- It will NOT delete or change your existing Appwrite Functions or the Python CLI's CrewAI agents — those stay as-is for future use
- It will NOT support publishing content to Instagram yet — the Expo app has no publishing UI, so publishing endpoints are deferred
- It will NOT deploy to the cloud — local + ngrok for MVP testing (your Nebius $50 credit is saved for when the MVP is validated)

**Effort:** Medium
**Risk:** Medium — instagrapi is unofficial and can break when Instagram changes its private API; sessions expire and may require re-login; 2FA accounts need manual handling
**Decisions to sanity-check:**
1. Reusing Clerk JWT for FastAPI auth (consistent with existing Appwrite Functions approach)
2. Local + ngrok for MVP (zero cost, full debug access, Nebius credit reserved for later)
3. FastAPI stores profile in Appwrite `creators` table (existing hooks need zero changes)
4. Publishing endpoints deferred (no publishing UI in the Expo app)

Your next move: approve this plan, then run `/start-work` to begin execution. Full execution detail follows below.

---

> TL;DR (machine): Medium effort, Medium risk. 6 tasks across 3 waves. Extend ig_client.py with profile/media/insights/logout + per-user sessions, build FastAPI backend with Clerk JWT auth + session manager + Appwrite sync, rewrite Expo instagram.ts + home screen from OAuth to username+password login. Local+ngrok deployment. Existing Appwrite Functions and CLI agents unchanged.

## Scope
### Must have
- **Extended `ig_client.py`**: 4 new methods on `InstagramClient` — `fetch_profile()`, `fetch_media()`, `fetch_insights()`, `logout()` — plus per-user session file support (constructor accepts `session_file_path` param). Existing DM/thread/lookup methods and the CLI singleton (`get_ig_client()`) remain unchanged.
- **FastAPI backend** (`D:\0/api/`): New Python HTTP server with 5 endpoints (`/login`, `/profile`, `/media`, `/insights`, `/disconnect`). Uses Clerk JWT for auth (PyJWT + `CLERK_SECRET_KEY`). Per-user `InstagramClient` registry keyed by `clerk_user_id` (`api/session_manager.py`) with LRU eviction (max 50 sessions). Session files at `data/sessions/{clerk_user_id}.json` with `chmod 0o600`. `/login` endpoint stores IG profile in Appwrite `creators` table via Python Appwrite Server SDK. CORS enabled for Expo app origin. Session expiry returns 401 `session_expired` so the Expo app re-shows the login form.
- **Rewritten Expo `instagram.ts`**: Replace OAuth flow with `loginInstagram(clerkId, username, password)` POSTing to FastAPI `/login`. Replace `fetchProfile`/`fetchMedia`/`fetchInsights`/`disconnectInstagram` to call FastAPI endpoints with Clerk JWT in `x-appwrite-user-jwt` header. Remove `publishContent` (deferred — no publishing UI). New env var `EXPO_PUBLIC_IG_API_BASE_URL`.
- **Updated Expo home screen** (`(home)/index.tsx`): Replace OAuth "Connect Instagram" button + realtime subscription with username+password input form (TextInput fields + Connect button). On submit, call `loginInstagram()`. On success, set connected state. Remove realtime subscription for connection detection (login response is synchronous). Keep "Connected @username" badge + Disconnect button.
- **Updated Expo hooks**: `useCreatorProfile` — profile still reads from Appwrite `creators` table (unchanged), add fetching media/insights from FastAPI. `useThreads`, `useMessages`, `useDashboard` — completely UNCHANGED (they read deal_threads/messages/deals from Appwrite, unaffected by the IG API switch).
- **ngrok tunnel + env config**: Start ngrok tunnel to FastAPI (port 8000). Set `EXPO_PUBLIC_IG_API_BASE_URL` in `creator-workspace/.env` to the ngrok URL. E2E test of full flow.
- **Tests**: pytest for backend (mock instagrapi, mock Appwrite SDK — follow `D:\0/tests/` existing pattern). Jest for Expo app (follow `D:\creator-workspace/src/__tests__/` existing pattern).

### Must NOT have (guardrails, anti-slop, scope boundaries)
- NO deletion or modification of existing Appwrite Functions (`ig-oauth-callback`, `ig-api-proxy`, `clerk-bridge`) — they stay deployed for future production switch
- NO changes to the Python CLI's CrewAI agents (`agents/`, `crew.py`, `main.py`, `check_replies.py`) — the FastAPI backend is additive
- NO changes to the singleton `get_ig_client()` or its global session behavior — the CLI's existing flow must keep working; per-user instances are separate
- NO `print()` or stdlib `logging` in Python backend — use `from loguru import logger` (AGENTS.md convention)
- NO hardcoded secrets — all credentials in `.env` via `config.py` or FastAPI env vars
- NO Meta App Review submission — this plan bypasses Meta entirely
- NO Expo Development Build — stays on Expo Go
- NO OAuth flow — replaced by username+password login via instagrapi
- NO client-side instagrapi session storage — sessions stay on the FastAPI backend, never sent to the app
- NO `@tool` decorator in FastAPI code — the backend uses plain FastAPI route handlers, not CrewAI tools
- NO bare `except:` clauses — use specific instagrapi exception types (follow `ig_client.py` pattern)
- NO fixed-interval delays — use `random.uniform(DM_DELAY_MIN, DM_DELAY_MAX)` (AGENTS.md convention)
- NO real Instagram API calls in tests — mock instagrapi Client in all pytest tests
- NO real network calls in Expo jest tests — mock `fetch` globally

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + manual E2E with real IG account (local+ngrok)
- Evidence: .omo/evidence/task-<N>-instagrapi-mvp-diversion.<ext>
- Backend tested via `pytest tests/` with mocked instagrapi Client and mocked Appwrite SDK (follow D:\0's existing 291-test pattern: pytest + pytest-mock, `:memory:` DB, no real network/LLM)
- Expo app tested via `npx jest` with `@testing-library/react-native` (follow D:\creator-workspace's existing integration.test.tsx pattern)
- E2E tested via manual flow: Expo Go on phone → ngrok → FastAPI → instagrapi → Instagram → Appwrite `creators` table

## Execution strategy
### Parallel execution waves

**Wave 1 (3 parallel tasks — no inter-dependencies):**
- Task 1: Extend `ig_client.py` — add 5 new methods + per-user session support
- Task 2: FastAPI infrastructure — app skeleton, Clerk JWT auth, session manager, Appwrite client, route stubs
- Task 3: Expo `instagram.ts` rewrite — replace Graph API calls with FastAPI calls

**Wave 2 (2 tasks — depend on Wave 1):**
- Task 4: FastAPI endpoint implementation — wire all 5 routes using extended ig_client + auth + session manager + Appwrite (depends on Tasks 1+2)
- Task 5: Expo home screen + hooks update — replace OAuth UI with login form, add media/insights fetching (depends on Task 3)

**Wave 3 (1 task — depends on Wave 2):**
- Task 6: ngrok setup, env config, E2E integration test (depends on Tasks 4+5)

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Extend ig_client.py | — | 4 | 2, 3 |
| 2. FastAPI infrastructure | — | 4 | 1, 3 |
| 3. Expo instagram.ts rewrite | — | 5 | 1, 2 |
| 4. FastAPI endpoint implementation | 1, 2 | 6 | 5 |
| 5. Expo home screen + hooks | 3 | 6 | 4 |
| 6. ngrok + env config + E2E test | 4, 5 | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->

- [ ] 1. Extend `ig_client.py`: Add profile/media/insights/publish methods + per-user session support + pytest
  What to do:
  - Add `session_file_path: str | None = None` parameter to `InstagramClient.__init__()`. When provided, use it instead of the global `IG_SESSION_FILE`. When `None`, fall back to `IG_SESSION_FILE` (preserves CLI singleton behavior — `get_ig_client()` is unchanged).
  - Modify `login()` to accept `session_file_path` override for `_dump_settings()` and `os.path.exists()` check — use `self._session_file_path` if set, else the global `IG_SESSION_FILE`.
  - Add method `fetch_profile(self, username: str | None = None) -> dict | None`:
    - If `username` provided → use `self.cl.user_info_from_username(username)` (fetch any user's profile)
    - If `username` is `None` → use `self.cl.user_info(self.cl.user_id)` (fetch own profile — requires login first)
    - Return dict with keys: `pk`, `username`, `full_name`, `biography`, `external_url`, `follower_count`, `following_count`, `media_count`, `is_private`, `is_verified`, `profile_pic_url`, `is_business`
    - Wrap in `self._lock`, add retry logic for `LoginRequired` (re-login once), `PleaseWaitFewMinutes`/`RateLimitError` (exponential backoff), `UserNotFound` (return None). Follow the EXACT try/except pattern of existing `read_threads()` method (lines 200-220 of ig_client.py).
    - Use `from loguru import logger` for logging (AGENTS.md convention — NO print(), NO stdlib logging).
  - Add method `fetch_media(self, amount: int = 25) -> list[dict]`:
    - Uses `self.cl.user_medias(self.cl.user_id, amount=amount)` — fetches authenticated user's own media
    - Return list of dicts with keys: `pk`, `caption_text`, `media_type`, `thumbnail_url`, `media_url`, `permalink`, `taken_at` (ISO string), `like_count`, `comment_count`, `view_count`, `play_count`
    - Same lock + retry pattern as `fetch_profile()`.
  - Add method `fetch_insights(self) -> dict | None`:
    - Uses `self.cl.insights_account()` — requires a Business account (instagrapi raises `UserError` if not business)
    - Catch `UserError` and return `{"error": "Business account required for insights"}` (don't crash — the app should handle gracefully)
    - Same lock + retry pattern.
  - Add method `logout(self) -> bool`:
    - Calls `self.cl.logout()`, sets `self._logged_in = False`, deletes session file if exists (`os.remove(self._session_file_path or IG_SESSION_FILE)` with try/except OSError pass)
    - Returns `True` on success.
  - Write tests in `tests/test_ig_client_extended.py`:
    - Mock `instagrapi.Client` using `pytest-mock`'s `mocker.patch` — follow the existing `tests/` pattern (no real network/LLM calls)
    - Test `fetch_profile()` happy: mock `user_info_from_username` returns a mock User object → assert returned dict has correct keys
    - Test `fetch_profile()` failure: mock raises `UserNotFound` → assert returns `None`
    - Test `fetch_profile()` re-login: mock raises `LoginRequired` on first call, succeed on second → assert `login()` called, returns dict
    - Test `fetch_media()` happy: mock `user_medias` returns list of mock Media objects → assert returned list of dicts
    - Test `fetch_insights()` business account: mock `insights_account` returns dict → assert returns dict
    - Test `fetch_insights()` non-business: mock raises `UserError` → assert returns `{"error": "Business account required for insights"}`
    - Test `logout()`: mock `cl.logout`, mock `os.path.exists` returns True → assert `_logged_in` is False, `os.remove` called
    - Test per-user session: create `InstagramClient(session_file_path="data/sessions/test_user.json")` → assert `self._session_file_path == "data/sessions/test_user.json"`
    - Test singleton unchanged: `get_ig_client()` returns instance with `_session_file_path` is None (uses global `IG_SESSION_FILE`)
  Must NOT do:
    - Do NOT modify the `get_ig_client()` singleton function or `_singleton`/`_singleton_lock` globals
    - Do NOT change existing methods (`login`, `send_dm`, `read_threads`, `read_thread`, `user_id_from_username`, `send_dm_to_thread`, `get_unread_threads`, `get_pending_requests`, `find_thread_by_user_id`) — only ADD new methods and the constructor param
    - Do NOT use `print()` or `import logging` — use `from loguru import logger`
    - Do NOT use bare `except:` — catch specific instagrapi exceptions
    - Do NOT add publishing methods (`publish_photo`, `publish_reel`) — deferred to future phase (no publishing UI in the Expo app)
  Parallelization: Wave 1 | Blocked by: none | Blocks: 4
  References:
    - `ig_client.py` — full file (392 lines) — the class to extend, lines 65-392
    - `ig_client.py:71-76` — `__init__` method (add `session_file_path` param here)
    - `ig_client.py:79-103` — `login()` method (modify to use `self._session_file_path`)
    - `ig_client.py:105-111` — `_dump_settings()` (modify to use `self._session_file_path`)
    - `ig_client.py:200-220` — `read_threads()` retry pattern (replicate for new methods)
    - `ig_client.py:249-271` — `user_id_from_username()` retry pattern (replicate for fetch_profile)
    - `tools/instagram_tools.py:114-141` — existing `get_profile()` tool that calls `cl.user_info_from_username()` — reference for field mapping
    - `config.py:59-61` — `IG_USERNAME`, `IG_PASSWORD`, `IG_SESSION_FILE` globals
    - `config.py:77-83` — `MAX_DMS_PER_DAY`, `DM_DELAY_SECONDS`, `DM_DELAY_JITTER` (rate limiting constants)
    - `tests/` — existing 291-test suite (pytest + pytest-mock, mocked, no real network/LLM)
    - instagrapi `User` type fields: `pk`, `username`, `full_name`, `biography`, `external_url`, `follower_count`, `following_count`, `media_count`, `is_private`, `is_verified`, `profile_pic_url`, `is_business` (from `instagrapi/types.py`)
    - instagrapi `Media` type fields: `pk`, `caption_text`, `media_type`, `thumbnail_url`, `media_url`, `permalink`, `taken_at`, `like_count`, `comment_count`, `view_count`, `play_count`
    - instagrapi `insights_account()` — raises `UserError` if not a Business account
  Acceptance criteria (agent-executable):
    - `python -m pytest tests/test_ig_client_extended.py -v` — all tests pass
    - `python -c "from ig_client import InstagramClient; c = InstagramClient(session_file_path='data/sessions/test.json'); assert c._session_file_path == 'data/sessions/test.json'"` — per-user session path works
    - `python -c "from ig_client import get_ig_client; c = get_ig_client(); assert c._session_file_path is None"` — singleton unchanged
    - `python -c "from ig_client import InstagramClient; assert hasattr(InstagramClient, 'fetch_profile')"` — method exists
    - `python -c "from ig_client import InstagramClient; assert hasattr(InstagramClient, 'fetch_media')"` — method exists
    - `python -c "from ig_client import InstagramClient; assert hasattr(InstagramClient, 'fetch_insights')"` — method exists
    - `python -c "from ig_client import InstagramClient; assert hasattr(InstagramClient, 'logout')"` — method exists
  QA scenarios:
    - Happy: `python -m pytest tests/test_ig_client_extended.py::test_fetch_profile_happy -v` — mock returns User → dict with all keys, passes
    - Failure: `python -m pytest tests/test_ig_client_extended.py::test_fetch_profile_user_not_found -v` — mock raises UserNotFound → returns None, passes
    - Failure: `python -m pytest tests/test_ig_client_extended.py::test_fetch_insights_non_business -v` — mock raises UserError → returns error dict, passes
    - Evidence: .omo/evidence/task-1-instagrapi-mvp-diversion.txt
  Commit: Y | feat(ig-client): Add profile/media/insights/logout methods + per-user session support

- [ ] 2. FastAPI infrastructure: App skeleton, Clerk JWT auth, session manager, Appwrite client, route stubs + pytest
  What to do:
  - Create directory `D:\0/api/` with these files:
    - `api/__init__.py` — empty package marker
    - `api/main.py` — FastAPI app instance with CORS middleware (allow all origins for MVP), lifespan context, and 5 route stubs: `/login` (POST), `/profile` (GET), `/media` (GET), `/insights` (GET), `/disconnect` (POST). Each stub returns `{"status": "not_implemented"}` with 501 status code. Include a `/health` GET endpoint that returns `{"status": "ok"}`.
    - `api/auth.py` — Clerk JWT verification function:
      - `verify_clerk_jwt(jwt_token: str) -> str | None` — decode JWT using `PyJWT` (`import jwt`) with `CLERK_SECRET_KEY` from env. Extract `sub` claim (Clerk user ID). Return `clerk_user_id` if valid, `None` if invalid/expired.
      - Use `jwt.decode(token, CLERK_SECRET_KEY, algorithms=["HS256"])` — Clerk test keys use HS256.
      - `from loguru import logger` for logging failures.
      - Dependency function `get_clerk_user_id(authorization: str = Header(...))` that extracts Bearer token, verifies, returns clerk_user_id or raises `HTTPException(401)`.
    - `api/session_manager.py` — per-user InstagramClient registry:
      - `class SessionManager` with `_clients: dict[str, InstagramClient]` (keyed by `clerk_user_id`), `_lock: threading.Lock`, `MAX_SESSIONS = 50` (LRU eviction — when dict exceeds 50, evict oldest by insertion order, call `.logout()` on evicted client).
      - `get_or_create(self, clerk_user_id: str, username: str, password: str) -> InstagramClient` — create `InstagramClient(session_file_path=f"data/sessions/{clerk_user_id}.json")`, call `.login(username, password)`, store in dict. If client already exists and `_logged_in` is True, return it. If exists but not logged in, re-login.
      - `get(self, clerk_user_id: str) -> InstagramClient | None` — return existing client or None.
      - `remove(self, clerk_user_id: str) -> bool` — call `.logout()`, remove from dict, return True.
      - `from loguru import logger` for logging.
      - Session expiry: if `get()` returns a client but instagrapi raises `LoginRequired` on the next call, the endpoint catches it and returns `HTTP 401` with `{"error": "session_expired", "message": "Please reconnect your Instagram account"}`. The Expo app shows the login form again.
    - `api/appwrite_client.py` — Appwrite Server SDK wrapper:
      - `class AppwriteClient` using `from appwrite import Client, Databases` (Python SDK: `pip install appwrite`)
      - `__init__` — create `Client()` with `set_endpoint(APPWRITE_ENDPOINT)`, `set_project(APPWRITE_PROJECT_ID)`, `set_key(APPWRITE_API_KEY)`. Store `Databases(client)`.
      - `store_creator_profile(self, clerk_user_id: str, profile: dict) -> bool` — query `creators` table where `clerk_user_id` = clerk_user_id. If row exists → update with profile fields. If not → create new row. Set row permissions: `read("user:{appwrite_uid}"), update("user:{appwrite_uid}"), delete("user:{appwrite_uid}")`.
      - `clear_creator_session(self, clerk_user_id: str) -> bool` — update creators row: set `access_token=""`, `token_expires_at=""`, `is_onboarded=False`.
      - All env vars from `config.py` or direct `os.getenv()`: `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY`, `APPWRITE_DATABASE_ID` (= "vernacular_saas"), `APPWRITE_CREATORS_TABLE_ID` (= "creators").
      - `from loguru import logger` for logging.
    - `api/requirements.txt` — add: `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`, `PyJWT>=2.9.0`, `appwrite>=7.0.0`, `pydantic>=2.0` (for request models)
    - `api/.env.example` — document: `CLERK_SECRET_KEY=`, `APPWRITE_ENDPOINT=https://sgp.cloud.appwrite.io/v1`, `APPWRITE_PROJECT_ID=6a4f2e330009199ecb31`, `APPWRITE_API_KEY=`, `APPWRITE_DATABASE_ID=vernacular_saas`, `APPWRITE_CREATORS_TABLE_ID=creators`, `IG_API_PORT=8000`
  - Write tests in `tests/test_api_infrastructure.py`:
    - Mock FastAPI `TestClient` from `fastapi.testclient`
    - Test `/health` returns 200 + `{"status": "ok"}`
    - Test all 5 route stubs return 501 + `{"status": "not_implemented"}`
    - Test `verify_clerk_jwt()` with valid token (mock `jwt.decode`) → returns clerk_user_id
    - Test `verify_clerk_jwt()` with invalid token (mock `jwt.decode` raises `jwt.InvalidTokenError`) → returns None
    - Test `SessionManager.get_or_create()` — mock `InstagramClient` class, assert client created with correct session_file_path, login called, stored in dict
    - Test `SessionManager` LRU eviction — add 51 clients, assert oldest evicted and `.logout()` called
    - Test `SessionManager.get()` returns None for unknown user
    - Test `AppwriteClient.store_creator_profile()` — mock `Databases`, assert `update_document` or `create_document` called with correct args
  Must NOT do:
    - Do NOT implement the actual endpoint logic (just stubs returning 501) — that's Task 4
    - Do NOT use `print()` or `import logging` — use `from loguru import logger`
    - Do NOT store IG credentials (username/password) in memory beyond the `login()` call — only the session file persists
    - Do NOT create multiple `SessionManager` or `AppwriteClient` instances — singleton pattern
    - Do NOT skip CORS — Expo Go sends requests from a different origin
    - Do NOT hardcode secrets — all from env/config.py
  Parallelization: Wave 1 | Blocked by: none | Blocks: 4
  References:
    - `ig_client.py:65-76` — `InstagramClient.__init__` (the class to instantiate per-user)
    - `ig_client.py:79-103` — `login()` method (called by SessionManager)
    - `config.py:1-11` — `.env` loading pattern with `python-dotenv`
    - `config.py:59-61` — `IG_USERNAME`, `IG_PASSWORD`, `IG_SESSION_FILE` globals
    - `creator-workspace/.env:4` — `CLERK_SECRET_KEY=sk_test_...` (the key to verify JWTs)
    - `creator-workspace/.env:5` — `APPWRITE_API_KEY=standard_...` (the key for Python SDK)
    - `creator-workspace/.env:6-7` — `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`
    - `creator-workspace/src/lib/constants.ts:1-9` — DATABASE_ID="vernacular_saas", TABLES.CREATORS="creators"
    - `creator-workspace/src/lib/instagram.ts:110-123` — current `fetchProfile()` that sends `x-appwrite-user-jwt` header (FastAPI must accept same header)
    - `creator-workspace/src/lib/types.ts:8-44` — `Creator` interface (the Appwrite table schema — FastAPI must write these fields)
    - Appwrite Python SDK: `pip install appwrite` → `from appwrite import Client, Databases` → `client = Client().set_endpoint().set_project().set_key()`
    - Clerk JWT docs: test keys use HS256, `sub` claim is the user ID
    - instagrapi session expiry: `LoginRequired` exception when session is invalid
  Acceptance criteria (agent-executable):
    - `cd D:\0 && python -m pytest tests/test_api_infrastructure.py -v` — all tests pass
    - `cd D:\0 && python -c "from api.main import app; from fastapi.testclient import TestClient; c = TestClient(app); r = c.get('/health'); assert r.status_code == 200 and r.json()['status'] == 'ok'"` — health check works
    - `cd D:\0 && python -c "from api.auth import verify_clerk_jwt; print(callable(verify_clerk_jwt))"` — auth module importable
    - `cd D:\0 && python -c "from api.session_manager import SessionManager; sm = SessionManager(); print(sm.MAX_SESSIONS)"` — session manager importable
    - `cd D:\0 && python -c "from api.appwrite_client import AppwriteClient; print(callable(AppwriteClient))"` — appwrite client importable
  QA scenarios:
    - Happy: `python -m pytest tests/test_api_infrastructure.py::test_health_endpoint -v` — GET /health returns 200
    - Happy: `python -m pytest tests/test_api_infrastructure.py::test_session_lru_eviction -v` — 51st client evicts 1st
    - Failure: `python -m pytest tests/test_api_infrastructure.py::test_verify_jwt_invalid -v` — invalid token returns None
    - Evidence: .omo/evidence/task-2-instagrapi-mvp-diversion.txt
  Commit: Y | feat(api): FastAPI infrastructure with Clerk JWT auth, session manager, Appwrite client, route stubs

- [ ] 3. Expo `instagram.ts` rewrite: Replace Graph API calls with FastAPI calls + jest
  What to do:
  - Edit `D:\creator-workspace/src/lib/instagram.ts` — COMPLETE REWRITE of the module:
    - Remove: `getOAuthUrl()`, `connectInstagram()` (OAuth flow), `IG_APP_ID`, `OAUTH_CALLBACK_URL` constants
    - Keep: `InstagramProfileResponse` interface (rename `followers_count` → `follower_count` to match instagrapi fields), `InstagramMediaResponse` interface, `InstagramInsightsResponse` interface, `isValidAccountType()`, `mapAccountType()`, `getTokenExpiryDate()` (latter two can stay — no harm)
    - Add env var: `const API_BASE_URL = process.env.EXPO_PUBLIC_IG_API_BASE_URL || '';` — the FastAPI base URL (ngrok URL for local dev)
    - Add helper: `async function getAuthHeaders(): Promise<HeadersInit>` — calls `account.createJWT()` from `./appwrite`, returns `{'x-appwrite-user-jwt': jwt.jwt, 'Content-Type': 'application/json'}`
    - Replace `connectInstagram(clerkUserId, appwriteUserId)` with:
      ```
      export async function loginInstagram(clerkId: string, username: string, password: string): Promise<InstagramProfileResponse>
      ```
      POSTs to `${API_BASE_URL}/login` with JSON body `{clerk_id: clerkId, username, password}` and JWT header. On 200 → returns profile JSON. On 401 → throws Error("Invalid credentials"). On 502 → throws Error("Instagram login failed").
    - Replace `fetchProfile(clerkId)` → `fetchProfile()` (no clerkId needed — JWT identifies the user). GET `${API_BASE_URL}/profile` with JWT header. On 200 → returns profile. On 401 → throws Error("session_expired").
    - Replace `fetchMedia(clerkId)` → `fetchMedia()`. GET `${API_BASE_URL}/media?amount=25` with JWT header.
    - Replace `fetchInsights(clerkId)` → `fetchInsights()`. GET `${API_BASE_URL}/insights` with JWT header. On 200 → returns insights. If returns `{"error": "Business account required..."}` → return that as-is (caller handles gracefully).
    - Replace `disconnectInstagram(clerkId)` → `disconnectInstagram()`. POST `${API_BASE_URL}/disconnect` with JWT header. No body needed.
    - Update `InstagramProfileResponse` interface to match instagrapi output:
      ```
      export interface InstagramProfileResponse {
        pk: string;
        username: string;
        full_name: string;
        biography: string;
        external_url: string | null;
        follower_count: number;
        following_count: number;
        media_count: number;
        is_private: boolean;
        is_verified: boolean;
        profile_pic_url: string;
        is_business: boolean;
      }
      ```
    - Update `InstagramMediaResponse` to match instagrapi output (array of media objects with `pk`, `caption_text`, `media_type`, `thumbnail_url`, `media_url`, `permalink`, `taken_at`, `like_count`, `comment_count`, `view_count`, `play_count`).
    - Remove `publishContent()` function — no publishing UI in the app (deferred)
  - Edit `D:\creator-workspace/.env` — add:
    ```
    EXPO_PUBLIC_IG_API_BASE_URL=  # Set to ngrok URL in Task 6
    ```
  - Write tests in `D:\creator-workspace/src/__tests__/instagram.test.ts`:
    - Mock `fetch` globally using `jest.fn()`
    - Mock `account.createJWT` to return `{jwt: 'mock-jwt'}`
    - Test `loginInstagram()` happy: mock fetch returns 200 with profile → assert fetch called with correct URL, method, body, headers → assert returns profile object
    - Test `loginInstagram()` failure: mock fetch returns 401 → assert throws Error("Invalid credentials")
    - Test `fetchProfile()` happy: mock fetch returns 200 → assert correct URL and headers
    - Test `fetchProfile()` session expired: mock fetch returns 401 → assert throws Error("session_expired")
    - Test `disconnectInstagram()` happy: mock fetch returns 200 → assert POST called with correct URL
    - Test `fetchMedia()` happy: mock fetch returns 200 with media array → assert returns array
    - Test `fetchInsights()` non-business: mock fetch returns 200 with `{"error": "..."}` → assert returns that object (no throw)
  Must NOT do:
    - Do NOT modify `src/lib/appwrite.ts`, `src/lib/constants.ts`, `src/lib/realtime.ts`, `src/lib/types.ts`, `src/lib/auth-bridge.ts`, `src/lib/logger.tsx`, `src/lib/polyfills.ts` — these stay unchanged
    - Do NOT add OAuth-related code — the entire OAuth flow is removed
    - Do NOT store IG username/password in the app beyond the login call — credentials are sent to FastAPI and forgotten
    - Do NOT remove `isValidAccountType()` or `mapAccountType()` — they may be used elsewhere
    - Do NOT use `expo-auth-session` or `expo-web-browser` — no longer needed
    - Do NOT add real network calls in tests — mock `fetch` globally
  Parallelization: Wave 1 | Blocked by: none | Blocks: 5
  References:
    - `creator-workspace/src/lib/instagram.ts` — full file (208 lines) — the module being rewritten
    - `creator-workspace/src/lib/appwrite.ts:1-13` — `account` export (for `createJWT()`)
    - `creator-workspace/src/lib/constants.ts:1-11` — `DATABASE_ID`, `TABLES` constants (unchanged)
    - `creator-workspace/src/lib/types.ts:8-44` — `Creator` interface (the Appwrite row schema)
    - `creator-workspace/src/app/(tabs)/(home)/index.tsx:1-152` — home screen that imports from `instagram.ts` (will be updated in Task 5)
    - `creator-workspace/src/hooks/useCreatorProfile.ts:1-108` — hook that reads Appwrite creators table (unchanged for profile, will add media/insights in Task 5)
    - `creator-workspace/.env:9-16` — current Instagram env vars (replace with `EXPO_PUBLIC_IG_API_BASE_URL`)
    - `creator-workspace/jest.config.js` — jest config
    - `creator-workspace/src/__tests__/integration.test.tsx:1-57` — existing test pattern
  Acceptance criteria (agent-executable):
    - `cd D:\creator-workspace && npx jest src/__tests__/instagram.test.ts --verbose` — all tests pass
    - `cd D:\creator-workspace && npx tsc --noEmit src/lib/instagram.ts` — no TypeScript errors
    - `cd D:\creator-workspace && grep -c "getOAuthUrl\|connectInstagram\|IG_APP_ID\|OAUTH_CALLBACK_URL" src/lib/instagram.ts` — returns 0 (old code fully removed)
    - `cd D:\creator-workspace && grep -c "loginInstagram\|EXPO_PUBLIC_IG_API_BASE_URL" src/lib/instagram.ts` — returns ≥ 2 (new code present)
  QA scenarios:
    - Happy: `npx jest src/__tests__/instagram.test.ts -t "loginInstagram happy" --verbose` — mock 200 → returns profile
    - Failure: `npx jest src/__tests__/instagram.test.ts -t "loginInstagram failure" --verbose` — mock 401 → throws
    - Failure: `npx jest src/__tests__/instagram.test.ts -t "fetchProfile session expired" --verbose` — mock 401 → throws "session_expired"
    - Evidence: .omo/evidence/task-3-instagrapi-mvp-diversion.txt
  Commit: Y | feat(instagram): Rewrite Instagram module to use FastAPI backend instead of Graph API OAuth

- [ ] 4. FastAPI endpoint implementation: Wire all 5 routes using extended ig_client + auth + session manager + Appwrite client + pytest
  What to do:
  - Edit `D:\0/api/main.py` — replace all 5 route stubs with full implementations:
    - `POST /login`:
      - Request body (Pydantic model `LoginRequest`): `clerk_id: str`, `username: str`, `password: str`
      - Verify Clerk JWT via `get_clerk_user_id` dependency (from `Authorization: Bearer <jwt>` header)
      - Assert `clerk_id` from body matches `clerk_user_id` from JWT (security: prevents impersonation)
      - Call `session_manager.get_or_create(clerk_user_id, username, password)` — creates InstagramClient, logs in, stores in registry
      - If login fails → 502 JSON `{"error": "instagram_login_failed", "message": str(exc)}`
      - If login succeeds → call `client.fetch_profile(username=None)` (own profile)
      - Call `appwrite_client.store_creator_profile(clerk_user_id, profile)` — stores in Appwrite `creators` table
      - Return 200 JSON: the profile dict (same shape as `InstagramProfileResponse`)
      - Also set `is_onboarded=True`, `account_type` based on `is_business` flag, `username`, `full_name`, `bio` (from `biography`), `profile_pic_url`, `follower_count`, `following_count`, `media_count`
    - `GET /profile`:
      - Auth via `get_clerk_user_id` dependency
      - Get client from `session_manager.get(clerk_user_id)` — if None → 401 `{"error": "not_connected", "message": "Please connect your Instagram account first"}`
      - Call `client.fetch_profile(username=None)` (own profile)
      - If `LoginRequired` → 401 `{"error": "session_expired", "message": "Please reconnect your Instagram account"}`
      - Return 200 JSON: profile dict
    - `GET /media?amount=25`:
      - Auth via `get_clerk_user_id` dependency
      - Get client → if None → 401 `{"error": "not_connected"}`
      - Call `client.fetch_media(amount=amount)`
      - Handle `LoginRequired` → 401 `session_expired`
      - Return 200 JSON: `{"data": [...media_dicts]}`
    - `GET /insights`:
      - Auth via `get_clerk_user_id` dependency
      - Get client → if None → 401 `{"error": "not_connected"}`
      - Call `client.fetch_insights()`
      - If returns `{"error": "Business account required..."}` → 200 with that dict (not an error — app shows gracefully)
      - Handle `LoginRequired` → 401 `session_expired`
      - Return 200 JSON: insights dict
    - `POST /disconnect`:
      - Auth via `get_clerk_user_id` dependency
      - Call `session_manager.remove(clerk_user_id)` — logs out client, removes from registry
      - Call `appwrite_client.clear_creator_session(clerk_user_id)` — clears `access_token`, `token_expires_at`, `is_onboarded` in Appwrite
      - Return 200 JSON: `{"status": "disconnected"}`
  - Add Pydantic models in `api/main.py` (or `api/models.py`):
    - `class LoginRequest(BaseModel): clerk_id: str; username: str; password: str`
  - Write tests in `tests/test_api_endpoints.py`:
    - Mock `SessionManager`, `AppwriteClient`, and `InstagramClient` via `mocker.patch`
    - Test `POST /login` happy: mock session_manager returns mock client, mock fetch_profile returns dict, mock store_creator_profile returns True → 200 with profile
    - Test `POST /login` IG login fail: mock session_manager raises Exception → 502 with error
    - Test `POST /login` no JWT → 401
    - Test `POST /login` mismatched clerk_id → 401 (body clerk_id ≠ JWT sub claim)
    - Test `GET /profile` happy: mock client.fetch_profile returns dict → 200
    - Test `GET /profile` no client (not connected): mock session_manager.get returns None → 401
    - Test `GET /profile` session expired: mock fetch_profile raises LoginRequired → 401
    - Test `GET /media` happy: mock fetch_media returns list → 200 with data array
    - Test `GET /insights` business account: mock fetch_insights returns dict → 200
    - Test `GET /insights` non-business: mock fetch_insights returns `{"error": "..."}` → 200 (not error)
    - Test `POST /disconnect` happy: mock session_manager.remove returns True, mock clear_creator_session returns True → 200
  Must NOT do:
    - Do NOT implement `/publish`, `/dm-send`, `/dm-threads` endpoints — deferred (no UI for these in the Expo app)
    - Do NOT store IG passwords in the `creators` table — only the session file persists on the backend
    - Do NOT return raw instagrapi objects — convert to plain dicts before JSON serialization
    - Do NOT skip the clerk_id mismatch check — prevents one user logging in as another
    - Do NOT use `print()` — use `from loguru import logger`
  Parallelization: Wave 2 | Blocked by: 1, 2 | Blocks: 6
  References:
    - `api/main.py` — route stubs created in Task 2 (replace with implementations)
    - `api/auth.py` — `get_clerk_user_id` dependency (created in Task 2)
    - `api/session_manager.py` — `SessionManager` class (created in Task 2)
    - `api/appwrite_client.py` — `AppwriteClient` class (created in Task 2)
    - `ig_client.py` — extended `InstagramClient` with `fetch_profile()`, `fetch_media()`, `fetch_insights()`, `logout()` (from Task 1)
    - `creator-workspace/src/lib/types.ts:8-44` — `Creator` interface (the fields to store in Appwrite)
    - `creator-workspace/src/lib/instagram.ts` — rewritten module (from Task 3) — the API contract the Expo app expects
    - Appwrite Python SDK: `from appwrite.query import Query`; `databases.list_documents(database_id, collection_id, queries=[Query.equal('clerk_user_id', clerk_id)])`
    - Appwrite `creators` table columns: `username`, `full_name`, `bio`, `profile_pic_url`, `follower_count`, `following_count`, `media_count`, `post_count`, `ig_user_id`, `ig_scoped_id`, `access_token`, `token_expires_at`, `is_onboarded`, `clerk_user_id`, `account_type`, `is_verified`, `is_business`
  Acceptance criteria (agent-executable):
    - `cd D:\0 && python -m pytest tests/test_api_endpoints.py -v` — all tests pass
    - `cd D:\0 && python -c "from api.main import app; from fastapi.testclient import TestClient; c = TestClient(app); r = c.post('/login'); assert r.status_code in [401, 422]"` — no-auth /login is rejected
    - `cd D:\0 && python -c "from api.main import app; from fastapi.testclient import TestClient; c = TestClient(app); r = c.get('/profile'); assert r.status_code == 401"` — no-auth /profile is 401
    - `cd D:\0 && python -c "from api.main import app; from fastapi.testclient import TestClient; c = TestClient(app); r = c.post('/disconnect'); assert r.status_code == 401"` — no-auth /disconnect is 401
  QA scenarios:
    - Happy: `python -m pytest tests/test_api_endpoints.py::test_login_happy -v` — login returns 200 + profile
    - Happy: `python -m pytest tests/test_api_endpoints.py::test_profile_happy -v` — profile returns 200 + data
    - Failure: `python -m pytest tests/test_api_endpoints.py::test_login_no_jwt -v` — 401
    - Failure: `python -m pytest tests/test_api_endpoints.py::test_profile_session_expired -v` — 401 session_expired
    - Failure: `python -m pytest tests/test_api_endpoints.py::test_login_clerk_id_mismatch -v` — 401 impersonation blocked
    - Evidence: .omo/evidence/task-4-instagrapi-mvp-diversion.txt
  Commit: Y | feat(api): Implement all 5 FastAPI endpoints with instagrapi + Clerk JWT auth + Appwrite sync

- [ ] 5. Expo home screen + hooks update: Replace OAuth UI with login form, add media/insights fetching + jest
  What to do:
  - Edit `D:\creator-workspace/src/app/(tabs)/(home)/index.tsx` — MAJOR REWRITE:
    - Remove: `useRealtimeSubscription` import and usage (connection is now synchronous via login response)
    - Remove: `connectInstagram` import → replace with `loginInstagram` from `@/lib/instagram`
    - Remove: `fetchCreatorProfile` function (the inline one that calls the old proxy)
    - Remove: OAuth "Connect Instagram" button that opens browser
    - Add: `useState` for `igUsername` and `igPassword` (TextInput fields)
    - Add: Login form with two `TextInput` components (username, password — password with `secureTextEntry`) and a "Connect" button
    - Add: `handleLogin()` function that calls `loginInstagram(user.id, igUsername, igPassword)`:
      - On success → `setIsConnected(true)`, `setUsername(profile.username)`, `setIgUsername('')`, `setIgPassword('')` (clear credentials from state)
      - On Error "Invalid credentials" → `setError("Invalid Instagram credentials")`
      - On Error "session_expired" → show login form again
      - On Error "Instagram login failed" → `setError("Could not connect to Instagram. Check 2FA or try again.")`
    - Keep: "Connected @username" badge + "Disconnect" button (calls `disconnectInstagram()`)
    - Keep: Error display, loading state
    - Add: after successful login, fetch media and insights using the new `fetchMedia()` and `fetchInsights()` from `@/lib/instagram` (display counts or a simple list — minimal UI, just prove the data flows)
    - Use Tamagui components (`YStack`, `XStack`, `Text`, `Button`, `Input`, `Spinner`, `H2`) — consistent with existing screen
    - Remove: `timeoutRef` / 60s timeout (no longer needed — login is synchronous)
  - Edit `D:\creator-workspace/src/hooks/useCreatorProfile.ts`:
    - Keep: existing Appwrite `creators` table fetch (UNCHANGED — profile data is stored there by FastAPI /login)
    - Add: after fetching creator from Appwrite, also call `fetchMedia()` and `fetchInsights()` from `@/lib/instagram` (these go to FastAPI)
    - Add: `recentMedia` state and `insights` state to the hook's return value
    - Handle: `fetchInsights()` returning `{"error": "Business account required..."}` → set `insights = null` (not an error)
    - Handle: `fetchMedia()` / `fetchInsights()` throwing `"session_expired"` → set `error = "session_expired"` (caller shows login form)
  - Do NOT modify `useThreads.ts`, `useMessages.ts`, `useDashboard.ts` — these read from Appwrite only and are UNCHANGED (deal_threads, messages, deals all stay in Appwrite, not affected by the IG API switch)
  - Write/update tests in `D:\creator-workspace/src/__tests__/integration.test.tsx`:
    - Update the Home screen test to mock `loginInstagram` instead of `connectInstagram`
    - Test: render home screen → shows username+password inputs + "Connect" button
    - Test: fill inputs + press Connect → `loginInstagram` called with correct args
    - Test: login success → shows "Connected @username" badge
    - Test: login failure → shows error text
  Must NOT do:
    - Do NOT modify `useThreads.ts`, `useMessages.ts`, `useDashboard.ts` — these are unchanged
    - Do NOT modify `src/lib/appwrite.ts`, `src/lib/constants.ts`, `src/lib/realtime.ts`, `src/lib/types.ts` — unchanged
    - Do NOT store IG password in component state beyond the login call — clear immediately after `loginInstagram()` returns
    - Do NOT use `Linking.openURL()` — no browser OAuth
    - Do NOT use `useRealtimeSubscription` for connection detection — login is synchronous
    - Do NOT add real network calls in tests — mock `loginInstagram`, `fetchMedia`, `fetchInsights`
  Parallelization: Wave 2 | Blocked by: 3 | Blocks: 6
  References:
    - `creator-workspace/src/app/(tabs)/(home)/index.tsx` — full file (152 lines) — the screen being rewritten
    - `creator-workspace/src/lib/instagram.ts` — rewritten module from Task 3 (imports `loginInstagram`, `fetchProfile`, `fetchMedia`, `fetchInsights`, `disconnectInstagram`)
    - `creator-workspace/src/hooks/useCreatorProfile.ts` — full file (108 lines) — hook to extend with media/insights
    - `creator-workspace/src/hooks/useThreads.ts` — full file (111 lines) — DO NOT MODIFY
    - `creator-workspace/src/hooks/useMessages.ts` — full file (129 lines) — DO NOT MODIFY
    - `creator-workspace/src/hooks/useDashboard.ts` — full file (106 lines) — DO NOT MODIFY
    - `creator-workspace/src/lib/types.ts:8-44` — `Creator` interface
    - `creator-workspace/src/lib/appwrite.ts:1-13` — `account` export
    - `creator-workspace/src/__tests__/integration.test.tsx:1-57` — existing test file to update
    - Tamagui components: `YStack`, `XStack`, `Text`, `Button`, `Input`, `Spinner`, `H2`
  Acceptance criteria (agent-executable):
    - `cd D:\creator-workspace && npx jest src/__tests__/integration.test.tsx --verbose` — all tests pass
    - `cd D:\creator-workspace && npx tsc --noEmit` — no TypeScript errors
    - `cd D:\creator-workspace && grep -c "useRealtimeSubscription" src/app/\(tabs\)/\(home\)/index.tsx` — returns 0 (realtime subscription removed from home)
    - `cd D:\creator-workspace && grep -c "loginInstagram" src/app/\(tabs\)/\(home\)/index.tsx` — returns ≥ 1 (new login function used)
    - `cd D:\creator-workspace && grep -c "TextInput\|Input" src/app/\(tabs\)/\(home\)/index.tsx` — returns ≥ 2 (username + password inputs)
  QA scenarios:
    - Happy: `npx jest src/__tests__/integration.test.tsx -t "Home" --verbose` — home screen renders with login form
    - Happy: `npx jest src/__tests__/integration.test.tsx -t "login success" --verbose` — connected badge shown
    - Failure: `npx jest src/__tests__/integration.test.tsx -t "login failure" --verbose` — error text shown
    - Evidence: .omo/evidence/task-5-instagrapi-mvp-diversion.txt
  Commit: Y | feat(home): Replace OAuth flow with username+password login form + media/insights fetching

- [ ] 6. ngrok setup, env config, E2E integration test
  What to do:
  - Start FastAPI server locally:
    - `cd D:\0 && pip install -r api/requirements.txt` (if not already installed)
    - Create `D:\0/api/run.py` — simple uvicorn launcher: `import uvicorn; uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)`
    - Set env vars in `D:\0/.env` (or create `D:\0/api/.env`): `CLERK_SECRET_KEY` (from creator-workspace/.env), `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY` (from creator-workspace/.env), `APPWRITE_DATABASE_ID=vernacular_saas`, `APPWRITE_CREATORS_TABLE_ID=creators`
    - Run: `python api/run.py` — server starts on port 8000
    - Verify: `curl http://localhost:8000/health` → 200 `{"status": "ok"}`
  - Start ngrok tunnel:
    - `ngrok http 8000` — creates a public HTTPS tunnel to localhost:8000
    - Copy the forwarding URL (e.g., `https://abc123.ngrok-free.app`)
    - NOTE: ngrok free tier changes URL on restart — update the Expo app's env var each time
  - Update Expo app env:
    - Edit `D:\creator-workspace/.env` — set `EXPO_PUBLIC_IG_API_BASE_URL=https://abc123.ngrok-free.app` (use your ngrok URL)
    - Restart Expo dev server: `cd D:\creator-workspace && npx expo start`
  - E2E test flow (manual on physical device with Expo Go):
    1. Open Expo Go on phone → scan QR code or enter URL
    2. Sign in via Clerk (existing auth)
    3. Home screen shows username + password input fields + "Connect" button
    4. Enter a real Instagram username + password
    5. Tap "Connect"
    6. If 2FA challenge → FastAPI returns 502 with challenge message (instagrapi raises ChallengeRequired) — log shows the challenge type
    7. If login succeeds → UI shows "Connected @username" badge
    8. Verify Appwrite `creators` table has a row with `clerk_user_id` matching the logged-in user, `is_onboarded=true`, `username`, `follower_count`, etc.
    9. Media and insights data displays on the home screen (if Business account for insights)
    10. Tap "Disconnect" → UI reverts to login form → Appwrite `creators` row has `is_onboarded=false`, `access_token=""`
  - Test error scenarios:
    - Enter wrong password → "Invalid Instagram credentials" error
    - No ngrok running → connection timeout error
    - FastAPI server not running → fetch fails → error message
  - Document the setup in `.omo/evidence/task-6-instagrapi-mvp-diversion.md`:
    - ngrok URL used
    - Test results (pass/fail for each step)
    - Any challenges encountered (2FA, rate limits, etc.)
  Must NOT do:
    - Do NOT deploy to a cloud platform — local + ngrok only (Nebius credit reserved for when MVP is validated)
    - Do NOT commit `.env` with real ngrok URLs or credentials
    - Do NOT test with a personal account if insights are needed — Business/Creator account required for `fetch_insights()`
    - Do NOT skip the Appwrite verification — confirm the `creators` table row is updated
  Parallelization: Wave 3 | Blocked by: 4, 5 | Blocks: none
  References:
    - `api/main.py` — FastAPI app (from Task 2+4)
    - `api/run.py` — uvicorn launcher (created in this task)
    - `creator-workspace/.env` — Expo app env vars (add `EXPO_PUBLIC_IG_API_BASE_URL`)
    - `creator-workspace/src/lib/instagram.ts` — rewritten module (from Task 3, uses `EXPO_PUBLIC_IG_API_BASE_URL`)
    - `creator-workspace/src/app/(tabs)/(home)/index.tsx` — updated home screen (from Task 5)
    - Appwrite project: 6a4f2e330009199ecb31 (sgp region)
    - Appwrite database: vernacular_saas, table: creators
    - ngrok docs: `ngrok http 8000` → HTTPS tunnel
    - `ig_client.py` — the extended InstagramClient (from Task 1)
  Acceptance criteria (agent-executable):
    - `curl http://localhost:8000/health` → 200 `{"status": "ok"}` (FastAPI running)
    - `curl -X GET https://<ngrok-url>/health` → 200 `{"status": "ok"}` (ngrok tunnel working)
    - `curl -X POST https://<ngrok-url>/login` without auth header → 401 (auth working through tunnel)
    - Appwrite `creators` table has a row with `is_onboarded=true` after successful login (verify via Appwrite console or API)
    - After disconnect, `creators` row has `is_onboarded=false`
  QA scenarios:
    - Happy: Expo Go → login form → enter real IG credentials → "Connected @username" badge → media/insights shown → Appwrite row updated
    - Failure: Wrong password → "Invalid Instagram credentials" error
    - Failure: 2FA account → 502 error with challenge message (document for future 2FA handling)
    - Evidence: .omo/evidence/task-6-instagrapi-mvp-diversion.md
  Commit: N | Setup + test only — no production code changes (only `api/run.py` if committed separately)

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit — verify every todo matches the plan, no scope creep (no /publish, /dm-send, /dm-threads endpoints), all Must-NOT-Haves respected (no print(), no OAuth, no Appwrite Function changes, no CrewAI agent changes, no bare except:)
- [ ] F2. Code quality review — verify FastAPI code uses loguru (not print/logging), instagrapi exception handling follows ig_client.py patterns, no hardcoded secrets, session files get chmod 0o600, LRU eviction works, Clerk JWT verification rejects invalid tokens, clerk_id mismatch check prevents impersonation
- [ ] F3. Real manual QA — verify the full flow works: Expo Go → ngrok → FastAPI → instagrapi → Instagram → Appwrite creators table. Test with a real Business/Creator IG account. Verify profile, media, insights (if business), disconnect all work. Test wrong password and session expiry error paths.
- [ ] F4. Scope fidelity — verify existing Appwrite Functions (ig-oauth-callback, ig-api-proxy) are unchanged, existing Python CLI agents are unchanged, singleton get_ig_client() is unchanged, Expo app's useThreads/useMessages/useDashboard are unchanged, no publishing endpoints added

## Commit strategy
- Task 1: `feat(ig-client): Add profile/media/insights/logout methods + per-user session support`
- Task 2: `feat(api): FastAPI infrastructure with Clerk JWT auth, session manager, Appwrite client, route stubs`
- Task 3: `feat(instagram): Rewrite Instagram module to use FastAPI backend instead of Graph API OAuth`
- Task 4: `feat(api): Implement all 5 FastAPI endpoints with instagrapi + Clerk JWT auth + Appwrite sync`
- Task 5: `feat(home): Replace OAuth flow with username+password login form + media/insights fetching`
- Task 6: No commit (setup + E2E test only — `api/run.py` can be committed separately if desired)
- Final: squash-merge after F1-F4 all approve

## Success criteria
1. Expo app shows a username+password login form (no OAuth browser redirect) on the home screen
2. User enters real IG credentials → FastAPI logs in via instagrapi → profile stored in Appwrite `creators` table → UI shows "Connected @username"
3. App fetches Instagram media (posts with engagement metrics) from FastAPI `/media` endpoint
4. App fetches Instagram insights from FastAPI `/insights` endpoint (Business accounts only — non-business shows graceful message)
5. User can disconnect → session file cleared, Appwrite row updated to `is_onboarded=false`, UI reverts to login form
6. Session expiry is handled: if instagrapi session is invalid, FastAPI returns 401 → app shows login form again
7. Existing Appwrite Functions (ig-oauth-callback, ig-api-proxy) remain deployed and unchanged — ready for future production switch when Meta App Review passes
8. Existing Python CLI (CrewAI agents, `main.py`, `check_replies.py`) and its `get_ig_client()` singleton are completely unchanged
9. Existing Expo app hooks (`useThreads`, `useMessages`, `useDashboard`) that read from Appwrite are unchanged — only `useCreatorProfile` is extended with media/insights fetching
10. All backend tests pass (`pytest`) with mocked instagrapi/Appwrite — no real network calls in tests
11. All Expo app tests pass (`npx jest`) with mocked fetch — no real network calls in tests
