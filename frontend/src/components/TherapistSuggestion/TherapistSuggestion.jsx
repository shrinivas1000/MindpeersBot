/**
 * TherapistSuggestion — renders a visually distinct card with therapist
 * recommendations below the assistant message bubble.
 *
 * Shows a friendly CTA line + 3 therapist chips, each linking to their
 * profile on dashboard.mindpeers.co (opens in new tab).
 *
 * Only rendered when the backend returns suggestion data.
 */

import './TherapistSuggestion.css';

export default function TherapistSuggestion({ cta, therapists }) {
  if (!therapists || therapists.length === 0) return null;

  return (
    <div className="therapist-suggestion" id="therapist-suggestion">
      <div className="therapist-suggestion__cta">{cta}</div>
      <div className="therapist-suggestion__chips">
        {therapists.map((therapist, i) => (
          <a
            key={i}
            href={therapist.link}
            target="_blank"
            rel="noopener noreferrer"
            className="therapist-suggestion__chip"
            id={`therapist-chip-${i}`}
          >
            <span className="therapist-suggestion__name">{therapist.name}</span>
            <svg
              className="therapist-suggestion__link-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </a>
        ))}
      </div>
    </div>
  );
}
