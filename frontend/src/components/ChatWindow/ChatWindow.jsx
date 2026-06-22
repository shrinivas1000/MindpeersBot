/**
 * ChatWindow — the main conversation view.
 *
 * Has the same gradient graphic from the landing page as a static backdrop.
 * A minimal floating bar shows "MindBridge" + online status.
 * Messages, typing indicator, and input bar at the bottom.
 */

import { useEffect, useRef } from 'react';
import MessageBubble from '../MessageBubble/MessageBubble';
import CrisisBanner from '../CrisisBanner/CrisisBanner';
import InputBar from '../InputBar/InputBar';
import './ChatWindow.css';

export default function ChatWindow({ messages, onSendMessage, isLoading }) {
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  return (
    <div className="chat-window" id="chat-window">
      {/* Static gradient backdrop — same as landing page */}
      <div className="chat-window__backdrop" aria-hidden="true">
        <div className="chat-window__orb chat-window__orb--1" />
        <div className="chat-window__orb chat-window__orb--2" />
        <div className="chat-window__orb chat-window__orb--3" />
        <div className="chat-window__orb chat-window__orb--4" />
        <div className="chat-window__grain" />
      </div>

      {/* Floating status bar */}
      <div className="chat-window__floating-bar" id="chat-status-bar">
        <span className="chat-window__brand-name">MindBridge</span>
        <div className="chat-window__status">
          <div className="chat-window__status-dot"></div>
          <span>Online</span>
        </div>
      </div>

      {/* Messages area */}
      <div className="chat-window__messages" ref={chatContainerRef}>
        <div className="chat-window__messages-inner">
          {/* First-message disclaimer */}
          <div className="chat-window__disclaimer">
            This is a wellbeing support tool, not a substitute for professional
            diagnosis or treatment. In an emergency, contact local emergency services
            or the helplines provided.
          </div>

          {messages.map((msg) => {
            if (msg.role === 'assistant' && msg.type === 'crisis') {
              return <CrisisBanner key={msg.id} message={msg} />;
            }
            return <MessageBubble key={msg.id} message={msg} />;
          })}

          {/* Typing indicator */}
          {isLoading && (
            <div className="chat-window__typing" id="typing-indicator">
              <div className="chat-window__typing-dots">
                <span></span><span></span><span></span>
              </div>
              <span className="chat-window__typing-text">Understanding...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat-window__input-area">
        <InputBar onSend={onSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}
