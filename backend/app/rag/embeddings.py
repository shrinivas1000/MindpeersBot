"""Embedding utility using the Gemini text-embedding API."""

from google import genai

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Get or create the Gemini client for embeddings."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def embed_text(text: str) -> list[float]:
    """
    Generate an embedding vector for a single text string.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding vector.
    """
    client = _get_client()
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
    )
    return response.embeddings[0].values


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embedding vectors for multiple text strings.

    Args:
        texts: List of texts to embed.

    Returns:
        List of embedding vectors.
    """
    client = _get_client()
    embeddings = []
    # Process in batches of 100 to stay within API limits
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.models.embed_content(
            model=settings.embedding_model,
            contents=batch,
        )
        embeddings.extend([e.values for e in response.embeddings])
        logger.debug("Embedded batch %d-%d of %d texts", i, i + len(batch), len(texts))
    return embeddings
