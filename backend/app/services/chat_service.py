"""
Chat service — orchestrates the full conversation flow.

Flow:
1. Crisis detector (deterministic) → bypass LLM if triggered
2. Topic classifier (keyword + LLM fallback) → redirect if off-topic
3. RAG retrieval → get relevant context
4. Gemini API call with system prompt + context + history
5. Output moderation → strip unsafe content
6. Return response to caller
"""

from app.core.config import settings
from app.core.logging_config import get_logger
from app.guardrails.crisis_detector import detect_crisis, get_crisis_response, log_crisis_event
from app.guardrails.topic_classifier import classify_topic, REDIRECT_RESPONSE
from app.guardrails.concern_classifier import classify_concern, get_therapist_suggestions
from app.guardrails.output_moderation import moderate_output
from app.guardrails.system_prompt import get_system_prompt
from app.rag.retriever import retrieve_context
from app.services.gemini_client import generate_response
from app.utils.session_store import session_store
from app.models.schemas import ChatResponse, ResponseType

logger = get_logger(__name__)


async def process_message(message: str, session_id: str) -> ChatResponse:
    """
    Process a user message through the full guardrail + RAG + LLM pipeline.

    Args:
        message: The user's message text.
        session_id: The session identifier.

    Returns:
        ChatResponse with the bot's reply and response type.
    """

    # ── Step 1: Crisis Detection (deterministic, pre-LLM) ──────────────
    if detect_crisis(message):
        log_crisis_event(session_id)
        crisis_text = get_crisis_response()

        # Store in session history for context continuity
        session_store.add_message(session_id, "user", message)
        session_store.add_message(session_id, "assistant", crisis_text)

        return ChatResponse(
            reply=crisis_text,
            type=ResponseType.CRISIS,
        )

    # ── Step 2: Topic Classification (pre-LLM) ────────────────────────
    is_in_scope, redirect_text = await classify_topic(message)
    if not is_in_scope:
        logger.info("Off-topic message redirected | session_id=%s", session_id)

        # Store in session but don't bloat history with off-topic exchanges
        session_store.add_message(session_id, "user", message)
        session_store.add_message(session_id, "assistant", redirect_text)

        return ChatResponse(
            reply=redirect_text,
            type=ResponseType.REDIRECT,
        )

    # ── Step 3: RAG Retrieval ──────────────────────────────────────────
    rag_context = ""
    sources = None
    try:
        rag_context = retrieve_context(message)
        if rag_context:
            # Extract source labels for the response metadata
            source_labels = []
            for line in rag_context.split("\n"):
                if line.startswith("[") and line.endswith("]"):
                    source_labels.append(line.strip("[]"))
            if source_labels:
                sources = source_labels
            logger.debug("RAG retrieved %d source(s) for query", len(source_labels))
    except Exception as e:
        logger.error("RAG retrieval error: %s — proceeding without context", e)

    # ── Step 4: Build System Prompt + Call Gemini ──────────────────────
    system_prompt = get_system_prompt(rag_context=rag_context)
    history = session_store.get_history(session_id)

    try:
        raw_response = await generate_response(
            user_message=message,
            system_prompt=system_prompt,
            conversation_history=history,
        )
    except Exception as e:
        logger.error("Gemini API call failed: %s", e)
        raw_response = (
            "I'm having a moment of difficulty on my end. "
            "I'm still here for you — could you try sending your message again in a moment? "
            "If you're in crisis, please reach out to Tele MANAS at 14416 or KIRAN at 1800-599-0019."
        )

    # ── Step 5: Output Moderation ─────────────────────────────────────
    moderated_response, was_modified = moderate_output(raw_response)
    if was_modified:
        logger.info("Output moderation modified response | session_id=%s", session_id)

    # ── Step 5.5: Concern Classification (therapist suggestions) ─────
    # Classify first, then check per-category cooldown.  This lets a user
    # who switches topics (stress → relationship) get fresh suggestions
    # immediately, while repeated messages on the same topic respect the
    # cooldown window.
    suggested_category = None
    suggested_therapists = None
    therapist_cta = None

    if settings.enable_therapist_suggestions:
        try:
            concern = await classify_concern(message)
            if concern != "none" and session_store.should_suggest_therapists(session_id, concern):
                suggestion = get_therapist_suggestions(concern)
                if suggestion:
                    therapist_list, cta = suggestion
                    suggested_category = concern
                    suggested_therapists = therapist_list
                    therapist_cta = cta
                    session_store.mark_therapist_suggested(session_id, concern)
                    logger.info(
                        "Therapist suggestion added | session_id=%s | category=%s",
                        session_id, concern,
                    )
        except Exception as e:
            logger.error("Concern classification error: %s — skipping suggestions", e)


    # ── Step 6: Store in Session History ──────────────────────────────
    session_store.add_message(session_id, "user", message)
    session_store.add_message(session_id, "assistant", moderated_response)

    return ChatResponse(
        reply=moderated_response,
        type=ResponseType.NORMAL,
        sources=sources,
        suggested_category=suggested_category,
        suggested_therapists=suggested_therapists,
        therapist_cta=therapist_cta,
    )
