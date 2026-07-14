/**
 * MessageBubble — renders a single chat message.
 *
 * User messages: aligned right, secondary tint background.
 * Assistant messages: aligned left, background with thin border.
 * All text is near-black.
 * Therapist suggestions rendered as a distinct card below assistant messages.
 */

import './MessageBubble.css';
import TherapistSuggestion from '../TherapistSuggestion/TherapistSuggestion';

/**
 * Strip any emojis from text as a safety net.
 * Removes emoji Unicode ranges.
 */
function stripEmojis(text) {
  return text.replace(
    /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{200D}\u{20E3}\u{E0020}-\u{E007F}]/gu,
    ''
  ).trim();
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const displayText = stripEmojis(message.content);
  const hasSuggestions = !isUser && message.suggested_therapists && message.suggested_therapists.length > 0;

  return (
    <div
      className={`message-bubble ${isUser ? 'message-bubble--user' : 'message-bubble--assistant'}`}
      id={`message-${message.id}`}
    >
      <div className="message-bubble__content">
        {displayText.split('\n').map((paragraph, i) => (
          paragraph.trim() ? <p key={i}>{paragraph}</p> : null
        ))}
      </div>
      {hasSuggestions && (
        <TherapistSuggestion
          cta={message.therapist_cta}
          therapists={message.suggested_therapists}
        />
      )}
    </div>
  );
}

