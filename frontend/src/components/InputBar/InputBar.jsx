/**
 * InputBar — text input + send button for composing messages.
 *
 * Features:
 * - Auto-expanding textarea (up to 4 lines)
 * - Send on Enter (Shift+Enter for newline)
 * - Disabled state while loading
 * - No emojis in placeholder or labels
 */

import { useState, useRef } from 'react';
import './InputBar.css';

export default function InputBar({ onSend, isLoading }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (trimmed && !isLoading) {
      onSend(trimmed);
      setText('');
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
          placeholder="Type how you're feeling..."
          disabled={isLoading}
          rows={1}
          aria-label="Message input"
        />
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
    </form>
  );
}
