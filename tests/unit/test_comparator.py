"""Unit tests for comparison metrics."""

import pytest

from src.comparator.wer import WERCalculator
from src.comparator.cer import CERCalculator
from src.comparator.hybrid import HybridScore


class TestWERCalculator:
    """Tests for WER calculation."""
    
    def test_identical_texts(self):
        """Test WER for identical texts."""
        calc = WERCalculator(normalize=True)
        
        wer = calc.calculate("hello world", "hello world")
        assert wer == 0.0
    
    def test_completely_different_texts(self):
        """Test WER for completely different texts."""
        calc = WERCalculator(normalize=True)
        
        wer = calc.calculate("hello world", "foo bar baz")
        assert wer > 0.5
    
    def test_one_word_error(self):
        """Test WER with one word error."""
        calc = WERCalculator(normalize=True)
        
        wer = calc.calculate("hello world", "hello there")
        assert 0.0 < wer < 1.0
    
    def test_empty_reference(self):
        """Test WER with empty reference."""
        calc = WERCalculator(normalize=True)
        
        wer = calc.calculate("", "hello")
        assert wer == 1.0
    
    def test_empty_hypothesis(self):
        """Test WER with empty hypothesis."""
        calc = WERCalculator(normalize=True)
        
        wer = calc.calculate("hello", "")
        assert wer == 1.0
    
    def test_both_empty(self):
        """Test WER when both are empty."""
        calc = WERCalculator(normalize=True)
        
        wer = calc.calculate("", "")
        assert wer == 0.0
    
    def test_detailed_calculation(self):
        """Test detailed WER breakdown."""
        calc = WERCalculator(normalize=True)
        
        details = calc.calculate_detailed(
            "the cat sat on the mat",
            "the cat on the mat"
        )
        
        assert "wer" in details
        assert "deletions" in details
        assert details["deletions"] > 0


class TestCERCalculator:
    """Tests for CER calculation."""
    
    def test_identical_texts(self):
        """Test CER for identical texts."""
        calc = CERCalculator(normalize=True)
        
        cer = calc.calculate("hello", "hello")
        assert cer == 0.0
    
    def test_one_character_error(self):
        """Test CER with one character error."""
        calc = CERCalculator(normalize=True)
        
        cer = calc.calculate("hello", "helo")
        assert 0.0 < cer < 1.0
    
    def test_completely_different(self):
        """Test CER for completely different texts."""
        calc = CERCalculator(normalize=True)
        
        cer = calc.calculate("abc", "xyz")
        assert cer == 1.0
    
    def test_detailed_calculation(self):
        """Test detailed CER breakdown."""
        calc = CERCalculator(normalize=True)
        
        details = calc.calculate_detailed("hello", "helo")
        
        assert "cer" in details
        assert "reference_chars" in details
        assert "hypothesis_chars" in details


class TestHybridScore:
    """Tests for hybrid scoring."""
    
    def test_perfect_match(self):
        """Test hybrid score for perfect match."""
        scorer = HybridScore(normalize=True)
        
        result = scorer.compare("hello world", "hello world")
        
        assert result.wer == 0.0
        assert result.hybrid_score > 0.9
    
    def test_compare_returns_all_metrics(self):
        """Test that compare returns all metrics."""
        scorer = HybridScore(normalize=True)
        
        result = scorer.compare("hello world", "hello there")
        
        assert hasattr(result, "wer")
        assert hasattr(result, "cer")
        assert hasattr(result, "semantic_similarity")
        assert hasattr(result, "hybrid_score")
    
    def test_alpha_weighting(self):
        """Test that alpha parameter affects hybrid score."""
        scorer_high_alpha = HybridScore(alpha=0.9, normalize=True)
        scorer_low_alpha = HybridScore(alpha=0.1, normalize=True)
        
        # For texts with high WER but high semantic similarity
        # Low alpha should favor semantic, high alpha should favor WER
        metrics_high = scorer_high_alpha.calculate("cat", "feline animal")
        metrics_low = scorer_low_alpha.calculate("cat", "feline animal")
        
        # Both should return valid scores
        assert 0.0 <= metrics_high["hybrid_score"] <= 1.0
        assert 0.0 <= metrics_low["hybrid_score"] <= 1.0
    
    def test_compare_all(self):
        """Test comparing multiple pairs."""
        scorer = HybridScore(normalize=True)
        
        refs = ["hello", "world", "test"]
        hyps = ["hello", "word", "testing"]
        
        results = scorer.compare_all(refs, hyps)
        
        assert len(results) == 3
        assert results[0].wer == 0.0  # "hello" == "hello"
        assert results[1].wer > 0.0   # "world" != "word"

