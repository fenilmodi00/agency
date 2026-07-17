# Instagram OAuth Appwrite Plan - Learnings

## 2026-07-17 Atlas Session Start
- Appwrite project: 6a4f2e330009199ecb31 (Kapluncer, sgp region)
- Appwrite endpoint: https://sgp.cloud.appwrite.io/v1
- Database: vernacular_saas (TablesDB), 5 tables
- Existing function: clerk-bridge (node-18.0, execute: any, var: clerk-secret-key)
- Creators table already has: ig_user_id (unique idx), ig_scoped_id, access_token (2048), token_expires_at, is_onboarded, clerk_user_id (idx), account_type (enum: business/creator/personal)
- Expo app at: D:\creator-workspace (Expo Router, Tamagui, Appwrite SDK 26.2.0, Clerk 2.19.31)
- Existing instagram.ts uses OLD approach (expo-auth-session + Facebook OAuth v19.0) - needs rewrite to Linking.openURL + Appwrite real-time
- Real-time hook already exists: useRealtimeSubscription(channels, callback) in src/lib/realtime.ts
- Constants: DATABASE_ID='vernacular_saas', TABLES.CREATORS='creators'
- Env vars: EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY, EXPO_PUBLIC_APPWRITE_ENDPOINT, EXPO_PUBLIC_APPWRITE_PROJECT_ID
- app.json: scheme='creatorworkspace', plugins include expo-web-browser, expo-secure-store, expo-router
- Home screen: src/app/(tabs)/(home)/index.tsx - basic placeholder
- No functions/ directory exists locally - will create D:\creator-workspace\functions/

## 2026-07-17 ig-api-proxy Function Created
- Created D:\creator-workspace\functions\ig-api-proxy\ with 5 files:
  - `package.json` — deps: node-appwrite only
  - `src/main.js` — Entry point: routes /profile, /media, /insights, /publish, /refresh, /disconnect
  - `src/instagram.js` — Graph API functions: getProfile, getMedia, getInsights, createMediaContainer, publishMediaContainer, refreshToken, revokePermissions, ensureValidToken
  - `src/appwrite-db.js` — TablesDB: getCreatorByClerkId, updateCreatorToken, clearCreatorInstagramFields
  - `src/jwt-verify.js` — Clerk JWT decoding + validation (checks exp, sub)
- All JS files pass `node --check` syntax validation
- Token auto-refresh: checks `token_expires_at` before each call, refreshes if <7 days remaining
- Routes accept `clerk_id` from query param or bodyJson
- Uses `req.headers['x-appwrite-key']` for dynamic auth, `req.headers['x-appwrite-user-jwt']` for JWT
- IG API endpoints confirmed for v24.0:
  - Profile: GET /me?fields=id,username,account_type,media_count,followers_count,follows_count,profile_picture_url,biography
  - Media: GET /me/media?fields=id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count&limit=25
  - Insights: GET /me/insights?metric=impressions,reach,profile_views,follower_count&period=day
  - Publish Step 1: POST /{ig_user_id}/media?image_url={URL}&caption={CAPTION}
  - Publish Step 2: POST /{ig_user_id}/media_publish?creation_id={ID}
  - Refresh: GET /refresh_access_token?grant_type=ig_refresh_token&access_token={TOKEN}
  - Revoke: DELETE /{ig_user_id}/permissions
- Created ig-oauth-callback function at D:\creator-workspace\functions\ig-oauth-callback\
  - src/main.js — Appwrite Function entry point (HTTP GET, parses code+state, orchestrates OAuth flow)
  - src/instagram.js — exchangeCodeForShortToken(), exchangeForLongToken(), fetchInstagramProfile(), calculateTokenExpiry()
  - src/appwrite-db.js — createAppwriteClient(), findCreatorByClerkId(), updateCreatorRow(), createCreatorRow(), buildCreatorData()
  - src/success-page.js — successPage(username), errorPage(message) with HTML + CSS
  - package.json — type: "module", deps: node-appwrite
- All 4 source files pass `node --check` syntax validation
- Uses dynamic x-appwrite-key header, all env vars from process.env, try/catch on every fetch

## 2026-07-17 F1/F2 Review Fixes Applied
- Fixed 8 code issues identified by Final Wave reviewers:
  1. `ig-oauth-callback/src/appwrite-db.js`: Added `ig_scoped_id: profile.id` to `buildCreatorData()` (was missing per plan requirement).
  2. `ig-api-proxy/src/main.js`: Fixed security vuln — `clerkUserId` now comes from JWT `sub` only; if query `clerk_id` differs from JWT sub, returns 403.
  3. `ig-api-proxy/src/jwt-verify.js`: Removed unused `CLERK_SECRET_KEY` const; added `appwriteUserId` param for cross-check against `x-appwrite-user-id` header; updated comments to accurately reflect Appwrite JWT (not Clerk JWT).
  4. `src/lib/instagram.ts`: Replaced 3x `Promise<any>` with `Promise<InstagramMediaResponse>`, `Promise<InstagramInsightsResponse>`, `Promise<InstagramPublishResponse>`.
  5. `src/app/(tabs)/(home)/index.tsx`: Replaced `event: any` with `RealtimeResponseEvent<unknown>` + typed `CreatorPayload` cast.
  6. Same file: Added `useRef`-based timeout management — timeout ID stored in ref, cleared on successful connection, cleaned up on unmount via dedicated `useEffect`.
  7. Same file: Moved `fetchProfile` outside component as `fetchCreatorProfile()` — no longer re-created per render, `useEffect` depends only on `[user]`.
  8. Same file: Fixed `catch (e: any)` → `catch (e: unknown)` with `instanceof Error` check.
