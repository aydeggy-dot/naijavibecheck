"""Tests for utility functions."""

import pytest

from app.utils.text_processing import anonymize_username, truncate_text, clean_text
from app.utils.nigerian_context import is_pidgin, get_sentiment_hints, extract_slang_terms


class TestAnonymizeUsername:
    """Tests for username anonymization."""

    def test_normal_username(self):
        """Test anonymizing a normal username."""
        result = anonymize_username("johndoe123")
        assert result.startswith("joh")
        assert result.endswith("123")
        assert "*" in result

    def test_short_username(self):
        """Test anonymizing a short username."""
        result = anonymize_username("user")
        assert result == "u***"

    def test_very_short_username(self):
        """Test anonymizing a very short username."""
        result = anonymize_username("ab")
        assert result == "a***"

    def test_empty_username(self):
        """Test anonymizing an empty username."""
        result = anonymize_username("")
        assert result == "***"


class TestTruncateText:
    """Tests for text truncation."""

    def test_short_text(self):
        """Test text shorter than max length."""
        result = truncate_text("Hello", max_length=10)
        assert result == "Hello"

    def test_long_text(self):
        """Test text longer than max length."""
        result = truncate_text("This is a very long text", max_length=10)
        assert len(result) <= 10
        assert result.endswith("...")

    def test_empty_text(self):
        """Test empty text."""
        result = truncate_text("")
        assert result == ""


class TestCleanText:
    """Tests for text cleaning."""

    def test_extra_whitespace(self):
        """Test removing extra whitespace."""
        result = clean_text("  hello   world  ")
        assert result == "hello world"

    def test_empty_text(self):
        """Test empty text."""
        result = clean_text("")
        assert result == ""


class TestIsPidgin:
    """Tests for Pidgin detection."""

    def test_pidgin_text(self):
        """Test text with Pidgin."""
        assert is_pidgin("Na wa o, this one no be small thing")
        assert is_pidgin("Abeg make una calm down")
        assert is_pidgin("Wetin dey happen for here?")

    def test_non_pidgin_text(self):
        """Test text without Pidgin."""
        assert not is_pidgin("This is a normal English sentence")
        assert not is_pidgin("Hello, how are you?")


class TestGetSentimentHints:
    """Tests for sentiment hint extraction."""

    def test_positive_text(self):
        """Test text with positive indicators."""
        hints = get_sentiment_hints("You slay queen! 🔥💯")
        assert hints["positive"] > 0

    def test_negative_text(self):
        """Test text with negative indicators."""
        hints = get_sentiment_hints("This is terrible and fake")
        assert hints["negative"] > 0

    def test_neutral_text(self):
        """Test neutral text."""
        hints = get_sentiment_hints("I went to the store today")
        assert hints["positive"] == 0
        assert hints["negative"] == 0


class TestExtractSlangTerms:
    """Tests for slang term extraction."""

    def test_with_slang(self):
        """Test text with slang terms."""
        terms = extract_slang_terms("Omo, e choke! This wahala no be small")
        assert "omo" in terms
        assert "e choke" in terms
        assert "wahala" in terms

    def test_without_slang(self):
        """Test text without slang."""
        terms = extract_slang_terms("This is a normal sentence")
        assert len(terms) == 0
