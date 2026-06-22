"""
Crisis detector — deterministic, regex/keyword-based matcher.

This module runs BEFORE any LLM call and must work even if the Gemini API
is down. When triggered, it returns a fixed, hardcoded crisis response
with helpline numbers.

Privacy note: we log the event (timestamp + session_id) but NOT the
raw message content.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Load crisis patterns from the structured resource file
_PATTERNS_FILE = Path(__file__).parent / "crisis_patterns.json"
_patterns_data = json.loads(_PATTERNS_FILE.read_text(encoding="utf-8"))

# Compile all patterns into a single regex for efficient matching
_all_patterns: list[str] = []
for category in _patterns_data["categories"].values():
    _all_patterns.extend(category["patterns"])

# Sort by length descending so longer phrases match first
_all_patterns.sort(key=len, reverse=True)

# Build compiled regex — each pattern is escaped and word-bounded where practical
_compiled_patterns = [
    re.compile(r"(?<!\w)" + re.escape(p) + r"(?!\w)", re.IGNORECASE)
    for p in _all_patterns
]

# Hardcoded crisis response — must not depend on LLM
CRISIS_RESPONSE = """I hear you, and I want you to know that what you're feeling matters. Right now, the most important thing is that you talk to someone who can help.

Please reach out to one of these helplines — they are free, confidential, and available right now:

Tele MANAS (Govt. of India, 24/7, multilingual): 14416 or 1-800-891-4416

KIRAN Mental Health Rehabilitation Helpline (Govt. of India, 24/7): 1800-599-0019

Vandrevala Foundation (24/7): 1860-266-2345 / 1800-233-3330, or emergency line +91 9999 666 555

You do not have to go through this alone. A trained person on the other end of these lines can help you right now. Please call."""


def detect_crisis(message: str) -> bool:
    """
    Check if a message contains crisis-related language.

    Args:
        message: The user's raw message text.

    Returns:
        True if crisis language is detected, False otherwise.
    """
    normalized = message.lower().strip()

    for pattern in _compiled_patterns:
        if pattern.search(normalized):
            return True

    return False


def get_crisis_response() -> str:
    """Return the fixed crisis response with helpline numbers."""
    return CRISIS_RESPONSE


def log_crisis_event(session_id: str) -> None:
    """
    Log a crisis detection event.

    Privacy-conscious: logs timestamp and session_id only,
    NOT the raw message content.
    """
    logger.warning(
        "CRISIS_DETECTED | session_id=%s | timestamp=%s",
        session_id,
        datetime.now(timezone.utc).isoformat(),
    )
