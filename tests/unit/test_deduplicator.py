"""Unit tests for n-gram deduplicator."""

import pytest

from src.deduplicator.ngram import NGramDeduplicator
from src.models.transcript import Transcript


class TestNGramDeduplicator:
    """Tests for NGramDeduplicator."""
    
    def test_remove_consecutive_duplicates(self):
        """Test removing consecutive duplicate words."""
        dedup = NGramDeduplicator()
        
        text = "the the quick quick brown fox"
        result = dedup.deduplicate_text(text)
        
        assert result == "the quick brown fox"
    
    def test_remove_repeated_bigrams(self):
        """Test removing repeated bigrams."""
        dedup = NGramDeduplicator()
        
        text = "hello world hello world how are you"
        result = dedup.deduplicate_text(text)
        
        assert "hello world hello world" not in result
        assert "hello world" in result
    
    def test_remove_repeated_trigrams(self):
        """Test removing repeated trigrams."""
        dedup = NGramDeduplicator()
        
        text = "one two three one two three four"
        result = dedup.deduplicate_text(text)
        
        assert result.count("one two three") == 1
    
    def test_preserve_non_duplicate_text(self):
        """Test that non-duplicate text is preserved."""
        dedup = NGramDeduplicator()
        
        text = "the quick brown fox jumps over the lazy dog"
        result = dedup.deduplicate_text(text)
        
        assert result == text
    
    def test_empty_string(self):
        """Test handling empty string."""
        dedup = NGramDeduplicator()
        
        assert dedup.deduplicate_text("") == ""
        assert dedup.deduplicate_text("   ") == ""
    
    def test_single_word(self):
        """Test handling single word."""
        dedup = NGramDeduplicator()
        
        assert dedup.deduplicate_text("hello") == "hello"
    
    def test_deduplicate_transcript(self):
        """Test deduplicating a Transcript object."""
        dedup = NGramDeduplicator()
        
        transcript = Transcript(
            text="hello hello world world",
            model_name="test",
            chunk_index=0,
        )
        
        result = dedup.deduplicate_transcript(transcript)
        
        assert result.text == "hello world"
        assert result.deduplicated is True
        assert result.raw_text == "hello hello world world"
    
    def test_deduplicate_multiple_transcripts(self):
        """Test deduplicating multiple transcripts."""
        dedup = NGramDeduplicator()
        
        transcripts = [
            Transcript(text="one one two", model_name="test", chunk_index=0),
            Transcript(text="three three four", model_name="test", chunk_index=1),
        ]
        
        results = dedup.deduplicate_transcripts(transcripts)
        
        assert len(results) == 2
        assert results[0].text == "one two"
        assert results[1].text == "three four"
    
    def test_case_insensitive_deduplication(self):
        """Test that deduplication is case-insensitive."""
        dedup = NGramDeduplicator()
        
        # Note: The current implementation preserves first occurrence case
        text = "Hello hello world"
        result = dedup.deduplicate_text(text)
        
        # Should remove duplicate regardless of case
        assert result.lower().count("hello") == 1

