"""Tests for the concern classifier module — keyword-based classification + integration."""

import pytest
from unittest.mock import AsyncMock, patch

from app.guardrails.concern_classifier import (
    _keyword_classify_concern,
    classify_concern,
    get_therapist_suggestions,
    _CTA_VARIANTS,
)
from app.models.schemas import ResponseType
from app.services.chat_service import process_message
from app.utils.session_store import SessionStore


@pytest.fixture(autouse=True)
def clean_session_store():
    """Reset session store before each test."""
    from app.utils import session_store as ss_module
    ss_module.session_store = SessionStore(max_history=20)
    yield


class TestKeywordClassifyConcern:
    """Test the fast keyword-based concern classification layer."""

    # ── Stress messages ───────────────────────────────────────────────

    @pytest.mark.parametrize("message", [
        "I'm so stressed about my deadlines",
        "Work has been really overwhelming lately",
        "I feel completely burnt out from my job",
        "The pressure at work is too much",
        "I'm exhausted and can't cope anymore",
        "My workload is crushing me",
    ])
    def test_stress_messages(self, message: str):
        result = _keyword_classify_concern(message)
        assert result == "stress", f"Expected stress for: {message!r}, got {result!r}"

    # ── Anxiety messages ──────────────────────────────────────────────

    @pytest.mark.parametrize("message", [
        "I'm feeling really anxious about everything",
        "I had a panic attack today",
        "I can't stop worrying about the future",
        "My nervousness is getting worse",
        "I'm afraid of going outside",
        "I keep overthinking everything",
        "I feel this constant sense of dread",
    ])
    def test_anxiety_messages(self, message: str):
        result = _keyword_classify_concern(message)
        assert result == "anxiety", f"Expected anxiety for: {message!r}, got {result!r}"

    # ── Relationship messages ─────────────────────────────────────────

    @pytest.mark.parametrize("message", [
        "My boyfriend and I broke up last week",
        "I'm going through a really painful breakup",
        "I think my partner is cheating on me",
        "My marriage is falling apart",
        "I'm dealing with a divorce",
        "I have trust issues with my girlfriend",
        "My ex-boyfriend keeps contacting me",
    ])
    def test_relationship_messages(self, message: str):
        result = _keyword_classify_concern(message)
        assert result == "relationship", f"Expected relationship for: {message!r}, got {result!r}"

    # ── None / unrelated messages ─────────────────────────────────────

    @pytest.mark.parametrize("message", [
        "I'm feeling sad today",
        "I can't sleep at night",
        "Hello, how are you?",
        "I need someone to talk to",
        "I've been feeling unmotivated lately",
    ])
    def test_none_or_ambiguous_messages(self, message: str):
        result = _keyword_classify_concern(message)
        assert result is None, f"Expected None for: {message!r}, got {result!r}"


class TestGetTherapistSuggestions:
    """Test the therapist suggestion lookup."""

    def test_stress_returns_therapists(self):
        result = get_therapist_suggestions("stress")
        assert result is not None
        therapists, cta = result
        assert len(therapists) == 3
        assert cta in _CTA_VARIANTS

    def test_anxiety_returns_therapists(self):
        result = get_therapist_suggestions("anxiety")
        assert result is not None
        therapists, cta = result
        assert len(therapists) == 3

    def test_relationship_returns_therapists(self):
        result = get_therapist_suggestions("relationship")
        assert result is not None
        therapists, cta = result
        assert len(therapists) == 3

    def test_none_returns_nothing(self):
        result = get_therapist_suggestions("none")
        assert result is None

    def test_invalid_category_returns_nothing(self):
        result = get_therapist_suggestions("unknown")
        assert result is None

    def test_therapist_links_are_valid(self):
        for category in ["stress", "anxiety", "relationship"]:
            result = get_therapist_suggestions(category)
            assert result is not None
            therapists, _ = result
            for t in therapists:
                assert "name" in t
                assert "link" in t
                assert t["link"].startswith("https://dashboard.mindpeers.co/")

    def test_cta_varies(self):
        """CTA should not always be the same string."""
        ctas = set()
        # Run enough times to get variation (probabilistic but reliable with 5 variants)
        for _ in range(50):
            result = get_therapist_suggestions("stress")
            assert result is not None
            _, cta = result
            ctas.add(cta)
        assert len(ctas) > 1, "CTA should vary across calls"


class TestCrisisPathNoSuggestions:
    """Test that crisis messages never produce therapist suggestions."""

    @pytest.mark.asyncio
    async def test_crisis_message_has_no_suggestions(self):
        response = await process_message("I want to kill myself", "test-session-crisis")
        assert response.type == ResponseType.CRISIS
        assert response.suggested_category is None
        assert response.suggested_therapists is None
        assert response.therapist_cta is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", [
        "I want to end my life",
        "I've been self-harming",
        "suicidal thoughts",
    ])
    async def test_multiple_crisis_messages_no_suggestions(self, message: str):
        response = await process_message(message, "test-session-crisis-2")
        assert response.type == ResponseType.CRISIS
        assert response.suggested_therapists is None


class TestNormalPathWithSuggestions:
    """Test that normal on-topic messages can produce therapist suggestions."""

    @pytest.mark.asyncio
    @patch("app.services.chat_service.retrieve_context", return_value="")
    @patch("app.services.chat_service.generate_response", new_callable=AsyncMock)
    async def test_stress_message_gets_suggestions(self, mock_generate, mock_retrieve):
        mock_generate.return_value = "I hear you. Work pressure can be really draining."
        response = await process_message(
            "I'm so stressed about my deadlines at work",
            "test-session-suggestions",
        )
        assert response.type == ResponseType.NORMAL
        assert response.suggested_category == "stress"
        assert response.suggested_therapists is not None
        assert len(response.suggested_therapists) == 3
        assert response.therapist_cta is not None

    @pytest.mark.asyncio
    @patch("app.services.chat_service.retrieve_context", return_value="")
    @patch("app.services.chat_service.generate_response", new_callable=AsyncMock)
    async def test_generic_message_no_suggestions(self, mock_generate, mock_retrieve):
        """A message without clear stress/anxiety/relationship signals should not get suggestions."""
        mock_generate.return_value = "I'm here for you."
        # "Hello" is in-scope (greeting) but no concern category
        response = await process_message("Hello, how are you?", "test-session-no-suggest")
        assert response.type == ResponseType.NORMAL
        assert response.suggested_category is None
        assert response.suggested_therapists is None
