/**
 * Auth Session Management (HttpOnly Cookie Architecture)
 *
 * Tokens are now managed securely by the browser via HttpOnly session cookies.
 * This file removes legacy storage tokens and provides helpers for session cleanup.
 */

const ACCESS_TOKEN_KEY = "access_token";
const TOKEN_TYPE_KEY = "token_type";

// Immediately clean up any legacy tokens stored in localStorage/sessionStorage
export function purgeLegacyStorageTokens() {
  try {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_TYPE_KEY);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(TOKEN_TYPE_KEY);
  } catch {
    // Storage access might be restricted in some environments
  }
}

// Run purge immediately on module evaluation
purgeLegacyStorageTokens();

export function getAuthToken() {
  // Authentication is now cookie-driven (HttpOnly) and inaccessible to JS.
  return null;
}

export function saveAuthSession() {
  // No-op: Authentication is stored exclusively in HttpOnly cookies by the server.
  purgeLegacyStorageTokens();
}

export function clearAuthSession() {
  purgeLegacyStorageTokens();
}
