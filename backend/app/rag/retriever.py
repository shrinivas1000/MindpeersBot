"""
RAG retriever — loads knowledge base, builds index, and retrieves relevant chunks.

The index is built at startup if the ChromaDB collection is empty.
Documents are chunked by section (splitting on ## headers) for better
granularity in retrieval.
"""

from pathlib import Path

from app.core.config import settings
from app.core.logging_config import get_logger
from app.rag.embeddings import embed_text
from app.rag.vector_store import index_documents, query_similar, get_collection

logger = get_logger(__name__)

KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"


def _load_and_chunk_documents() -> list[dict]:
    """
    Load markdown files from the knowledge base and split them into chunks.

    Chunks are split on ## headers to maintain topical coherence.
    Each chunk gets a unique ID and metadata with the source filename.
    """
    documents = []
    chunk_id = 0

    for md_file in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        source_name = md_file.stem.replace("_", " ").title()

        # Split by ## headers for granular chunks
        sections = []
        current_section = []
        title = ""

        for line in content.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections.append((title, "\n".join(current_section).strip()))
                title = line.lstrip("# ").strip()
                current_section = [line]
            elif line.startswith("# ") and not current_section:
                # Top-level heading — use as document title
                title = line.lstrip("# ").strip()
                current_section = [line]
            else:
                current_section.append(line)

        # Don't forget the last section
        if current_section:
            sections.append((title, "\n".join(current_section).strip()))

        for section_title, section_text in sections:
            if len(section_text.strip()) < 50:
                # Skip very short sections (e.g., just a heading)
                continue

            documents.append({
                "id": f"kb_{chunk_id:04d}",
                "text": section_text,
                "metadata": {
                    "source": source_name,
                    "section": section_title,
                    "file": md_file.name,
                },
            })
            chunk_id += 1

    logger.info("Loaded %d chunks from %d knowledge base files",
                len(documents), len(list(KNOWLEDGE_BASE_DIR.glob("*.md"))))
    return documents


def initialize_index() -> None:
    """
    Build the RAG index if it doesn't already exist.

    Called at application startup.
    """
    try:
        collection = get_collection()
        if collection.count() > 0:
            logger.info("RAG index already exists with %d documents — skipping build", collection.count())
            return

        documents = _load_and_chunk_documents()
        if not documents:
            logger.warning("No knowledge base documents found — RAG will be inactive")
            return

        index_documents(documents)
        logger.info("RAG index built successfully")
    except Exception as e:
        logger.error("Failed to initialize RAG index: %s — RAG will be unavailable", e)


def retrieve_context(query: str, top_k: int | None = None) -> str:
    """
    Retrieve relevant context from the knowledge base for a query.

    Args:
        query: The user's message.
        top_k: Number of chunks to retrieve (defaults to config value).

    Returns:
        A formatted string of retrieved context chunks, or empty string
        if no relevant content is found.
    """
    k = top_k or settings.rag_top_k

    try:
        collection = get_collection()
        if collection.count() == 0:
            return ""

        query_embedding = embed_text(query)
        results = query_similar(query_embedding, top_k=k)

        if not results:
            return ""

        # Format the retrieved chunks as context
        context_parts = []
        for result in results:
            source = result["metadata"].get("source", "General Wellbeing")
            section = result["metadata"].get("section", "")
            label = f"{source} — {section}" if section else source
            context_parts.append(f"[{label}]\n{result['text']}")

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        logger.error("RAG retrieval failed: %s — proceeding without context", e)
        return ""
