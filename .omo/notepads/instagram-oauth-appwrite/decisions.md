# Instagram OAuth Appwrite Plan - Decisions

## 2026-07-17
1. Backend-mediated OAuth via Appwrite Functions - user approved in brainstorming
2. Instagram API with Instagram Login (direct, not Facebook Login for Business)
3. Token stored in existing creators table (schema already has columns)
4. Two separate functions: ig-oauth-callback (HTTP GET handler) + ig-api-proxy (HTTP endpoint)
5. Real-time subscription for auth completion detection (not deep linking)
6. State parameter: JSON {uid, clerk_id} URL-encoded
7. Graph API version v24.0
8. Expo app at D:\creator-workspace - functions code goes in D:\creator-workspace\functions/
