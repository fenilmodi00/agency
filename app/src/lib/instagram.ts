import { account } from './appwrite';

/**
 * Instagram FastAPI helper functions.
 *
 * Replaced Graph API OAuth flow with FastAPI backend calls:
 * - loginInstagram(): POSTs credentials to FastAPI /login
 * - fetchProfile(): GETs profile from FastAPI /profile
 * - fetchMedia(): GETs media from FastAPI /media?amount=25
 * - fetchInsights(): GETs insights from FastAPI /insights
 * - disconnectInstagram(): POSTs disconnect to FastAPI /disconnect
 *
 * All endpoints use JWT auth via getAuthHeaders() (x-appwrite-user-jwt header).
 */

// FastAPI base URL (ngrok URL for local dev, production URL for deployed)
const API_BASE_URL = process.env.EXPO_PUBLIC_IG_API_BASE_URL || '';

/**
 * Returns auth headers with Appwrite JWT for FastAPI endpoint calls.
 */
async function getAuthHeaders(): Promise<HeadersInit> {
  const jwt = await account.createJWT();
  return {
    'x-appwrite-user-jwt': jwt.jwt,
    'Content-Type': 'application/json',
  };
}

/**
 * Instagram profile response matching instagrapi user_info output.
 */
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

/**
 * Instagram media response matching instagrapi user_medias output.
 */
export interface InstagramMediaResponse {
  pk: string;
  caption_text: string | null;
  media_type: number;
  thumbnail_url: string | null;
  media_url: string | null;
  permalink: string;
  taken_at: number;
  like_count: number;
  comment_count: number;
  view_count: number;
  play_count: number;
}

/**
 * Instagram insights response.
 */
export interface InstagramInsightsResponse {
  data: Array<{
    name: string;
    period: string;
    values: Array<{ value: number; end_time: string }>;
  }>;
  error?: string;
}

/**
 * Logs in to Instagram via the FastAPI backend.
 * Sends credentials to /login — credentials are NOT stored client-side.
 *
 * @throws Error("Invalid credentials") on 401
 * @throws Error("Instagram login failed") on 502 or other non-200
 */
export async function loginInstagram(
  clerkId: string,
  username: string,
  password: string
): Promise<InstagramProfileResponse> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      clerk_id: clerkId,
      username,
      password,
    }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Invalid credentials');
    }
    throw new Error('Instagram login failed');
  }

  return response.json();
}

/**
 * Fetches the current user's Instagram profile from the FastAPI backend.
 * No params — the JWT identifies the user.
 *
 * @throws Error("session_expired") on 401
 */
export async function fetchProfile(): Promise<InstagramProfileResponse> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/profile`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('session_expired');
    }
    throw new Error(`Fetch profile failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetches the current user's Instagram media from the FastAPI backend.
 * Returns up to 25 media items.
 */
export async function fetchMedia(): Promise<InstagramMediaResponse[]> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/media?amount=25`, {
    method: 'GET',
    headers,
  });

  return response.json();
}

/**
 * Fetches Instagram insights from the FastAPI backend.
 * Returns insights data or an error object — callers handle gracefully.
 * Does NOT throw on non-200 or business-account errors.
 */
export async function fetchInsights(): Promise<InstagramInsightsResponse> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/insights`, {
    method: 'GET',
    headers,
  });

  return response.json();
}

/**
 * Disconnects Instagram session via the FastAPI backend.
 */
export async function disconnectInstagram(): Promise<void> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/disconnect`, {
    method: 'POST',
    headers,
  });

  if (!response.ok) {
    throw new Error(`Disconnect failed: ${response.statusText}`);
  }
}

/**
 * Validates whether an account type string is BUSINESS or CREATOR.
 */
export function isValidAccountType(
  accountType: string
): accountType is 'BUSINESS' | 'CREATOR' {
  return accountType === 'BUSINESS' || accountType === 'CREATOR';
}

/**
 * Maps Instagram account type strings to the app's internal type.
 */
export function mapAccountType(
  igAccountType: string
): 'business' | 'creator' | 'personal' {
  switch (igAccountType) {
    case 'BUSINESS':
      return 'business';
    case 'CREATOR':
      return 'creator';
    default:
      return 'personal';
  }
}

/**
 * Returns an ISO date string 60 days from now.
 */
export function getTokenExpiryDate(): string {
  const now = new Date();
  now.setDate(now.getDate() + 60);
  return now.toISOString();
}
