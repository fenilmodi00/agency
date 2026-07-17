---
slug: instagrapi-mvp-diversion
status: plan-written
intent: clear
review_required: false
pending-action: none (plan written, awaiting user to start work)
approach: Extend ig_client.py + FastAPI backend + rewrite Expo instagram.ts. 6 tasks, 3 waves. Local+ngrok deployment.
---

# Draft: instagrapi-mvp-diversion

## Components (topology ledger)
1. **FastAPI backend** (new, D:\0/api/) — Python HTTP server extending ig_client.py. status: active
2. **Expo app Instagram module** (D:\creator-workspace/src/lib/instagram.ts) — rewrite from Graph API to FastAPI. status: active
3. **Expo app screens/hooks** (home/index.tsx, useCreatorProfile.ts) — login form + media/insights. status: active
4. **Deployment & env config** — local+ngrok, env vars. status: active

## Open assumptions (announced defaults)
- Publishing endpoints deferred (no publishing UI in Expo app) — reversible, add later
- DM endpoints deferred (DMs handled by Python CLI, not Expo app) — reversible, add later
- Local+ngrok for MVP (Nebius $50 credit reserved for later) — reversible, deploy when validated

## Findings (cited)
- ig_client.py:65-392 — existing InstagramClient with login, DM, thread, user lookup methods
- ig_client.py LACKS: fetch_profile, fetch_media, fetch_insights, logout (to be added)
- tools/instagram_tools.py:114-141 — existing get_profile() tool calls cl.user_info_from_username()
- creator-workspace/src/lib/instagram.ts:1-208 — current Graph API integration (OAuth + proxy calls)
- creator-workspace/src/app/(tabs)/(home)/index.tsx:1-152 — home screen with OAuth Connect button
- creator-workspace/src/hooks/ — useCreatorProfile, useThreads, useMessages, useDashboard (all read Appwrite)
- creator-workspace/.env:4-7 — CLERK_SECRET_KEY, APPWRITE_API_KEY, APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID
- Appwrite project 6a4f2e330009199ecb31, database vernacular_saas, table creators (rowSecurity: true)
- Existing plan instagram-oauth-appwrite.md: Tasks 2-4 done, Tasks 1+5 blocked (Meta App Review)
- instagrapi capabilities verified (librarian, commit 0759c11): all 9 operations supported

## Decisions (with rationale)
1. **Auth: Reuse Clerk JWT** — FastAPI verifies with CLERK_SECRET_KEY via PyJWT. Consistent with existing approach, most secure.
2. **Deployment: Local + ngrok** — zero cost, full debug access, Nebius credit reserved for later.
3. **Data persistence: FastAPI stores in Appwrite** — /login stores profile in creators table. Existing hooks need ZERO changes.
4. **Publishing deferred** — no publishing UI in Expo app (profile screen is "Coming soon" placeholder).
5. **Singleton vs registry** — InstagramClient gets session_file_path param; get_ig_client() singleton unchanged.
6. **Session expiry** — FastAPI returns 401 session_expired; Expo app shows login form again.
7. **LRU eviction** — SessionManager MAX_SESSIONS=50, evicts oldest on overflow.

## Scope IN
- Extend ig_client.py: fetch_profile, fetch_media, fetch_insights, logout + per-user session support
- FastAPI backend: /login, /profile, /media, /insights, /disconnect (5 endpoints)
- Expo instagram.ts rewrite: loginInstagram, fetchProfile, fetchMedia, fetchInsights, disconnectInstagram
- Expo home screen: username+password form, connected badge, media/insights display
- useCreatorProfile: extend with media/insights fetching from FastAPI
- ngrok + env config + E2E test

## Scope OUT (Must NOT have)
- NO changes to Appwrite Functions (ig-oauth-callback, ig-api-proxy, clerk-bridge)
- NO changes to Python CLI CrewAI agents (agents/, crew.py, main.py, check_replies.py)
- NO changes to get_ig_client() singleton
- NO publishing endpoints (/publish)
- NO DM endpoints (/dm-send, /dm-threads)
- NO cloud deployment (local+ngrok only)
- NO OAuth flow
- NO print() or stdlib logging

## Open questions
None — all resolved.

## Approval gate
status: plan-written
Plan file: .omo/plans/instagrapi-mvp-diversion.md (546 lines)
Metis gap analysis: COMPLETED (bg_b23c0960) — findings folded in
Review required: false
User approved approach on 2026-07-17
