"""
Topic classifier — determines whether a message is in-scope for mental wellbeing support.

Uses a two-stage approach:
1. Cheap keyword/phrase check (immediate allow or deny for clear cases).
2. Gemini fallback for ambiguous messages (small classification call).

Designed to be permissive with borderline cases — venting about a bad day,
work stress, relationship issues, sleep, motivation, and loneliness are all in-scope.
"""

import re
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Keywords/phrases that strongly signal IN-SCOPE messages
_IN_SCOPE_SIGNALS = [
    "feel", "feeling", "feelings", "felt", "emotion", "emotions", "mood",
    "stress", "stressed", "stressful", "overwhelm",
    "anxious", "anxiety", "worried", "worry", "worrying", "panic",
    "sad", "sadness", "unhappy", "down", "low",
    "depress", "depressed", "depressing",
    "lonely", "loneliness", "alone", "isolated",
    "sleep", "insomnia", "can't sleep", "sleeping",
    "tired", "exhausted", "burnout", "burnt out",
    "angry", "anger", "frustrated", "frustration", "irritated",
    "relationship", "breakup", "broke up", "divorce",
    "grief", "grieving", "loss", "lost someone", "miss them",
    "therapy", "therapist", "counselor", "counselling", "counseling",
    "mental health", "wellbeing", "well-being", "self-care", "self care",
    "cope", "coping", "manage", "handling",
    "motivation", "unmotivated", "procrastinating", "stuck",
    "confidence", "self-esteem", "self-worth", "insecure",
    "fear", "scared", "afraid", "phobia",
    "trauma", "traumatic", "ptsd",
    "eating", "appetite", "body image",
    "crying", "tears", "cry",
    "numb", "empty", "hopeless", "helpless",
    "breathe", "breathing", "meditation", "mindful",
    "journal", "vent", "venting", "rant",
    "family", "parent", "sibling", "friend",
    "work stress", "job stress", "school stress",
    "pressure", "burden", "struggling",
    "happy", "happiness", "grateful", "gratitude",
    "calm", "relax", "peace", "peaceful",
    "support", "help me", "need help",
    "thank you", "thanks", "hi", "hello", "hey",
    "how are you", "good morning", "good night",
]

# Keywords/phrases that strongly signal OFF-TOPIC messages
_OFF_TOPIC_SIGNALS = [
    "write me a", "write a program", "write code", "write a script",
    "code", "coding", "programming", "python", "javascript", "java ",
    "algorithm", "function", "class ", "variable",
    "recipe", "cook", "cooking", "ingredients",
    "score", "match", "tournament", "championship", "cricket", "football",
    "who won", "who is the", "what is the capital",
    "homework", "assignment", "exam", "test paper",
    "math", "calculate", "equation", "solve for",
    "translate", "translation",
    "weather", "forecast",
    "stock", "bitcoin", "crypto", "invest",
    "movie", "film", "song", "music recommendation",
    "game", "gaming",
    "buy", "purchase", "shopping", "price",
    "joke", "tell me a joke", "funny",
    "story", "write a story", "poem",
    "news", "politics", "election",
    "explain quantum", "explain relativity",
    "debug", "error message", "stack trace",
    "api", "database", "server",
    "html", "css", "react",
]

# Pre-compile for faster matching
_in_scope_patterns = [re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.IGNORECASE) for kw in _IN_SCOPE_SIGNALS]
_off_topic_patterns = [re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.IGNORECASE) for kw in _OFF_TOPIC_SIGNALS]

# Short, friendly redirect message
REDIRECT_RESPONSE = (
    "I'm here to support your emotional wellbeing and mental health. "
    "I'm not able to help with that particular topic, but I'm always here "
    "if you'd like to talk about how you're feeling."
)


def _keyword_classify(message: str) -> str | None:
    """
    Quick keyword-based classification.

    Returns:
        "in_scope" — clearly about wellbeing
        "off_topic" — clearly not about wellbeing
        None — ambiguous, needs LLM fallback
    """
    normalized = message.lower().strip()

    # Very short messages like greetings are always in-scope
    if len(normalized.split()) <= 3:
        for pattern in _in_scope_patterns:
            if pattern.search(normalized):
                return "in_scope"

    in_scope_hits = sum(1 for p in _in_scope_patterns if p.search(normalized))
    off_topic_hits = sum(1 for p in _off_topic_patterns if p.search(normalized))

    # Clear off-topic with no wellbeing signals
    if off_topic_hits > 0 and in_scope_hits == 0:
        return "off_topic"

    # Clear in-scope
    if in_scope_hits > 0 and off_topic_hits == 0:
        return "in_scope"

    # Mixed signals or no signals — ambiguous
    if in_scope_hits > off_topic_hits:
        return "in_scope"
    if off_topic_hits > in_scope_hits:
        return "off_topic"

    return None


async def _llm_classify(message: str) -> str:
    """
    Use a small Gemini call to classify ambiguous messages.

    Returns "in_scope" or "off_topic".
    """
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a classifier. Determine if the user's message is related to "
                    "mental wellbeing, emotions, feelings, stress, coping, relationships, "
                    "sleep, motivation, self-care, or general emotional support. "
                    "Be permissive: venting about a bad day, work/school frustration, "
                    "loneliness, or general life struggles count as in-scope. "
                    "Only classify as off-topic if the message is clearly about something "
                    "unrelated like coding, trivia, homework, sports, shopping, etc. "
                    "Reply with EXACTLY one word: 'in_scope' or 'off_topic'."
                ),
                max_output_tokens=10,
                temperature=0.0,
            ),
        )
        result = response.text.strip().lower().replace("'", "").replace('"', '')
        if "in_scope" in result:
            return "in_scope"
        elif "off_topic" in result:
            return "off_topic"
        else:
            # If unclear, be permissive
            logger.warning("Ambiguous LLM classification result: %s — defaulting to in_scope", result)
            return "in_scope"
    except Exception as e:
        # If the LLM call fails, be permissive — let the message through
        logger.error("Topic classification LLM call failed: %s — defaulting to in_scope", e)
        return "in_scope"


async def classify_topic(message: str) -> tuple[bool, str | None]:
    """
    Determine whether a message is in-scope for mental wellbeing support.

    Returns:
        (is_in_scope, redirect_message)
        - (True, None) if the message is in-scope
        - (False, redirect_text) if the message is off-topic
    """
    # Stage 1: keyword check
    result = _keyword_classify(message)

    if result == "in_scope":
        logger.debug("Topic classifier (keyword): in_scope")
        return True, None
    elif result == "off_topic":
        logger.info("Topic classifier (keyword): off_topic")
        return False, REDIRECT_RESPONSE

    # Stage 2: LLM fallback for ambiguous cases
    logger.debug("Topic classifier: ambiguous, falling back to LLM")
    result = await _llm_classify(message)

    if result == "in_scope":
        return True, None
    else:
        logger.info("Topic classifier (LLM): off_topic")
        return False, REDIRECT_RESPONSE
