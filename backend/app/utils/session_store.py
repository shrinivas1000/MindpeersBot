"""In-memory session store for conversation history."""

from collections import defaultdict
from typing import Optional

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SessionStore:
    """
    In-memory session store keyed by session_id.

    Stores conversation history as a list of message dicts:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    Sessions are lost on restart — acceptable for v1.
    """

    def __init__(self, max_history: int | None = None):
        self._max_history = max_history or settings.max_session_history
        self._sessions: dict[str, list[dict]] = defaultdict(list)
        # Tracks the user-message index at which therapists were last suggested
        self._therapist_tracker: dict[str, int] = {}

    def get_history(self, session_id: str) -> list[dict]:
        """Return the conversation history for a session."""
        return list(self._sessions[session_id])

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Append a message to the session history, trimming if needed."""
        self._sessions[session_id].append({"role": role, "content": content})

        # Keep only the last N turns (each turn = 1 user + 1 assistant message)
        max_messages = self._max_history * 2
        if len(self._sessions[session_id]) > max_messages:
            self._sessions[session_id] = self._sessions[session_id][-max_messages:]

    def session_exists(self, session_id: str) -> bool:
        """Check if a session has any history."""
        return session_id in self._sessions and len(self._sessions[session_id]) > 0

    def clear_session(self, session_id: str) -> None:
        """Clear a session's history."""
        self._sessions.pop(session_id, None)
        self._therapist_tracker.pop(session_id, None)

    # ── Therapist suggestion cooldown ────────────────────────────────────

    def _user_message_count(self, session_id: str) -> int:
        """Count user messages in a session's history."""
        return sum(1 for m in self._sessions[session_id] if m["role"] == "user")

    def should_suggest_therapists(self, session_id: str, cooldown: int = 3) -> bool:
        """
        Return True if enough user messages have passed since the last
        therapist suggestion (or if therapists have never been suggested).
        """
        if session_id not in self._therapist_tracker:
            return True
        last_suggested_at = self._therapist_tracker[session_id]
        current_count = self._user_message_count(session_id)
        return (current_count - last_suggested_at) >= cooldown

    def mark_therapist_suggested(self, session_id: str) -> None:
        """Record that therapists were suggested at the current message count."""
        self._therapist_tracker[session_id] = self._user_message_count(session_id)


# Singleton instance
session_store = SessionStore()

