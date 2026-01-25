/**
 * API configuration - Code simplification Phase 3.
 *
 * Centralizes API base URL configuration currently hardcoded in 10+ files.
 * Single source of truth for API endpoints.
 */

/**
 * API base URL from environment variable.
 * Defaults to localhost for development.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Common API endpoints.
 */
export const API_ENDPOINTS = {
  insights: `${API_BASE_URL}/api/insights`,
  dailyTop: `${API_BASE_URL}/api/insights/daily-top`,
  research: `${API_BASE_URL}/api/research`,
  admin: `${API_BASE_URL}/api/admin`,
  users: `${API_BASE_URL}/api/users`,
} as const;
