/**
 * api.js — Fetch wrapper for the backend API.
 */

const API_BASE = '/api';

/**
 * Send a chat message to the backend.
 *
 * @param {string} message - The user's message text.
 * @param {string} sessionId - The session identifier.
 * @returns {Promise<{reply: string, type: string, sources?: string[]}>}
 */
export async function sendMessage(message, sessionId) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Check if the backend API is healthy.
 *
 * @returns {Promise<{status: string, service: string}>}
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

/**
 * Get session history from the backend.
 *
 * @param {string} sessionId - The session identifier.
 * @returns {Promise<{session_id: string, messages: Array}>}
 */
export async function getSessionHistory(sessionId) {
  const response = await fetch(`${API_BASE}/session/${sessionId}/history`);
  if (!response.ok) {
    throw new Error(`Session history fetch failed: ${response.status}`);
  }
  return response.json();
}
