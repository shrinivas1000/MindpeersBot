"""Chat API route — POST /api/chat and GET /api/session/{id}/history."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, SessionHistoryResponse
from app.services.chat_service import process_message
from app.utils.session_store import session_store
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return a response.

    The message flows through crisis detection, topic classification,
    RAG retrieval, Gemini generation, and output moderation.
    """
    logger.info("Chat request received | session_id=%s | message_length=%d",
                request.session_id, len(request.message))

    try:
        response = await process_message(
            message=request.message,
            session_id=request.session_id,
        )
        logger.info("Chat response sent | session_id=%s | type=%s",
                     request.session_id, response.type)
        return response
    except Exception as e:
        logger.error("Chat processing error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your message. Please try again.",
        )


@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str) -> SessionHistoryResponse:
    """Retrieve conversation history for a session."""
    history = session_store.get_history(session_id)
    return SessionHistoryResponse(
        session_id=session_id,
        messages=history,
    )
