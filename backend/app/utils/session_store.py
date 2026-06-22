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


# Singleton instance
session_store = SessionStore()
