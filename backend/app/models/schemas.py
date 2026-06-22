"""Pydantic request/response models for the chat API."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ResponseType(str, Enum):
    """Type of chatbot response."""
    NORMAL = "normal"
    CRISIS = "crisis"
    REDIRECT = "redirect"


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""
    message: str = Field(..., min_length=1, max_length=5000, description="User message text")
    session_id: str = Field(..., min_length=1, max_length=128, description="Session identifier")


class ChatResponse(BaseModel):
    """Response sent back to the frontend."""
    reply: str = Field(..., description="Bot response text")
    type: ResponseType = Field(..., description="Response type: normal, crisis, or redirect")
    sources: Optional[list[str]] = Field(
        default=None,
        description="Source descriptions from RAG retrieval, if any",
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    service: str = "mental-health-chatbot-api"


class SessionHistoryResponse(BaseModel):
    """Session conversation history."""
    session_id: str
    messages: list[dict]
