# instagram-oauth-appwrite - Work Plan

## TL;DR (For humans)

**What you'll get:** Your Expo Go app will have a "Connect Instagram" button on the home screen. When a user taps it, their phone opens Instagram's login page in the system browser. After they approve, their Instagram data (profile, posts, insights, publishing ability) is securely stored and accessible through your app — all without leaving Expo Go and without the Instagram access token ever touching the client.

**Why this approach:** Expo Go can't do OAuth redirects (it has no custom URI scheme), so we route the Instagram OAuth callback through an Appwrite Function instead. Your server handles the redirect, exchanges the code for a long-lived token, and stores it in your existing `creators` table. The app detects completion via Appwrite's real-time subscription. This keeps the token secure on the backend and works perfectly within Expo Go's constraints.

**What it will NOT do:**
- It will NOT require a Development Build or custom APK — stays on Expo Go
- It will NOT store the Instagram token on the client — token stays server-side
- It will NOT submit for Meta App Review — Development mode (testers only) for now
- It will NOT use Facebook Login for Business — uses direct Instagram Login (simpler)

**Effort:** Medium
**Risk:** Medium — Meta Dashboard configuration is manual and the Instagram product addition is the root cause of the tester issue

**Decisions to sanity-check:**
1. Using direct Instagram API with Instagram Login (not Facebook Login for Business) — simpler for single-account apps
2. Storing token in existing `creators` table (schema already has columns for this)
3. Two separate Appwrite Functions: one for OAuth callback, one for API proxy
4. Real-time subscription (not deep linking) for detecting auth completion on Expo Go
5. State parameter carries both Appwrite user ID and Clerk user ID for row permissions + lookup
6. Graph API version v24.0

Your next move: approve this plan, then run `/start-work` to begin execution. Full execution detail follows below.

---

> TL;DR (machine): Medium effort, Medium risk. Backend-mediated Instagram OAuth via 2 Appwrite Functions (callback + proxy) storing tokens in existing creators table, Expo Go client with real-time subscription, Meta Dashboard config. 4 parallel tasks + 1 integration test.

## Scope
### Must have
- Meta App Dashboard: Instagram product added, OAuth redirect URI configured (Appwrite Function URL), Instagram testers added, scopes configured
- Appwrite Function `ig-oauth-callback` (node-18.0, execute: any): HTTP GET handler that receives `?code=...&state=...`, exchanges code → short-lived token → long-lived token (60 days), fetches IG profile, stores all in `creators` table row keyed by `clerk_user_id`, sets row permissions for the user, returns success HTML page
- Appwrite Function `ig-api-proxy` (node-18.0, execute: any): HTTP endpoint that receives app requests with Clerk JWT, verifies JWT, looks up stored token by user, proxies to Instagram Graph API (profile, media, insights, publish), auto-refreshes token if within 7 days of expiry, returns JSON response
- Expo Go client module: `Linking.openURL()` to open Instagram OAuth URL, Appwrite real-time subscription on `creators` table (filtered by `clerk_user_id`), connected/disconnected state UI, disconnect button
- Function variables: `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`, `APPWRITE_API_KEY` on both functions
- Token auto-refresh logic in ig-api-proxy (check `token_expires_at`, refresh if <7 days remaining)

### Must NOT have (guardrails, anti-slop, scope boundaries)
- NO Expo Development Build, dev-client, or custom APK — Expo Go only
- NO custom URI scheme or deep linking (`exp://` redirect) for OAuth completion — use real-time subscription
- NO client-side Instagram token storage — token NEVER sent to the app
- NO Meta App Review submission — Development mode only (testers)
- NO Facebook Login for Business — direct Instagram Login only
- NO new database tables — use existing `creators` table
- NO instagrapi modifications — this plan is for the Expo/Appwrite SaaS app, not the Python CLI
- NO hardcoded secrets — all credentials as Appwrite Function variables
- NO `console.log` of tokens or secrets in function code

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + manual E2E with tester account
- Evidence: .omo/evidence/task-{N}-instagram-oauth-appwrite.{ext}
- Function code tested via `appwrite functions createExecution` (SDK) and direct HTTP GET (domain)
- Expo client tested via Expo Go on physical device with a tester Instagram account

## Execution strategy
### Parallel execution waves

**Wave 1 (4 parallel tasks — no inter-dependencies):**
- Task 1: Meta Dashboard configuration (manual, no code)
- Task 2: Create `ig-oauth-callback` Appwrite Function
- Task 3: Create `ig-api-proxy` Appwrite Function
- Task 4: Create Expo Go client integration module

**Wave 2 (1 task — depends on ALL of Wave 1):**
- Task 5: End-to-end integration test with tester Instagram account

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Meta Dashboard config | — | 5 | 2, 3, 4 |
| 2. ig-oauth-callback function | — | 5 | 1, 3, 4 |
| 3. ig-api-proxy function | — | 5 | 1, 2, 4 |
| 4. Expo Go client module | — | 5 | 1, 2, 3 |
| 5. E2E integration test | 1, 2, 3, 4 | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.

- [x] 1. Meta Dashboard: Add Instagram product, configure OAuth redirect URI, add testers, set scopes
  What to do:
  - Go to https://developers.facebook.com/apps → select your Meta app
  - Left sidebar → "Add Product" (or "Products") → find "Instagram" → click "Set Up"
  - Choose "Instagram API with Instagram Login" (NOT "Instagram API with Facebook Login")
  - Go to "Instagram → API Setup with Instagram Login" → copy Instagram App ID and App Secret
  - Go to "Instagram → Basic Display → Client OAuth Settings" (or "OAuth" under Instagram product)
  - Add redirect URI: the Appwrite Function domain URL for `ig-oauth-callback` (format: `https://{function-id}.sgp.appwrite.run`). NOTE: The exact URL will be generated when Task 2 creates the function. Use a placeholder and update after Task 2 completes, OR create the function first then configure the redirect. The URL pattern is `https://<function-domain>.sgp.appwrite.run`.
  - Configure OAuth scopes: `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_comments`, `instagram_business_manage_insights`
  - Go to "Roles → Instagram Testers → Add Instagram Testers" → enter tester's Instagram username
  - Tester must: have a Business or Creator IG account, accept invite in IG app (Settings → Security → Apps and Websites → Invitations)
  - Store the Instagram App ID and App Secret — these will be set as function variables in Tasks 2 and 3
  Must NOT do:
  - Do NOT submit for App Review (Development mode only)
  - Do NOT choose "Instagram API with Facebook Login" — use "Instagram API with Instagram Login"
  - Do NOT add `exp://` URIs as redirect — only the Appwrite Function HTTPS URL
  Parallelization: Wave 1 | Blocked by: none | Blocks: 5
  References:
    - Meta App Dashboard: https://developers.facebook.com/apps
    - Instagram OAuth docs: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/get-started
    - Scopes reference: https://developers.facebook.com/docs/instagram-platform/permissions
    - Appwrite project ID: 6a4f2e330009199ecb31 (Kapluncer, sgp region)
  Acceptance criteria (agent-executable):
    - "Instagram" product appears in left sidebar of Meta App Dashboard
    - "Instagram Testers" section visible under Roles (this was the user's blocker — adding the Instagram product makes it appear)
    - At least 1 Instagram tester added with status "Invited" or "Accepted"
    - Redirect URI configured (Appwrite Function URL — may be placeholder until Task 2 creates it)
    - Instagram App ID and App Secret are available (to set as function variables)
  QA scenarios: manual verification via Meta Dashboard UI. Evidence: .omo/evidence/task-1-instagram-oauth-appwrite.md (screenshots or text description of dashboard state)
  Commit: N | No code changes — manual dashboard configuration only

- [x] 2. Appwrite Function `ig-oauth-callback`: OAuth code exchange → long-lived token → store in creators table
  What to do:
  - Create a new Appwrite Function named `ig-oauth-callback` (runtime: node-18.0, execute: ["any"], enabled: true)
  - Function code structure (Node.js 18, using `node-fetch` or built-in `fetch`):
    ```
    src/
      main.js          # Entry point — handles HTTP GET with ?code=&state=
      instagram.js     # OAuth exchange functions (code→short, short→long, profile fetch)
      appwrite-db.js   # Appwrite Server SDK — find/update creator row
      success-page.js  # HTML response for success/failure
      package.json     # Dependencies: node-appwrite
    ```
  - `main.js` logic:
    1. Parse `req.query.code` and `req.query.state` from the HTTP request
    2. If `code` is missing → return error HTML "Authorization failed: no code received"
    3. Decode `state` (URL-encoded JSON: `{uid, clerk_id}`) — if invalid → return error HTML
    4. Call `exchangeCodeForToken(code)` → POST to `https://api.instagram.com/oauth/access_token` with `client_id`, `client_secret`, `grant_type=authorization_code`, `redirect_uri`, `code`
    5. Call `exchangeForLongLived(shortToken)` → GET `https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret={SECRET}&access_token={SHORT}`
    6. Call `fetchProfile(longToken)` → GET `https://graph.instagram.com/v24.0/me?fields=id,username,account_type,media_count,followers_count,follows_count,profile_picture_url,biography&access_token={TOKEN}`
    7. Calculate `token_expires_at` = now + 60 days (from `expires_in` field)
    8. Use Appwrite Server SDK (`node-appwrite`) with API key to:
       a. Query `creators` table where `clerk_user_id` = `state.clerk_id` (use `tables_db_list_rows` with query filter)
       b. If row exists → update it with ig_user_id, ig_scoped_id, access_token, token_expires_at, is_onboarded=true, account_type, username, follower_count, following_count, post_count, profile_pic_url, bio, updated_at
       c. If row doesn't exist → create new row with clerk_user_id, ig_user_id, ig_scoped_id, access_token, token_expires_at, is_onboarded=true, and all profile fields
       d. Set row permissions: `read("user:{state.uid}"), update("user:{state.uid}"), delete("user:{state.uid}")`
    9. Return success HTML page:
       ```html
       <!DOCTYPE html>
       <html>
       <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
       <body style="font-family:system-ui;text-align:center;padding:40px;">
         <h1>Instagram Connected!</h1>
         <p>Your Instagram account @username has been successfully connected.</p>
         <p>You can close this browser and return to the app.</p>
       </body>
       </html>
       ```
    10. If any step fails → return error HTML with message
  - Set function variables: `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`, `APPWRITE_API_KEY`, `APPWRITE_ENDPOINT=https://sgp.cloud.appwrite.io/v1`, `APPWRITE_PROJECT_ID=6a4f2e330009199ecb31`, `APPWRITE_DATABASE_ID=vernacular_saas`, `APPWRITE_CREATORS_TABLE_ID=creators`, `GRAPH_API_VERSION=v24.0`, `REDIRECT_URI=<this function's domain URL>`
  - Deploy the function via `appwrite push function` CLI or console upload
  - After deployment, go to function Settings → Domains → copy the generated domain URL (e.g., `https://abc123.sgp.appwrite.run`)
  - Update the `REDIRECT_URI` function variable to match the domain URL
  - Go back to Meta Dashboard (Task 1) and add this URL as the OAuth redirect URI
  Must NOT do:
    - Do NOT log or return the access_token in the HTML response
    - Do NOT use the user's session — use the server API key
    - Do NOT hardcode secrets — use function variables
    - Do NOT skip error handling — every fetch must have try/catch
  Parallelization: Wave 1 | Blocked by: none | Blocks: 5
  References:
    - Appwrite project: 6a4f2e330009199ecb31 (Kapluncer, sgp)
    - Database: vernacular_saas, Table: creators (rowSecurity: true)
    - Existing function clerk-bridge as reference for runtime/structure: ID=clerk-bridge, runtime=node-18.0
    - Instagram OAuth authorize URL: `GET https://api.instagram.com/oauth/authorize?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES}&state={STATE}`
    - Token exchange: `POST https://api.instagram.com/oauth/access_token`
    - Long-lived: `GET https://graph.instagram.com/access_token?grant_type=ig_exchange_token`
    - Profile: `GET https://graph.instagram.com/v24.0/me?fields=id,username,account_type,media_count,followers_count,follows_count,profile_picture_url,biography`
    - Creators table columns: username, full_name, bio, profile_pic_url, follower_count, following_count, post_count, ig_user_id (unique), ig_scoped_id, access_token (2048), token_expires_at (datetime), is_onboarded (bool), clerk_user_id (indexed), account_type (enum: business/creator/personal)
  Acceptance criteria (agent-executable):
    - Function deployed and status "ready" (verify via `appwrite functions list` or console)
    - Function domain URL accessible — `curl https://{domain}.sgp.appwrite.run` returns a response (not 404)
    - HTTP GET without code param returns error HTML
    - HTTP GET with invalid state returns error HTML
    - After Meta Dashboard config (Task 1), full OAuth flow stores a row in creators table (verify via `tables_db_list_rows`)
  QA scenarios: 
    - Happy: `curl "https://{domain}.sgp.appwrite.run?code=VALID_CODE&state=%7B%22uid%22%3A%22test%22%2C%22clerk_id%22%3A%22test%22%7D"` → 200 + success HTML + row in DB
    - Failure: `curl "https://{domain}.sgp.appwrite.run?code=INVALID_CODE&state=..."` → 200 + error HTML, no DB row
    - Failure: `curl "https://{domain}.sgp.appwrite.run"` (no params) → 200 + error HTML
    Evidence: .omo/evidence/task-2-instagram-oauth-appwrite.md
  Commit: Y | feat(ig-oauth-callback): Appwrite Function for Instagram OAuth code exchange and token storage

- [x] 3. Appwrite Function `ig-api-proxy`: Proxy all Instagram Graph API calls with auto token refresh
  What to do:
  - Create a new Appwrite Function named `ig-api-proxy` (runtime: node-18.0, execute: ["any"], enabled: true)
  - Function code structure (Node.js 18):
    ```
    src/
      main.js          # Entry point — routes by req.path: /profile, /media, /insights, /publish, /refresh
      instagram.js     # Graph API call functions
      appwrite-db.js   # Server SDK — look up token by user, update refreshed token
      jwt-verify.js    # Verify Clerk JWT from x-appwrite-user-jwt header
      package.json     # Dependencies: node-appwrite
    ```
  - `main.js` routing logic (use `req.path`):
    - `/profile` → fetch IG profile: `GET https://graph.instagram.com/v24.0/me?fields=id,username,account_type,media_count,followers_count,follows_count,profile_picture_url,biography&access_token={TOKEN}`
    - `/media` → fetch recent media: `GET https://graph.instagram.com/v24.0/me/media?fields=id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count&limit=25&access_token={TOKEN}`
    - `/insights` → fetch insights: `GET https://graph.instagram.com/v24.0/me/insights?metric=impressions,reach,profile_views,follower_count&period=day&access_token={TOKEN}`
    - `/publish` → 2-step publish (POST body: `{image_url, caption}`):
      Step 1: `POST https://graph.instagram.com/v24.0/{IG_USER_ID}/media?image_url={URL}&caption={CAPTION}&access_token={TOKEN}` → get `creation_id`
      Step 2: `POST https://graph.instagram.com/v24.0/{IG_USER_ID}/media_publish?creation_id={ID}&access_token={TOKEN}`
    - `/refresh` → manually trigger token refresh
    - `/disconnect` → revoke token: `DELETE https://graph.instagram.com/v24.0/{IG_USER_ID}/permissions?access_token={TOKEN}`, then clear `access_token`, `token_expires_at`, `is_onboarded` in creators table
  - JWT verification: extract `x-appwrite-user-jwt` header, verify with Clerk secret key (reuse pattern from clerk-bridge function). Extract `clerk_user_id` from JWT claims.
  - Token lookup: use Appwrite Server SDK to query `creators` table where `clerk_user_id` = `{JWT.clerk_user_id}`, get `access_token`, `ig_user_id`, `token_expires_at`
  - Auto-refresh logic (before every API call):
    1. Check `token_expires_at` on the creator row
    2. If expiry < 7 days away → call `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={TOKEN}`
    3. Update `access_token` and `token_expires_at` in the creators table
    4. Use the refreshed token for the API call
    5. If token is already expired (>60 days) → return 401 JSON `{error: "token_expired", message: "Please reconnect your Instagram account"}`
  - Return JSON responses for all routes (Content-Type: application/json)
  - Set function variables: `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`, `APPWRITE_API_KEY`, `APPWRITE_ENDPOINT=https://sgp.cloud.appwrite.io/v1`, `APPWRITE_PROJECT_ID=6a4f2e330009199ecb31`, `APPWRITE_DATABASE_ID=vernacular_saas`, `APPWRITE_CREATORS_TABLE_ID=creators`, `GRAPH_API_VERSION=v24.0`, `CLERK_SECRET_KEY` (reuse from clerk-bridge)
  - Deploy the function via `appwrite push function` CLI or console upload
  - After deployment, copy the generated domain URL
  Must NOT do:
    - Do NOT return the raw access_token in API responses — return only the data
    - Do NOT accept requests without a valid JWT
    - Do NOT skip token expiry checks before API calls
    - Do NOT hardcode secrets
  Parallelization: Wave 1 | Blocked by: none | Blocks: 5
  References:
    - Appwrite project: 6a4f2e330009199ecb31 (Kapluncer, sgp)
    - Database: vernacular_saas, Table: creators
    - Existing function clerk-bridge: ID=clerk-bridge (reference for JWT verification pattern, runtime, variable: clerk-secret-key)
    - Instagram Graph API base: `https://graph.instagram.com/v24.0/`
    - Token refresh: `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={TOKEN}`
    - Profile fields: id, username, account_type, media_count, followers_count, follows_count, profile_picture_url, biography
    - Media fields: id, caption, media_type, media_url, thumbnail_url, permalink, timestamp, like_count, comments_count
    - Insights metrics: impressions, reach, profile_views, follower_count (period=day)
    - Publishing: 2-step (create media container → publish)
    - Creators table columns: access_token, ig_user_id, token_expires_at, is_onboarded, clerk_user_id
  Acceptance criteria (agent-executable):
    - Function deployed and status "ready"
    - `curl -X GET https://{domain}.sgp.appwrite.run/profile` without JWT → 401 JSON
    - `curl -X GET https://{domain}.sgp.appwrite.run/profile -H "x-appwrite-user-jwt: {valid_jwt}"` → 200 JSON with IG profile data (requires valid token in DB)
    - `curl -X GET https://{domain}.sgp.appwrite.run/media -H "x-appwrite-user-jwt: {valid_jwt}"` → 200 JSON with media array
    - Token auto-refresh triggers when token_expires_at < 7 days (verify by checking DB row updated_at changes)
  QA scenarios:
    - Happy: authenticated GET /profile with valid token → 200 + profile JSON
    - Happy: authenticated GET /media → 200 + media array
    - Failure: no JWT → 401
    - Failure: expired token (>60 days) → 401 with token_expired error
    - Failure: invalid JWT → 401
    Evidence: .omo/evidence/task-3-instagram-oauth-appwrite.md
  Commit: Y | feat(ig-api-proxy): Appwrite Function for Instagram Graph API proxy with auto token refresh

- [x] 4. Expo Go client: OAuth trigger + real-time subscription + connected state UI
  What to do:
  - Locate the Expo Go app codebase (separate from D:\0 Python CLI). Look for `app.json`, `package.json` with `expo` dependency, or `app/` directory with `.tsx` files.
  - If the app uses Expo Router, add the Instagram connection UI to the home screen route (e.g., `app/(tabs)/index.tsx` or `app/index.tsx`)
  - Create a new module `src/lib/instagram.ts` (or `app/lib/instagram.ts` matching project conventions):
    ```typescript
    // Key functions:
    // 1. getOAuthUrl(clerkUserId, appwriteUserId) → constructs the Instagram OAuth URL
    //    URL: https://api.instagram.com/oauth/authorize?client_id={IG_APP_ID}&redirect_uri={OAUTH_CALLBACK_URL}&response_type=code&scope=instagram_business_basic,instagram_business_content_publish,instagram_business_manage_comments,instagram_business_manage_insights&state={URL_ENCODED_JSON}
    //    IG_APP_ID and OAUTH_CALLBACK_URL should come from app config / environment / Appwrite function variables
    //
    // 2. connectInstagram() → opens system browser via Linking.openURL(getOAuthUrl(...))
    //
    // 3. subscribeToConnection(clerkUserId, onUpdate) → Appwrite client.subscribe(
    //      `databases.vernacular_saas.tables.creators`,
    //      (response) => { if response.events includes "databases.*.update" or "databases.*.create" &&
    //                       response.payload.clerk_user_id === clerkUserId &&
    //                       response.payload.is_onboarded === true → onUpdate(connected: true, profile: response.payload) }
    //    )
    //
    // 4. disconnectInstagram() → calls ig-api-proxy /disconnect endpoint with JWT
    //
    // 5. fetchProfile(jwt) → calls ig-api-proxy /profile endpoint
    // 6. fetchMedia(jwt) → calls ig-api-proxy /media endpoint
    // 7. fetchInsights(jwt) → calls ig-api-proxy /insights endpoint
    // 8. publishContent(jwt, imageUrl, caption) → calls ig-api-proxy /publish endpoint
    ```
  - Add UI component to home screen:
    - "Connect Instagram" button (shown when `is_onboarded` is false or null)
    - "Instagram Connected @username" badge with disconnect button (shown when `is_onboarded` is true)
    - Loading state while waiting for OAuth callback
    - Error state if subscription times out (60s) without connection
  - Use Appwrite Client SDK (`appwrite` npm package) for real-time subscription:
    ```typescript
    import { Client } from 'appwrite';
    const client = new Client()
      .setEndpoint('https://sgp.cloud.appwrite.io/v1')
      .setProject('6a4f2e330009199ecb31');
    // Subscribe after opening browser
    const unsubscribe = client.subscribe(
      `databases.vernacular_saas.tables.creators`,
      (response) => { /* check is_onboarded */ }
    );
    // Unsubscribe on unmount or after connection detected
    ```
  - Use `Linking.openURL()` from `react-native` (or `expo-linking`) to open the OAuth URL in the system browser
  - Store function URLs and IG App ID as constants or in app config (NOT secrets — the App ID is public, the secret is only on the backend)
  Must NOT do:
    - Do NOT use `expo-auth-session` or `openAuthSessionAsync()` — it doesn't work reliably on Expo Go for custom OAuth
    - Do NOT store the access token on the client — all API calls go through ig-api-proxy
    - Do NOT use `WebBrowser.openBrowserAsync()` — use `Linking.openURL()` for system browser (more reliable redirect handling)
    - Do NOT hardcode the IG App Secret — only the App ID is safe on client
    - Do NOT leave the subscription running after the component unmounts — always unsubscribe
  Parallelization: Wave 1 | Blocked by: none | Blocks: 5
  References:
    - Appwrite project: 6a4f2e330009199ecb31 (Kapluncer, sgp)
    - Appwrite endpoint: https://sgp.cloud.appwrite.io/v1
    - Database: vernacular_saas, Table: creators
    - Real-time channel: `databases.vernacular_saas.tables.creators`
    - ig-oauth-callback function URL: (from Task 2 deployment)
    - ig-api-proxy function URL: (from Task 3 deployment)
    - Instagram OAuth authorize URL: `https://api.instagram.com/oauth/authorize`
    - Scopes: `instagram_business_basic,instagram_business_content_publish,instagram_business_manage_comments,instagram_business_manage_insights`
    - Creators table fields for UI: username, profile_pic_url, is_onboarded, follower_count, account_type
    - Appwrite Client SDK docs: https://appwrite.io/docs/references/realtime
  Acceptance criteria (agent-executable):
    - "Connect Instagram" button renders on home screen
    - Tapping button opens system browser to Instagram OAuth page
    - After OAuth completes (user authorizes in browser), real-time subscription fires and UI updates to "Connected @username" within 5 seconds
    - Disconnect button clears the connected state and calls ig-api-proxy /disconnect
    - No memory leaks — subscription is cleaned up on unmount
  QA scenarios:
    - Happy: tap Connect → browser opens → authorize → return to app → UI shows "Connected @username"
    - Failure: tap Connect → browser opens → cancel authorization → return to app → UI shows "Connect" (still not connected)
    - Failure: tap Connect → browser opens → authorize but token exchange fails → UI shows error after timeout
    - Happy: tap Disconnect → UI reverts to "Connect Instagram" button
    Evidence: .omo/evidence/task-4-instagram-oauth-appwrite.md
  Commit: Y | feat(instagram-oauth): Expo Go client for Instagram OAuth with real-time subscription

- [x] 5. End-to-end integration test with tester Instagram account
  What to do:
  - Ensure Tasks 1-4 are complete:
    - Meta Dashboard has Instagram product, redirect URI set to ig-oauth-callback domain, tester added and accepted
    - ig-oauth-callback function deployed with correct variables
    - ig-api-proxy function deployed with correct variables
    - Expo Go app has the Instagram connect UI
  - Test the full flow on a physical device with Expo Go:
    1. Open the app in Expo Go
    2. Sign in via Clerk (existing auth)
    3. Tap "Connect Instagram" on home screen
    4. System browser opens → Instagram OAuth page
    5. Log in with tester Instagram account (Business/Creator)
    6. Approve the requested permissions
    7. Browser shows "Instagram Connected!" success page
    8. Return to app → UI shows "Connected @username" (via real-time subscription)
    9. Navigate to profile/media/insights views → data loads from ig-api-proxy
    10. Test disconnect → token revoked, UI reverts to "Connect Instagram"
  - Test token refresh:
    - Manually set `token_expires_at` to 5 days from now in the creators table
    - Call /profile endpoint → should auto-refresh token and update `token_expires_at` in DB
  - Test error scenarios:
    - Cancel OAuth in browser → app shows "Connect" state (no error crash)
    - Expired token (>60 days) → API proxy returns 401 with "token_expired" → app shows "Please reconnect" prompt
    - Invalid JWT → API proxy returns 401
  Must NOT do:
    - Do NOT test with a personal Instagram account — must be Business or Creator
    - Do NOT submit for App Review as part of this task
    - Do NOT test publishing with copyrighted content
  Parallelization: Wave 2 | Blocked by: 1, 2, 3, 4 | Blocks: none
  References:
    - All previous tasks
    - Tester Instagram account (configured in Task 1)
    - Expo Go app (from Task 4)
    - Appwrite functions (from Tasks 2, 3)
  Acceptance criteria (agent-executable):
    - Full OAuth flow completes: app → browser → Instagram → callback → token stored → real-time notification → UI update
    - Profile data loads via ig-api-proxy /profile
    - Media data loads via ig-api-proxy /media
    - Insights data loads via ig-api-proxy /insights
    - Token auto-refresh works when token_expires_at < 7 days
    - Disconnect flow revokes token and updates UI
    - Cancel/error scenarios don't crash the app
  QA scenarios: manual E2E on physical device with Expo Go. Evidence: .omo/evidence/task-5-instagram-oauth-appwrite.md (screenshots, log excerpts)
  Commit: N | Test-only task — no code changes

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit — verify every todo matches the plan, no scope creep, all Must-NOT-Haves respected
- [x] F2. Code quality review — verify function code has error handling, no hardcoded secrets, no token logging, clean structure
- [x] F3. Real manual QA — verify the full flow works on a physical device with Expo Go and a tester Instagram account
- [x] F4. Scope fidelity — verify no Development Build was created, no App Review submitted, token stays server-side

## Commit strategy
- Task 2: `feat(ig-oauth-callback): Appwrite Function for Instagram OAuth code exchange and token storage`
- Task 3: `feat(ig-api-proxy): Appwrite Function for Instagram Graph API proxy with auto token refresh`
- Task 4: `feat(instagram-oauth): Expo Go client for Instagram OAuth with real-time subscription`
- Tasks 1, 5: No commits (manual configuration / testing)
- Final: squash-merge after F1-F4 all approve

## Success criteria
1. User can tap "Connect Instagram" in the Expo Go app → browser opens → Instagram OAuth → token stored securely on backend → app UI updates via real-time subscription
2. App can fetch Instagram profile, media, and insights through the ig-api-proxy function (token never reaches client)
3. App can publish content to Instagram through the ig-api-proxy function
4. Token auto-refreshes when within 7 days of expiry (60-day lifecycle)
5. User can disconnect their Instagram account (token revoked, UI reverts)
6. Instagram testers can be added in Meta Dashboard (the original blocker is resolved)
7. Everything works on Expo Go — no Development Build, no custom APK, no deep linking
