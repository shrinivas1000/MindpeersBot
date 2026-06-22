"""
FastAPI application entry point.

Initializes logging, mounts routes, configures CORS,
and builds the RAG index on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.api.routes import chat, health
from app.rag.retriever import initialize_index

# Set up logging before anything else
setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""
    logger.info("Starting Mental Health Support Chatbot API")
    logger.info("Model: %s | Embedding: %s", settings.gemini_model, settings.embedding_model)

    # Build RAG index if not already present
    try:
        initialize_index()
    except Exception as e:
        logger.error("RAG initialization failed: %s — continuing without RAG", e)

    yield

    logger.info("Shutting down Mental Health Support Chatbot API")


app = FastAPI(
    title="Mental Health Support Chatbot API",
    description="A mental wellbeing support chatbot with guardrails, RAG, and Gemini integration.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — configurable via CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount route modules
app.include_router(chat.router)
app.include_router(health.router)
