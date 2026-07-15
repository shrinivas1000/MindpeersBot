/**
 * InputBar — text input + mic button + send button for composing messages.
 *
 * Features:
 * - Auto-expanding textarea (up to 4 lines)
 * - Send on Enter (Shift+Enter for newline)
 * - Voice input via Web Speech API (Chrome/Edge) — hidden in unsupported browsers
 * - Real-time speech-to-text: input field updates as the user speaks
 * - Typing during voice: new keystrokes are appended after the speech text
 * - Send while listening: stops mic, grabs final transcript, sends immediately
 * - Disabled state while loading
 * - No emojis in placeholder or labels
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import useSpeechRecognition from '../../hooks/useSpeechRecognition';
import './InputBar.css';

export default function InputBar({ onSend, isLoading }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  // Tracks the portion of `text` that came from the keyboard (typed before
  // or during a listening session). Speech output is appended after this.
  const typedTextRef = useRef('');

  // Guard: prevents the speech-sync effect from running after we've already
  // consumed the transcript (e.g. after send).
  const suppressSpeechSyncRef = useRef(false);

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

  // ── Sync speech transcript into the text field in real-time ──────────
  useEffect(() => {
    if (suppressSpeechSyncRef.current) return;
    if (!isListening && !finalText && !interimText) return;

    const typed = typedTextRef.current;
    const separator = typed && !typed.endsWith(' ') ? ' ' : '';
    const speechPart = finalText + (interimText || '');

    if (speechPart) {
      setText(typed + separator + speechPart);
    }
  }, [finalText, interimText, isListening]);

  // ── When listening stops naturally (silence timeout / max duration),
  //    commit the final speech text into typedTextRef so subsequent
  //    keystrokes append correctly. ─────────────────────────────────────
  const prevListeningRef = useRef(false);
  useEffect(() => {
    if (prevListeningRef.current && !isListening) {
      // Listening just ended — if not suppressed, commit the current
      // text as the new "typed" baseline.
      if (!suppressSpeechSyncRef.current) {
        typedTextRef.current = text;
      }
    }
    prevListeningRef.current = isListening;
  }, [isListening, text]);

  // ── Auto-resize textarea helper ─────────────────────────────────────
  const resizeTextarea = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, []);

  // Resize whenever text changes (covers speech-injected text too)
  useEffect(() => {
    resizeTextarea();
  }, [text, resizeTextarea]);

  // ── Send logic ──────────────────────────────────────────────────────
  const doSend = useCallback((messageText) => {
    const trimmed = messageText.trim();
    if (!trimmed || isLoading) return;

    // Suppress speech sync so onend doesn't resurrect the text
    suppressSpeechSyncRef.current = true;

    onSend(trimmed);
    setText('');
    typedTextRef.current = '';
    resetSpeech();

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Re-enable speech sync after a tick (for the next interaction)
    requestAnimationFrame(() => {
      suppressSpeechSyncRef.current = false;
    });
  }, [isLoading, onSend, resetSpeech]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();

    if (isListening) {
      // Stop the mic and grab the final transcript before sending.
      // This ensures we capture any in-flight interim text.
      const speechFinal = await stopListening();
      const typed = typedTextRef.current;
      const separator = typed && !typed.endsWith(' ') ? ' ' : '';
      const fullMessage = typed + (speechFinal ? separator + speechFinal : '');
      doSend(fullMessage);
    } else {
      doSend(text);
    }
  }, [isListening, stopListening, text, doSend]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  const handleChange = useCallback((e) => {
    const newValue = e.target.value;
    setText(newValue);

    // If listening, update the typed portion to be everything the user
    // has in the box minus the current speech output. This handles the
    // case where the user types additional text while speaking.
    if (isListening) {
      const speechPart = finalText + (interimText || '');
      if (speechPart && newValue.endsWith(speechPart)) {
        // User is editing before the speech portion
        typedTextRef.current = newValue.slice(0, newValue.length - speechPart.length).trimEnd();
      } else {
        // User is editing/appending freely — treat the whole thing as typed
        typedTextRef.current = newValue;
      }
    } else {
      // Not listening: all text is "typed"
      typedTextRef.current = newValue;
    }
  }, [isListening, finalText, interimText]);

  const handleMicClick = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      // Snapshot whatever is currently typed as the prefix
      typedTextRef.current = text;
      suppressSpeechSyncRef.current = false;
      startListening();
    }
  }, [isListening, stopListening, startListening, text]);

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
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
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
          disabled={!text.trim() || isLoading}
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
