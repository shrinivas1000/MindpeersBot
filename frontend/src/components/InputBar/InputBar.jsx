/**
 * InputBar — text input + mic button + send button for composing messages.
 *
 * Features:
 * - Auto-expanding textarea (up to 4 lines)
 * - Send on Enter (Shift+Enter for newline)
 * - Voice input via Web Speech API (Chrome/Edge) — hidden in unsupported browsers
 * - Real-time speech-to-text: input field updates as the user speaks
 * - Disabled state while loading
 * - No emojis in placeholder or labels
 */

import { useState, useRef, useEffect } from 'react';
import useSpeechRecognition from '../../hooks/useSpeechRecognition';
import './InputBar.css';

export default function InputBar({ onSend, isLoading }) {
  const [text, setText] = useState('');
  // Text that was in the input before the user started speaking
  const preListeningTextRef = useRef('');
  const textareaRef = useRef(null);

  const {
    isSupported: isSpeechSupported,
    isListening,
    finalText,
    interimText,
    error: speechError,
    startListening,
    stopListening,
  } = useSpeechRecognition();

  // Snapshot the current text when listening starts
  useEffect(() => {
    if (isListening) {
      preListeningTextRef.current = text;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isListening]);

  // Update the text field in real-time as speech is recognized
  useEffect(() => {
    if (!isListening && !finalText && !interimText) return;

    const prefix = preListeningTextRef.current;
    const separator = prefix && !prefix.endsWith(' ') ? ' ' : '';
    const liveText = finalText + (interimText ? interimText : '');

    if (liveText) {
      setText(prefix + separator + liveText);
    }
  }, [finalText, interimText, isListening]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (trimmed && !isLoading) {
      onSend(trimmed);
      setText('');
      preListeningTextRef.current = '';
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleChange = (e) => {
    setText(e.target.value);
    // Auto-resize textarea
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  };

  const handleMicClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

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
