"""Tests for the crisis detector module."""

import pytest
from app.guardrails.crisis_detector import detect_crisis, get_crisis_response, CRISIS_RESPONSE


class TestCrisisDetection:
    """Test that the crisis detector correctly identifies crisis language."""

    # ── Positive cases: these SHOULD trigger ──────────────────────────

    @pytest.mark.parametrize("message", [
        "I want to kill myself",
        "i want to die",
        "I don't want to be alive anymore",
        "I'm thinking about suicide",
        "I want to end my life",
        "I've been cutting myself",
        "I'm going to hurt myself",
        "no point in living",
        "I wish I was dead",
        "better off dead",
        "I have a plan to end it",
        "this is my last message",
        "I want to end it all",
        "thinking about ending my life",
        "I'm going to jump off",
        "I took too many pills",
        "I've been self-harming",
        "want to hurt myself",
        "suicidal thoughts",
        "I feel suicidal",
        "no reason to live",
        "considering suicide",
        "WANT TO KILL MYSELF",  # Case insensitive
        "  i want to die  ",   # With whitespace
    ])
    def test_positive_crisis_detection(self, message: str):
        assert detect_crisis(message) is True, f"Expected crisis for: {message!r}"

    # ── Negative cases: these should NOT trigger ──────────────────────

    @pytest.mark.parametrize("message", [
        "I feel sad today",
        "I'm having a bad day",
        "I'm stressed about work",
        "I can't sleep at night",
        "I feel anxious about my exam",
        "My relationship is falling apart",
        "I feel lonely",
        "I'm overwhelmed with work",
        "I need to talk to someone",
        "Hello, how are you?",
        "Write me a Python script",
        "What's the weather like?",
        "I feel like giving up on this project",
        "This job is killing me",  # Figurative use — should NOT trigger
        "I'm dying to see that movie",  # Figurative use
        "That joke killed me",  # Figurative use
    ])
    def test_negative_crisis_detection(self, message: str):
        assert detect_crisis(message) is False, f"False positive for: {message!r}"


class TestCrisisResponse:
    """Test that the crisis response is correct and contains helpline numbers."""

    def test_response_contains_tele_manas(self):
        response = get_crisis_response()
        assert "14416" in response
        assert "1-800-891-4416" in response

    def test_response_contains_kiran(self):
        response = get_crisis_response()
        assert "1800-599-0019" in response

    def test_response_contains_vandrevala(self):
        response = get_crisis_response()
        assert "1860-266-2345" in response
        assert "9999 666 555" in response

    def test_response_is_not_empty(self):
        assert len(get_crisis_response()) > 100

    def test_response_is_deterministic(self):
        """The crisis response should always be the same — no LLM involvement."""
        assert get_crisis_response() == CRISIS_RESPONSE
        assert get_crisis_response() == get_crisis_response()
