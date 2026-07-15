/**
 * InputBar — text input + mic button + send button for composing messages.
 *
 * State machine:
 *   IDLE       → textarea editable, mic button starts listening
 *   LISTENING  → textarea read-only (shows typed prefix + live speech),
 *                mic button stops, send button stops + sends
 *   IDLE       → speech committed into text, fully editable again
 *
 * Features:
 * - Auto-expanding textarea (up to 4 lines)
 * - Send on Enter (Shift+Enter for newline)
 * - Voice input via Web Speech API (Chrome/Edge) — hidden in unsupported browsers
 * - Textarea is read-only during listening — no keyboard conflicts
 * - When speech stops, transcript lands in the field and user can type from there
 * - Send while listening: stops mic, grabs final text, sends atomically
 * - Disabled state while loading
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import useSpeechRecognition from '../../hooks/useSpeechRecognition';
import './InputBar.css';

export default function InputBar({ onSend, isLoading }) {
  // Committed text — only modified by keyboard input (idle) or speech commit (on stop)
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  // Ref mirror of `text` for async callbacks (avoids stale closures)
  const textRef = useRef('');

  // Guards the commit effect from firing during a send-while-listening flow
  const isSendingRef = useRef(false);

  const {
    isSupported: isSpeechSupported,
    isListening,
    finalText,
    interimText,
    error: speechError,
    startListening,
    stopListening,
    reset: resetSpeech,
  } = useSpeechRecognition();

  // Keep textRef in sync with state
  const updateText = useCallback((newText) => {
    textRef.current = newText;
    setText(newText);
  }, []);

  // ── Display value ───────────────────────────────────────────────────
  // Idle:      show committed text (editable)
  // Listening: show committed text + live speech (read-only)
  const displayValue = (() => {
    if (!isListening) return text;
    const speech = finalText + (interimText || '');
    if (!speech) return text;
    const sep = text && !text.endsWith(' ') ? ' ' : '';
    return text + sep + speech;
  })();

  // ── Commit speech when listening stops naturally ────────────────────
  // (silence timeout, max duration, or manual mic-off click)
  const prevListeningRef = useRef(false);
  useEffect(() => {
    const wasListening = prevListeningRef.current;
    prevListeningRef.current = isListening;

    if (wasListening && !isListening && !isSendingRef.current) {
      if (finalText) {
        const current = textRef.current;
        const sep = current && !current.endsWith(' ') ? ' ' : '';
        updateText(current + sep + finalText);
      }
      resetSpeech();
    }
  }, [isListening, finalText, resetSpeech, updateText]);

  // ── Auto-resize textarea (covers both typed and speech-injected text)
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, [displayValue]);

  // ── Focus textarea when listening stops so user can type immediately
  useEffect(() => {
    if (!isListening && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isListening]);

  // ── Clear everything ───────────────────────────────────────────────
  const clearInput = useCallback(() => {
    updateText('');
    resetSpeech();
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [updateText, resetSpeech]);

  // ── Submit handler ─────────────────────────────────────────────────
  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (isLoading) return;

    if (isListening) {
      // Atomic stop-and-send: stop mic → grab final transcript → send → clear
      isSendingRef.current = true;
      const speechFinal = await stopListening();
      const current = textRef.current;
      const sep = current && !current.endsWith(' ') ? ' ' : '';
      const fullMessage = (current + (speechFinal ? sep + speechFinal : '')).trim();

      if (fullMessage) {
        onSend(fullMessage);
        clearInput();
      }
      isSendingRef.current = false;
    } else {
      const trimmed = text.trim();
      if (trimmed) {
        onSend(trimmed);
        clearInput();
      }
    }
  }, [isLoading, isListening, stopListening, text, onSend, clearInput]);

  // ── Keyboard handling ──────────────────────────────────────────────
  // Enter fires even on readOnly textareas, so send-while-listening works
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  // ── Typing (only fires when not readOnly, i.e., not listening) ─────
  const handleChange = useCallback((e) => {
    updateText(e.target.value);
  }, [updateText]);

  // ── Mic toggle ─────────────────────────────────────────────────────
  const handleMicClick = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, stopListening, startListening]);

  const placeholder = isListening
    ? 'Listening...'
    : "Type how you're feeling...";

  return (
    <form className="input-bar" onSubmit={handleSubmit} id="input-bar-form">
      <div className="input-bar__wrapper">
        <textarea
          ref={textareaRef}
          className="input-bar__input"
          id="chat-input"
          value={displayValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          readOnly={isListening}
          rows={1}
          aria-label="Message input"
        />

        {/* Mic button — only rendered if Web Speech API is available */}
        {isSpeechSupported && (
          <button
            type="button"
            className={`input-bar__mic ${isListening ? 'input-bar__mic--listening' : ''}`}
            id="mic-button"
            onClick={handleMicClick}
            disabled={isLoading}
            aria-label={isListening ? 'Stop listening' : 'Start voice input'}
            title={isListening ? 'Stop listening' : 'Voice input'}
          >
            {isListening ? (
              /* Stop icon — small square */
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
              /* Mic icon */
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            )}
          </button>
        )}

        <button
          type="submit"
          className="input-bar__send"
          id="send-button"
          disabled={!displayValue.trim() || isLoading}
          aria-label="Send message"
        >
          {isLoading ? (
            <span className="input-bar__spinner" aria-hidden="true"></span>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>

      {/* Speech error message — auto-dismisses after 3s */}
      {speechError && (
        <div className="input-bar__speech-error" role="alert">
          {speechError}
        </div>
      )}
    </form>
  );
}
