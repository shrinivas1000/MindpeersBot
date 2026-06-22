"""Tests for the chat flow — integration-level tests using mocked Gemini calls."""

import pytest
from unittest.mock import AsyncMock, patch

from app.models.schemas import ResponseType
from app.services.chat_service import process_message
from app.utils.session_store import SessionStore


@pytest.fixture(autouse=True)
def clean_session_store():
    """Reset session store before each test."""
    from app.utils import session_store as ss_module
    ss_module.session_store = SessionStore(max_history=20)
    yield


class TestChatFlowCrisis:
    """Test that crisis messages bypass the LLM entirely."""

    @pytest.mark.asyncio
    async def test_crisis_message_returns_crisis_type(self):
        response = await process_message("I want to kill myself", "test-session")
        assert response.type == ResponseType.CRISIS

    @pytest.mark.asyncio
    async def test_crisis_response_contains_helplines(self):
        response = await process_message("I want to end my life", "test-session")
        assert "14416" in response.reply
        assert "1800-599-0019" in response.reply

    @pytest.mark.asyncio
    @patch("app.services.chat_service.generate_response")
    async def test_crisis_does_not_call_llm(self, mock_generate):
        """The LLM should never be called for crisis messages."""
        await process_message("I want to kill myself", "test-session")
        mock_generate.assert_not_called()


class TestChatFlowOffTopic:
    """Test that off-topic messages get redirected without calling the main LLM."""

    @pytest.mark.asyncio
    @patch("app.guardrails.topic_classifier._llm_classify", new_callable=AsyncMock)
    @patch("app.services.chat_service.generate_response", new_callable=AsyncMock)
    async def test_off_topic_returns_redirect(self, mock_generate, mock_classify):
        response = await process_message("Write me a Python script", "test-session")
        assert response.type == ResponseType.REDIRECT
        mock_generate.assert_not_called()


class TestChatFlowNormal:
    """Test the normal (on-topic, non-crisis) message flow."""

    @pytest.mark.asyncio
    @patch("app.services.chat_service.retrieve_context", return_value="")
    @patch("app.services.chat_service.generate_response", new_callable=AsyncMock)
    async def test_normal_message_calls_llm(self, mock_generate, mock_retrieve):
        mock_generate.return_value = "I hear you. That sounds really difficult."
        response = await process_message("I'm feeling really anxious today", "test-session")
        assert response.type == ResponseType.NORMAL
        mock_generate.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.chat_service.retrieve_context", return_value="")
    @patch("app.services.chat_service.generate_response", new_callable=AsyncMock)
    async def test_session_history_is_stored(self, mock_generate, mock_retrieve):
        mock_generate.return_value = "I'm here for you."
        # Use the session_store as seen by chat_service (same singleton)
        import app.services.chat_service as cs

        await process_message("I feel sad", "hist-session")
        history = cs.session_store.get_history("hist-session")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"


class TestOutputModeration:
    """Test that output moderation catches unsafe content."""

    @pytest.mark.asyncio
    @patch("app.services.chat_service.retrieve_context", return_value="")
    @patch("app.services.chat_service.generate_response", new_callable=AsyncMock)
    async def test_diagnosis_language_is_moderated(self, mock_generate, mock_retrieve):
        mock_generate.return_value = "You have depression and should take medication."
        response = await process_message("I've been feeling low for weeks", "test-session")
        # The diagnostic language should be softened
        assert "you have depression" not in response.reply.lower()
