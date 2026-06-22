"""Tests for the topic classifier module — keyword-based classification only."""

import pytest
from app.guardrails.topic_classifier import _keyword_classify, REDIRECT_RESPONSE


class TestKeywordClassification:
    """Test the fast keyword-based classification layer."""

    # ── In-scope messages ─────────────────────────────────────────────

    @pytest.mark.parametrize("message", [
        "I'm feeling really anxious today",
        "I can't sleep at night",
        "I'm stressed about my exams",
        "My relationship is falling apart",
        "I feel lonely all the time",
        "I need help coping with grief",
        "I'm so tired and burnt out from work",
        "I've been feeling sad for weeks",
        "How can I manage my anger better?",
        "I'm having trouble with motivation",
        "Can you help me with breathing exercises?",
        "I want to talk about my feelings",
        "I'm worried about my mental health",
        "I feel overwhelmed and don't know what to do",
        "My self-esteem is really low",
        "I've been crying a lot lately",
        "I feel empty inside",
        "Hello",
        "Hi there",
        "Thank you for listening",
    ])
    def test_in_scope_messages(self, message: str):
        result = _keyword_classify(message)
        assert result == "in_scope", f"Expected in_scope for: {message!r}, got {result!r}"

    # ── Off-topic messages ────────────────────────────────────────────

    @pytest.mark.parametrize("message", [
        "Write me a Python script to sort a list",
        "What's the recipe for butter chicken?",
        "Who won the cricket match yesterday?",
        "Help me with my math homework",
        "Calculate the integral of x squared",
        "Write a program to reverse a string",
        "What is the capital of France?",
        "Tell me a joke",
        "Write a story about a dragon",
        "How do I debug this error message?",
        "What's the stock price of Apple?",
    ])
    def test_off_topic_messages(self, message: str):
        result = _keyword_classify(message)
        assert result == "off_topic", f"Expected off_topic for: {message!r}, got {result!r}"

    # ── Ambiguous messages (should return None for LLM fallback) ──────

    @pytest.mark.parametrize("message", [
        "What should I do?",
        "I don't know anymore",
        "Everything is too much",
    ])
    def test_ambiguous_messages(self, message: str):
        result = _keyword_classify(message)
        # These could be None (ambiguous) or in_scope — either is acceptable
        assert result in (None, "in_scope"), f"Ambiguous message wrongly classified as off_topic: {message!r}"


class TestRedirectResponse:
    """Test that the redirect response is appropriate."""

    def test_redirect_is_friendly(self):
        assert "wellbeing" in REDIRECT_RESPONSE.lower() or "well-being" in REDIRECT_RESPONSE.lower()

    def test_redirect_is_not_preachy(self):
        # Should be short — one or two sentences
        assert len(REDIRECT_RESPONSE) < 300

    def test_redirect_is_not_empty(self):
        assert len(REDIRECT_RESPONSE) > 20
