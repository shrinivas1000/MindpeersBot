"""
Concern classifier — classifies in-scope messages into concern categories.

Uses a two-stage approach (same pattern as topic_classifier):
1. Cheap keyword/phrase check for clear-cut cases.
2. Gemini LLM fallback for ambiguous messages.

Categories: stress, anxiety, relationship, none.
Returns a single best-match category per message.

NOTE: This module should ONLY be called for messages that have already passed
crisis detection and topic classification (i.e., non-crisis, in-scope messages).
"""

import json
import random
import re
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ── Load therapist data once at import time ──────────────────────────────────
_THERAPISTS_FILE = Path(__file__).resolve().parent.parent / "data" / "therapists.json"
_therapists_data: dict = json.loads(_THERAPISTS_FILE.read_text(encoding="utf-8"))

# ── Friendly CTA variants — randomly selected to avoid repetition ────────────
_CTA_VARIANTS = [
    "You might find it helpful to chat with one of these therapists:",
    "Here are some therapists who could be a great fit for you:",
    "These therapists specialise in this area and might be worth checking out:",
    "If you'd like to talk to a professional, these therapists come highly recommended:",
    "Sometimes it helps to talk to someone trained in this — here are a few options:",
]

# ── Keyword lists per category ───────────────────────────────────────────────
_STRESS_KEYWORDS = [
    "stress", "stressed", "stressful", "overwhelm", "overwhelmed", "overwhelming",
    "burnout", "burnt out", "burned out", "overwork", "overworked",
    "pressure", "pressured", "deadline", "deadlines",
    "workload", "work load", "too much work",
    "exhausted", "exhaustion", "drained",
    "tension", "tense",
    "work stress", "job stress", "school stress", "exam stress",
    "can't handle", "can't cope", "cannot cope",
    "breaking point", "snapping", "at my limit",
    "burden", "burdened",
]

_ANXIETY_KEYWORDS = [
    "anxious", "anxiety", "anxiousness",
    "panic", "panic attack", "panicking", "panicked",
    "worry", "worried", "worrying", "worries",
    "nervous", "nervousness", "nerves",
    "fear", "fearful", "afraid", "scared", "terrified",
    "restless", "restlessness", "on edge",
    "racing thoughts", "racing mind", "can't stop thinking",
    "overthinking", "overthink",
    "phobia", "phobic",
    "uneasy", "unease", "dread",
    "heart racing", "heart pounding", "sweating",
    "hyperventilat", "shortness of breath",
    "social anxiety",
]

_RELATIONSHIP_KEYWORDS = [
    "relationship", "relationships",
    "breakup", "break up", "broke up", "breaking up",
    "partner", "boyfriend", "girlfriend", "spouse", "husband", "wife",
    "marriage", "married", "divorce", "divorcing", "separated", "separation",
    "heartbreak", "heartbroken", "heart broken",
    "cheating", "cheated", "affair", "infidelity", "unfaithful",
    "trust issues", "jealous", "jealousy",
    "toxic relationship", "abusive relationship",
    "family conflict", "family issues", "family problems",
    "fighting with my", "argument with my",
    "long distance", "ldr",
    "love life", "romantic",
    "dating", "date",
    "commitment", "commitment issues",
    "ex-boyfriend", "ex-girlfriend", "my ex",
]

# Pre-compile for faster matching
_category_patterns: dict[str, list[re.Pattern]] = {
    "stress": [
        re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.IGNORECASE)
        for kw in _STRESS_KEYWORDS
    ],
    "anxiety": [
        re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.IGNORECASE)
        for kw in _ANXIETY_KEYWORDS
    ],
    "relationship": [
        re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.IGNORECASE)
        for kw in _RELATIONSHIP_KEYWORDS
    ],
}


def _keyword_classify_concern(message: str) -> str | None:
    """
    Quick keyword-based concern classification.

    Returns:
        "stress", "anxiety", "relationship" — if one category clearly dominates
        None — ambiguous or no clear match, needs LLM fallback
    """
    normalized = message.lower().strip()

    hits: dict[str, int] = {}
    for category, patterns in _category_patterns.items():
        count = sum(1 for p in patterns if p.search(normalized))
        if count > 0:
            hits[category] = count

    if not hits:
        return None

    # Sort by hit count descending
    sorted_hits = sorted(hits.items(), key=lambda x: x[1], reverse=True)

    # Clear winner — either only one category matched, or top has strictly more hits
    if len(sorted_hits) == 1:
        return sorted_hits[0][0]

    if sorted_hits[0][1] > sorted_hits[1][1]:
        return sorted_hits[0][0]

    # Tied — ambiguous, fall through to LLM
    return None


async def _llm_classify_concern(message: str) -> str:
    """
    Use a small Gemini call to classify the concern category.

    Returns one of: "stress", "anxiety", "relationship", "none".
    """
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a classifier. Given a user message about their emotional "
                    "wellbeing, classify it into exactly ONE of these concern categories:\n"
                    "- 'stress' — work stress, burnout, overwhelm, pressure, exhaustion\n"
                    "- 'anxiety' — worry, panic, fear, nervousness, overthinking, dread\n"
                    "- 'relationship' — romantic relationships, breakups, family conflict, "
                    "trust issues, dating\n"
                    "- 'none' — the message is about general wellbeing, sadness, sleep, "
                    "motivation, or something that doesn't clearly fit the above categories\n\n"
                    "If unsure, reply 'none'. Do NOT guess or force a category.\n"
                    "Reply with EXACTLY one word: 'stress', 'anxiety', 'relationship', or 'none'."
                ),
                max_output_tokens=10,
                temperature=0.0,
            ),
        )
        result = response.text.strip().lower().replace("'", "").replace('"', '')

        valid_categories = {"stress", "anxiety", "relationship", "none"}
        for cat in valid_categories:
            if cat in result:
                return cat

        logger.warning(
            "Ambiguous concern classification result: %s — defaulting to none", result
        )
        return "none"
    except Exception as e:
        logger.error("Concern classification LLM call failed: %s — defaulting to none", e)
        return "none"


async def classify_concern(message: str) -> str:
    """
    Classify a message into a concern category.

    This should only be called for non-crisis, in-scope messages.

    Returns:
        One of: "stress", "anxiety", "relationship", "none"
    """
    # Stage 1: keyword check
    result = _keyword_classify_concern(message)

    if result is not None:
        logger.debug("Concern classifier (keyword): %s", result)
        return result

    # Stage 2: LLM fallback for ambiguous cases
    logger.debug("Concern classifier: ambiguous, falling back to LLM")
    result = await _llm_classify_concern(message)
    logger.debug("Concern classifier (LLM): %s", result)
    return result


def get_therapist_suggestions(category: str) -> tuple[list[dict], str] | None:
    """
    Get therapist suggestions for a given concern category.

    Args:
        category: One of "stress", "anxiety", "relationship".

    Returns:
        (therapists_list, cta_text) if category is valid,
        None if category is "none" or not found.
    """
    if category == "none" or category not in _therapists_data:
        return None

    therapists = _therapists_data[category]
    cta = random.choice(_CTA_VARIANTS)
    return therapists, cta
