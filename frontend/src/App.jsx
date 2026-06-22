/**
 * App.jsx — Root application component.
 *
 * Handles the hero → chat view transition with a smooth cross-fade:
 * - Both views exist in the DOM during transition
 * - Landing fades out while chat fades in simultaneously
 */

import { useState, useEffect } from 'react';
import LandingHero from './components/LandingHero/LandingHero';
import ChatWindow from './components/ChatWindow/ChatWindow';
import useChat from './hooks/useChat';
import './App.css';

export default function App() {
  const { messages, isLoading, hasStarted, send } = useChat();
  const [phase, setPhase] = useState('hero'); // 'hero' | 'crossfade' | 'chat'

  // Smooth cross-fade: hero fades out while chat fades in simultaneously
  useEffect(() => {
    if (hasStarted && phase === 'hero') {
      setPhase('crossfade');
      const timer = setTimeout(() => {
        setPhase('chat');
      }, 700); // match the CSS transition duration
      return () => clearTimeout(timer);
    }
  }, [hasStarted, phase]);

  return (
    <div className="app" id="app-root">
      {/* Landing hero — visible in 'hero' and 'crossfade' phases */}
      {phase !== 'chat' && (
        <div className={`app__hero ${phase === 'crossfade' ? 'app__hero--exit' : ''}`}>
          <LandingHero onSendMessage={send} isLoading={isLoading} />
        </div>
      )}

      {/* Chat window — visible in 'crossfade' and 'chat' phases */}
      {phase !== 'hero' && (
        <div className={`app__chat ${phase === 'crossfade' ? 'app__chat--entering' : 'app__chat--entered'}`}>
          <ChatWindow
            messages={messages}
            onSendMessage={send}
            isLoading={isLoading}
          />
        </div>
      )}
    </div>
  );
}
