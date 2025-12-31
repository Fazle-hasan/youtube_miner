"""Unit tests for text normalizer."""

import pytest

from src.comparator.normalizer import TextNormalizer


class TestTextNormalizer:
    """Tests for TextNormalizer."""
    
    def test_lowercase(self):
        """Test lowercase conversion."""
        normalizer = TextNormalizer()
        
        assert normalizer.normalize("Hello WORLD") == "hello world"
    
    def test_remove_punctuation(self):
        """Test punctuation removal."""
        normalizer = TextNormalizer()
        
        result = normalizer.normalize("Hello, world! How are you?")
        assert "," not in result
        assert "!" not in result
        assert "?" not in result
    
    def test_collapse_whitespace(self):
        """Test whitespace collapsing."""
        normalizer = TextNormalizer()
        
        result = normalizer.normalize("hello   world\n\ttab")
        assert "  " not in result
        assert result == "hello world tab"
    
    def test_expand_contractions(self):
        """Test contraction expansion."""
        normalizer = TextNormalizer(expand_contractions=True)
        
        assert "is not" in normalizer.normalize("isn't")
        assert "will not" in normalizer.normalize("won't")
        assert "cannot" in normalizer.normalize("can't")
    
    def test_normalize_pair(self):
        """Test normalizing a pair of texts."""
        normalizer = TextNormalizer()
        
        t1, t2 = normalizer.normalize_pair(
            "Hello, World!",
            "HELLO WORLD"
        )
        
        assert t1 == t2
    
    def test_empty_string(self):
        """Test handling empty strings."""
        normalizer = TextNormalizer()
        
        assert normalizer.normalize("") == ""
        assert normalizer.normalize("   ") == ""
    
    def test_numbers_to_words_disabled(self):
        """Test that numbers are kept by default."""
        normalizer = TextNormalizer(numbers_to_words=False)
        
        result = normalizer.normalize("I have 5 apples")
        assert "5" in result
    
    def test_numbers_to_words_enabled(self):
        """Test number to word conversion."""
        normalizer = TextNormalizer(numbers_to_words=True)
        
        result = normalizer.normalize("I have 5 apples")
        assert "five" in result
        assert "5" not in result

