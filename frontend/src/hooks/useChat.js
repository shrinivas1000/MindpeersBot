/**
 * useChat — custom hook for chat state management.
 *
 * Manages messages, session ID, loading state, and send logic.
 * Generates a session ID on mount (crypto.randomUUID).
 */

import { useState, useCallback, useRef } from 'react';
import { sendMessage } from '../services/api';

/**
 * Generate a unique session ID.
 */
function generateSessionId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for environments without crypto.randomUUID
  return 'session-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
}

let messageIdCounter = 0;
function nextMessageId() {
  return `msg-${++messageIdCounter}`;
}

export default function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const sessionIdRef = useRef(generateSessionId());

  const sessionId = sessionIdRef.current;
  const hasStarted = messages.length > 0;

  const send = useCallback(async (text) => {
    if (!text.trim() || isLoading) return;

    setError(null);

    // Add user message to the list immediately
    const userMsg = {
      id: nextMessageId(),
      role: 'user',
      content: text,
      type: 'normal',
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await sendMessage(text, sessionId);

      const assistantMsg = {
        id: nextMessageId(),
        role: 'assistant',
        content: response.reply,
        type: response.type,
        sources: response.sources || null,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Chat send error:', err);
      setError('Something went wrong. Please try again.');

      // Add a fallback error message so the user sees feedback
      const errorMsg = {
        id: nextMessageId(),
        role: 'assistant',
        content:
          'I am having a moment of difficulty connecting. Please try again in a moment. ' +
          'If you are in crisis, please reach out to Tele MANAS at 14416 or KIRAN at 1800-599-0019.',
        type: 'normal',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, sessionId]);

  return {
    messages,
    isLoading,
    error,
    hasStarted,
    sessionId,
    send,
  };
}
