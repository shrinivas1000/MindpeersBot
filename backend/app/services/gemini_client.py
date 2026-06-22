"""Thin wrapper around the Google Gemini API."""

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Module-level client — initialized once
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Get or create the Gemini client singleton."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
        logger.info("Gemini client initialized with model=%s", settings.gemini_model)
    return _client


async def generate_response(
    user_message: str,
    system_prompt: str,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Generate a response from the Gemini model.

    Args:
        user_message: The current user message.
        system_prompt: The full system prompt (persona + rules + RAG context).
        conversation_history: Optional list of prior messages
            [{"role": "user"/"model", "content": "..."}].

    Returns:
        The model's response text.

    Raises:
        Exception: If the Gemini API call fails.
    """
    client = _get_client()

    # Build the contents list from conversation history + current message
    contents = []
    if conversation_history:
        for msg in conversation_history:
            role = msg["role"]
            # Gemini SDK uses "user" and "model" roles
            if role == "assistant":
                role = "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

    # Add the current user message
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        )
    )

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.7,
        max_output_tokens=1024,
        top_p=0.9,
    )

    logger.debug("Sending request to Gemini: model=%s, history_len=%d",
                 settings.gemini_model, len(contents) - 1)

    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=config,
    )

    if response.text:
        return response.text
    else:
        logger.warning("Gemini returned empty response")
        return "I'm here and listening. Could you share a bit more about what's on your mind?"
