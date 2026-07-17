---
slug: instagram-oauth-appwrite
status: awaiting-approval
intent: clear
pending-action: write .omo/plans/instagram-oauth-appwrite.md
approach: Backend-mediated Instagram OAuth via Appwrite Functions — Appwrite Function handles the OAuth callback, exchanges code for long-lived token, stores it in existing `creators` table. Expo Go app opens system browser to Instagram OAuth URL, subscribes to Appwrite real-time to detect token storage. Token never reaches client. All Instagram API calls proxied through a second Appwrite Function.
---

# Draft: instagram-oauth-appwrite

## Components (topology ledger)
| id | outcome (one line) | status: active|deferred | evidence path |
| --- | --- | --- | --- |
| meta-dashboard | Instagram product added to Meta app, OAuth redirect configured, testers added | active | Meta App Dashboard |
| ig-oauth-callback | Appwrite Function: receives OAuth code, exchanges for long-lived token, stores in creators table | active | New function `ig-oauth-callback` |
| ig-api-proxy | Appwrite Function: proxies all Instagram Graph API calls (profile, media, insights, publish) with auto token refresh | active | New function `ig-api-proxy` |
| expo-client | Expo Go module: opens browser to OAuth URL, subscribes to Appwrite real-time, shows connected state | active | Expo app (separate repo) |

## Open assumptions (announced defaults)
Record any default you adopt instead of asking, so the user can veto it at the gate.
| assumption | adopted default | rationale | reversible? |
| --- | --- | --- | --- |
| Expo app location | Expo app is in a separate directory/repo from D:\0 (Python CLI). Worker locates it. | D:\0 has no .tsx/.jsx/.ts files or app.json — it's the Python CrewAI CLI. | Yes |
| OAuth approach | Instagram API with Instagram Login (direct IG OAuth, not Facebook Login for Business) | Simpler, single-account, user-approved in brainstorming session | Yes |
| Token storage | Store in existing `creators` table (already has access_token, ig_user_id, token_expires_at, clerk_user_id columns) | Schema already prepared (columns added 2026-07-15) | Yes |
| Real-time detection | Appwrite real-time subscription on creators table, filtered by clerk_user_id | Most reliable on Expo Go — no deep linking needed | Yes |
| State parameter | JSON `{uid: appwrite_user_id, clerk_id: clerk_user_id}` URL-encoded in OAuth state | Function needs appwrite_user_id for row permissions, clerk_id for lookup | Yes |
| Function runtime | Node.js 18 (matching existing clerk-bridge function) | Consistency with existing Appwrite setup | Yes |
| Graph API version | v24.0 | Latest stable as of research date | Yes |

## Findings (cited)
- Appwrite project: `6a4f2e330009199ecb31` (Kapluncer, Singapore region)
- Database: `vernacular_saas` (TablesDB), 5 tables
- Existing function: `clerk-bridge` (node-18.0, execute: any, var: clerk-secret-key)
- `creators` table (ID: `creators`): has ig_user_id (unique index), ig_scoped_id, access_token (size 2048), token_expires_at, is_onboarded (bool), clerk_user_id (indexed), account_type (enum: business/creator/personal), rowSecurity: true
- Expo Go CANNOT do OAuth (Expo docs: "Expo Go cannot be used for local development and testing of OAuth-enabled apps")
- Appwrite Functions get HTTP endpoint URL (e.g., `https://xxx.sgp.appwrite.run`) — any HTTP method triggers the function
- Instagram Basic Display API deprecated Dec 4, 2024 — only Instagram Graph API works now
- Requires Business/Creator account linked to Facebook Page (for Facebook Login) OR direct Instagram Business Login
- Instagram OAuth authorize: `GET https://api.instagram.com/oauth/authorize?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES}&state={STATE}`
- Token exchange: `POST https://api.instagram.com/oauth/access_token`
- Long-lived exchange: `GET https://graph.instagram.com/access_token?grant_type=ig_exchange_token`
- Token refresh: `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token`
- Scopes needed (full access + publishing): `instagram_business_basic,instagram_business_content_publish,instagram_business_manage_comments,instagram_business_manage_insights`
- Long-lived tokens expire in 60 days — must refresh proactively
- Tester issue root cause: likely Instagram product not added to Meta app → "Instagram Testers" section doesn't appear in Roles

## Decisions (with rationale)
1. **Backend-mediated OAuth via Appwrite Function** — user approved in brainstorming. Token stays on backend, works on Expo Go, uses existing infrastructure.
2. **Two separate functions** (not one) — `ig-oauth-callback` (HTTP GET handler, execute: any) and `ig-api-proxy` (HTTP endpoint for app calls, execute: any). Separation of concerns: callback is public (Instagram redirect), proxy is for app calls (JWT-authenticated).
3. **Store token in existing `creators` table** — schema already has all needed columns. No new table.
4. **Real-time subscription for completion detection** — more reliable than deep linking on Expo Go.

## Scope IN
- Meta App Dashboard: add Instagram product, configure OAuth redirect URI, add Instagram testers, configure scopes
- Appwrite Function `ig-oauth-callback`: HTTP GET handler, code→token exchange, long-lived exchange, fetch IG profile, store in creators table
- Appwrite Function `ig-api-proxy`: HTTP endpoint for app calls (profile, media, insights, publish), auto token refresh, JWT verification
- Expo Go client: OAuth trigger button, real-time subscription, connected/disconnected state UI, disconnect flow
- Token auto-refresh logic in ig-api-proxy

## Scope OUT (Must NOT have)
- No Expo Development Build / dev-client — stay on Expo Go
- No custom URI scheme / deep linking for OAuth redirect
- No client-side token storage — token NEVER leaves the backend
- No Meta App Review submission (Development mode only — testers only)
- No Facebook Login for Business (using direct Instagram Login instead)
- No new database tables — use existing `creators` table
- No instagrapi integration in this plan (separate from the Python CLI system)

## Open questions
None — all resolved through brainstorming.

## Approval gate
status: awaiting-approval
User approved Approach 1 in brainstorming session. Plan is decision-complete. Waiting for explicit okay to write the plan file.
