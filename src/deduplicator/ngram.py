"""N-gram based repetition removal for transcripts."""

import logging
import re
from typing import List, Tuple

from src.models.transcript import Transcript

logger = logging.getLogger(__name__)


class NGramDeduplicator:
    """Remove repetitive words and phrases using n-gram analysis.
    
    This class detects and removes stuttering and repeated phrases
    that commonly occur in speech-to-text output, especially from
    smaller models like Whisper-Tiny.
    
    Example:
        >>> dedup = NGramDeduplicator()
        >>> text = "the the quick quick brown brown fox"
        >>> cleaned = dedup.deduplicate_text(text)
        >>> print(cleaned)  # "the quick brown fox"
    """
    
    def __init__(self, min_n: int = 1, max_n: int = 30):
        """Initialize the deduplicator.
        
        Args:
            min_n: Minimum n-gram size to check (default: 1 for single word).
            max_n: Maximum n-gram size to check (default: 30 for sentences).
        """
        self.min_n = min_n
        self.max_n = max_n
    
    def deduplicate_text(self, text: str) -> str:
        """Remove repeated words and phrases from text.
        
        Handles multiple types of repetition:
        1. Sentence-level repetition (e.g., entire clauses repeated 3x)
        2. Phrase-level repetition (5-15 words)
        3. Word-level repetition (single words)
        
        Args:
            text: Input text with potential repetitions.
            
        Returns:
            Cleaned text with repetitions removed.
        """
        if not text or not text.strip():
            return ""
        
        original_text = text
        
        # Step 1: Remove large repeated segments (sentence-level)
        # This catches patterns like "X Y Z. X Y Z. X Y Z." 
        text = self._remove_large_repetitions(text)
        
        # Step 2: Remove medium n-gram repetitions (phrases)
        for n in range(min(self.max_n, 20), 4, -1):
            text = self._remove_repeated_ngrams(text, n)
        
        # Step 3: Remove small n-gram repetitions (1-4 words)
        for n in range(4, self.min_n, -1):
            text = self._remove_repeated_ngrams(text, n)
        
        # Step 4: Remove consecutive duplicate words
        text = self._remove_consecutive_duplicates(text)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Log significant reduction
        original_words = len(original_text.split())
        cleaned_words = len(text.split())
        if original_words > 0 and cleaned_words < original_words * 0.7:
            reduction = ((original_words - cleaned_words) / original_words) * 100
            logger.info(f"Heavy deduplication: {original_words} -> {cleaned_words} words ({reduction:.1f}% reduction)")
        
        return text
    
    def _remove_large_repetitions(self, text: str) -> str:
        """Remove large repeated segments using pattern detection.
        
        This method specifically handles Whisper's tendency to repeat
        entire sentences or clauses multiple times.
        
        Args:
            text: Input text.
            
        Returns:
            Text with large repetitions removed.
        """
        words = text.split()
        if len(words) < 10:
            return text
        
        # Try different segment sizes from large to small
        for segment_size in range(min(len(words) // 2, 25), 5, -1):
            words = self._remove_segment_repetitions(words, segment_size)
        
        return ' '.join(words)
    
    def _remove_segment_repetitions(self, words: List[str], segment_size: int) -> List[str]:
        """Remove repeated segments of a specific size.
        
        Args:
            words: List of words.
            segment_size: Size of segment to check for repetition.
            
        Returns:
            Words with repeated segments removed.
        """
        if len(words) < segment_size * 2:
            return words
        
        result = []
        i = 0
        
        while i < len(words):
            if i + segment_size * 2 <= len(words):
                current_segment = tuple(w.lower() for w in words[i:i+segment_size])
                next_segment = tuple(w.lower() for w in words[i+segment_size:i+segment_size*2])
                
                # Check for similarity (allowing small differences)
                if self._segments_similar(current_segment, next_segment):
                    # Keep first occurrence
                    result.extend(words[i:i+segment_size])
                    i += segment_size
                    
                    # Skip all consecutive repetitions
                    while i + segment_size <= len(words):
                        check_segment = tuple(w.lower() for w in words[i:i+segment_size])
                        if self._segments_similar(current_segment, check_segment):
                            i += segment_size
                        else:
                            break
                else:
                    result.append(words[i])
                    i += 1
            else:
                result.append(words[i])
                i += 1
        
        return result
    
    def _segments_similar(self, seg1: Tuple[str, ...], seg2: Tuple[str, ...]) -> bool:
        """Check if two segments are similar (allowing minor differences).
        
        Args:
            seg1: First segment as tuple of lowercase words.
            seg2: Second segment as tuple of lowercase words.
            
        Returns:
            True if segments are similar enough to be considered duplicates.
        """
        if seg1 == seg2:
            return True
        
        if len(seg1) != len(seg2):
            return False
        
        # Allow up to 10% difference for longer segments
        if len(seg1) >= 10:
            matches = sum(1 for a, b in zip(seg1, seg2) if a == b)
            return matches >= len(seg1) * 0.9
        
        return False
    
    def _remove_consecutive_duplicates(self, text: str) -> str:
        """Remove consecutive duplicate words.
        
        Args:
            text: Input text.
            
        Returns:
            Text with consecutive duplicates removed.
        """
        words = text.split()
        if not words:
            return text
        
        result = [words[0]]
        
        for word in words[1:]:
            # Skip if same as previous word (case-insensitive)
            if word.lower() != result[-1].lower():
                result.append(word)
        
        return ' '.join(result)
    
    def _remove_repeated_ngrams(self, text: str, n: int) -> str:
        """Remove repeated n-grams from text.
        
        Args:
            text: Input text.
            n: N-gram size.
            
        Returns:
            Text with repeated n-grams removed.
        """
        words = text.split()
        
        if len(words) < n * 2:
            return text
        
        result = []
        i = 0
        
        while i < len(words):
            # Check if current n-gram is repeated
            if i + n * 2 <= len(words):
                current_ngram = tuple(w.lower() for w in words[i:i+n])
                next_ngram = tuple(w.lower() for w in words[i+n:i+n*2])
                
                if current_ngram == next_ngram:
                    # Skip the duplicate, keep only first occurrence
                    result.extend(words[i:i+n])
                    i += n * 2
                    
                    # Continue skipping while more duplicates exist
                    while i + n <= len(words):
                        check_ngram = tuple(w.lower() for w in words[i:i+n])
                        if check_ngram == current_ngram:
                            i += n
                        else:
                            break
                else:
                    result.append(words[i])
                    i += 1
            else:
                result.append(words[i])
                i += 1
        
        return ' '.join(result)
    
    def deduplicate_transcript(self, transcript: Transcript) -> Transcript:
        """Deduplicate a transcript object.
        
        Args:
            transcript: Transcript to deduplicate.
            
        Returns:
            New Transcript with deduplicated text.
        """
        original_text = transcript.text
        cleaned_text = self.deduplicate_text(original_text)
        
        # Calculate reduction
        original_words = len(original_text.split())
        cleaned_words = len(cleaned_text.split())
        
        if original_words > cleaned_words:
            reduction = ((original_words - cleaned_words) / original_words) * 100
            logger.debug(
                f"Deduplication: {original_words} -> {cleaned_words} words "
                f"({reduction:.1f}% reduction)"
            )
        
        return Transcript(
            text=cleaned_text,
            model_name=transcript.model_name,
            chunk_index=transcript.chunk_index,
            confidence=transcript.confidence,
            language=transcript.language,
            processing_time=transcript.processing_time,
            raw_text=original_text,
            deduplicated=True,
        )
    
    def deduplicate_transcripts(self, transcripts: List[Transcript]) -> List[Transcript]:
        """Deduplicate multiple transcripts.
        
        Args:
            transcripts: List of transcripts to deduplicate.
            
        Returns:
            List of deduplicated transcripts.
        """
        return [self.deduplicate_transcript(t) for t in transcripts]

