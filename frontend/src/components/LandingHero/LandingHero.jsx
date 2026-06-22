/**
 * LandingHero — premium full-screen landing page.
 *
 * Cream base with pastel gradient mesh blobs drifting in the upper portion.
 * Bold hero typography with gradient accent, suggestion chips, floating input.
 */

import InputBar from '../InputBar/InputBar';
import './LandingHero.css';

const SUGGESTIONS = [
  "I've been feeling anxious lately",
  "Help me with stress management",
  "I need someone to talk to",
];

export default function LandingHero({ onSendMessage, isLoading }) {
  return (
    <div className="landing-hero" id="landing-hero">
      {/* Animated pastel gradient mesh */}
      <div className="landing-hero__bg" aria-hidden="true">
        <div className="landing-hero__orb landing-hero__orb--1" />
        <div className="landing-hero__orb landing-hero__orb--2" />
        <div className="landing-hero__orb landing-hero__orb--3" />
        <div className="landing-hero__orb landing-hero__orb--4" />
        <div className="landing-hero__grain" />
      </div>

      {/* Hero content */}
      <div className="landing-hero__content">
        <h1 className="landing-hero__heading">
          How are you{' '}
          <span className="landing-hero__heading-accent">feeling</span>{' '}
          today?
        </h1>
        <p className="landing-hero__subtext">
          A safe space to share what's on your mind. I'm here to listen,
          understand, and support you.
        </p>
      </div>

      {/* Bottom — suggestions + input */}
      <div className="landing-hero__bottom">
        <div className="landing-hero__suggestions">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              className="landing-hero__chip"
              onClick={() => onSendMessage(suggestion)}
              disabled={isLoading}
              type="button"
            >
              {suggestion}
            </button>
          ))}
        </div>

        <div className="landing-hero__input-wrapper">
          <InputBar onSend={onSendMessage} isLoading={isLoading} />
        </div>

        <div className="landing-hero__disclaimer">
          This is a wellbeing support tool, not a substitute for professional
          diagnosis or treatment. In an emergency, contact local emergency
          services or the helplines provided.
        </div>
      </div>
    </div>
  );
}
