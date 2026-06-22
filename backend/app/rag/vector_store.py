"""ChromaDB vector store wrapper for the RAG knowledge base."""

import chromadb
from pathlib import Path

from app.core.config import settings
from app.core.logging_config import get_logger
from app.rag.embeddings import embed_texts

logger = get_logger(__name__)

COLLECTION_NAME = "mental_health_kb"

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_client() -> chromadb.ClientAPI:
    """Get or create the ChromaDB persistent client."""
    global _client
    if _client is None:
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(persist_dir))
        logger.info("ChromaDB client initialized at %s", persist_dir)
    return _client


def get_collection() -> chromadb.Collection:
    """Get or create the knowledge base collection."""
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Vetted mental health and wellbeing content"},
        )
        logger.info("ChromaDB collection '%s' ready (count=%d)", COLLECTION_NAME, _collection.count())
    return _collection


def index_documents(documents: list[dict]) -> None:
    """
    Index a list of documents into ChromaDB.

    Args:
        documents: List of dicts with keys: "id", "text", "metadata".
    """
    if not documents:
        logger.warning("No documents to index")
        return

    collection = get_collection()

    # Check if already indexed
    if collection.count() > 0:
        logger.info("Collection already has %d documents — skipping indexing", collection.count())
        return

    ids = [doc["id"] for doc in documents]
    texts = [doc["text"] for doc in documents]
    metadatas = [doc.get("metadata", {}) for doc in documents]

    logger.info("Generating embeddings for %d documents...", len(texts))
    embeddings = embed_texts(texts)

    logger.info("Indexing %d documents into ChromaDB...", len(documents))
    # ChromaDB has a batch limit, process in chunks
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=texts[i:end],
            metadatas=metadatas[i:end],
        )

    logger.info("Indexing complete — %d documents in collection", collection.count())


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
