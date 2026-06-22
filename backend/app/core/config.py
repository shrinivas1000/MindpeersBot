"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration loaded from environment variables / .env file."""

    # Gemini API
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model name for chat completions",
    )
    embedding_model: str = Field(
        default="gemini-embedding-001",
        description="Gemini model name for text embeddings",
    )

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    log_level: str = Field(default="info")

    # ChromaDB — /tmp is the only writable dir in serverless environments
    chroma_persist_dir: str = Field(
        default="/tmp/chroma_data",
        description="Directory for ChromaDB persistent storage",
    )

    # Session
    max_session_history: int = Field(
        default=20,
        description="Maximum number of conversation turns to keep per session",
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # RAG
    rag_top_k: int = Field(
        default=5,
        description="Number of RAG chunks to retrieve per query",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton instance — import this throughout the app
settings = Settings()
