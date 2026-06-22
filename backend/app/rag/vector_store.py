"""Lightweight in-memory vector store for the RAG knowledge base.

Replaces ChromaDB with a pure-Python implementation using cosine similarity.
This keeps the serverless bundle well under Vercel's 500 MB limit while
providing identical retrieval functionality for our small knowledge base.
"""

import json
import math
from pathlib import Path

from app.core.config import settings
from app.core.logging_config import get_logger
from app.rag.embeddings import embed_texts

logger = get_logger(__name__)

COLLECTION_NAME = "mental_health_kb"


class _InMemoryCollection:
    """A minimal vector collection stored in memory with optional /tmp cache."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._embeddings: list[list[float]] = []
        self._documents: list[str] = []
        self._metadatas: list[dict] = []
        self._cache_path = Path(settings.chroma_persist_dir) / "vector_cache.json"

    # ------------------------------------------------------------------
    # Persistence helpers (optional /tmp cache to survive warm starts)
    # ------------------------------------------------------------------
    def _save_cache(self) -> None:
        """Persist the index to /tmp so warm invocations skip re-embedding."""
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "ids": self._ids,
                "embeddings": self._embeddings,
                "documents": self._documents,
                "metadatas": self._metadatas,
            }
            self._cache_path.write_text(json.dumps(data), encoding="utf-8")
            logger.debug("Vector cache saved to %s", self._cache_path)
        except Exception as e:
            logger.warning("Failed to save vector cache: %s", e)

    def _load_cache(self) -> bool:
        """Attempt to load a previously cached index."""
        try:
            if self._cache_path.exists():
                data = json.loads(self._cache_path.read_text(encoding="utf-8"))
                self._ids = data["ids"]
                self._embeddings = data["embeddings"]
                self._documents = data["documents"]
                self._metadatas = data["metadatas"]
                logger.info("Loaded %d documents from vector cache", len(self._ids))
                return True
        except Exception as e:
            logger.warning("Failed to load vector cache: %s", e)
        return False

    # ------------------------------------------------------------------
    # Public API (mirrors the subset used by retriever.py)
    # ------------------------------------------------------------------
    def count(self) -> int:
        return len(self._ids)

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self._ids.extend(ids)
        self._embeddings.extend(embeddings)
        self._documents.extend(documents)
        self._metadatas.extend(metadatas)

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 5,
    ) -> dict:
        """Return the top-k most similar documents by cosine similarity."""
        query_vec = query_embeddings[0]
        scored: list[tuple[int, float]] = []

        for idx, doc_vec in enumerate(self._embeddings):
            sim = _cosine_similarity(query_vec, doc_vec)
            # ChromaDB returns *distance*; cosine distance = 1 - similarity
            scored.append((idx, 1.0 - sim))

        scored.sort(key=lambda x: x[1])
        top = scored[:n_results]

        result_ids = [self._ids[i] for i, _ in top]
        result_docs = [self._documents[i] for i, _ in top]
        result_metas = [self._metadatas[i] for i, _ in top]
        result_dists = [d for _, d in top]

        return {
            "ids": [result_ids],
            "documents": [result_docs],
            "metadatas": [result_metas],
            "distances": [result_dists],
        }


# ------------------------------------------------------------------
# Module-level singleton (same pattern as before)
# ------------------------------------------------------------------
_collection: _InMemoryCollection | None = None


def get_collection() -> _InMemoryCollection:
    """Get or create the in-memory collection."""
    global _collection
    if _collection is None:
        _collection = _InMemoryCollection()
        _collection._load_cache()
        logger.info(
            "In-memory collection '%s' ready (count=%d)",
            COLLECTION_NAME,
            _collection.count(),
        )
    return _collection


def index_documents(documents: list[dict]) -> None:
    """
    Index a list of documents into the in-memory vector store.

    Args:
        documents: List of dicts with keys: "id", "text", "metadata".
    """
    if not documents:
        logger.warning("No documents to index")
        return

    collection = get_collection()

    # Check if already indexed
    if collection.count() > 0:
        logger.info(
            "Collection already has %d documents — skipping indexing",
            collection.count(),
        )
        return

    ids = [doc["id"] for doc in documents]
    texts = [doc["text"] for doc in documents]
    metadatas = [doc.get("metadata", {}) for doc in documents]

    logger.info("Generating embeddings for %d documents...", len(texts))
    embeddings = embed_texts(texts)

    logger.info("Indexing %d documents into in-memory store...", len(documents))
    # Process in batches to match the original pattern
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=texts[i:end],
            metadatas=metadatas[i:end],
        )

    # Cache to /tmp for warm starts
    collection._save_cache()

    logger.info(
        "Indexing complete — %d documents in collection", collection.count()
    )


def query_similar(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """
    Query the vector store for similar documents.

    Args:
        query_embedding: The embedding vector of the query.
        top_k: Number of results to return.

    Returns:
        List of dicts with "text", "metadata", and "distance".
    """
    collection = get_collection()

    if collection.count() == 0:
        logger.debug("Collection is empty — no results")
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )

    documents = []
    for i in range(len(results["ids"][0])):
        documents.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            "distance": results["distances"][0][i] if results["distances"] else None,
        })

    return documents


# ------------------------------------------------------------------
# Math helpers
# ------------------------------------------------------------------
def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
