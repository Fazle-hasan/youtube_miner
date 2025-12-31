"""Text normalization for comparison."""

import re
import string
from typing import Tuple


class TextNormalizer:
    """Normalize text for fair comparison between transcripts.
    
    Applies consistent normalization to both model output and
    YouTube captions before calculating comparison metrics.
    
    Example:
        >>> normalizer = TextNormalizer()
        >>> text = "Hello, World! It's 123."
        >>> normalized = normalizer.normalize(text)
        >>> print(normalized)  # "hello world its one two three"
    """
    
    # Number to word mappings
    NUMBER_WORDS = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
    }
    
    def __init__(
        self,
        lowercase: bool = True,
        remove_punctuation: bool = True,
        collapse_whitespace: bool = True,
        numbers_to_words: bool = False,
        expand_contractions: bool = True,
    ):
        """Initialize the normalizer.
        
        Args:
            lowercase: Convert to lowercase.
            remove_punctuation: Remove punctuation marks.
            collapse_whitespace: Collapse multiple spaces to one.
            numbers_to_words: Convert digits to words.
            expand_contractions: Expand contractions (it's -> it is).
        """
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        self.collapse_whitespace = collapse_whitespace
        self.numbers_to_words = numbers_to_words
        self.expand_contractions = expand_contractions
        
        # Common contractions
        self.contractions = {
            "won't": "will not",
            "can't": "cannot",
            "n't": " not",
            "'re": " are",
            "'s": " is",
            "'d": " would",
            "'ll": " will",
            "'ve": " have",
            "'m": " am",
        }
    
    def normalize(self, text: str) -> str:
        """Apply all normalization steps to text.
        
        Args:
            text: Input text to normalize.
            
        Returns:
            Normalized text.
        """
        if not text:
            return ""
        
        # Step 1: Lowercase
        if self.lowercase:
            text = text.lower()
        
        # Step 2: Expand contractions
        if self.expand_contractions:
            text = self._expand_contractions(text)
        
        # Step 3: Numbers to words
        if self.numbers_to_words:
            text = self._numbers_to_words(text)
        
        # Step 4: Remove punctuation
        if self.remove_punctuation:
            text = self._remove_punctuation(text)
        
        # Step 5: Collapse whitespace
        if self.collapse_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def normalize_pair(self, text1: str, text2: str) -> Tuple[str, str]:
        """Normalize both texts identically.
        
        Args:
            text1: First text (e.g., model transcript).
            text2: Second text (e.g., YouTube caption).
            
        Returns:
            Tuple of normalized (text1, text2).
        """
        return self.normalize(text1), self.normalize(text2)
    
    def _expand_contractions(self, text: str) -> str:
        """Expand contractions in text.
        
        Args:
            text: Input text.
            
        Returns:
            Text with contractions expanded.
        """
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
        return text
    
    def _numbers_to_words(self, text: str) -> str:
        """Convert digits to words.
        
        Args:
            text: Input text.
            
        Returns:
            Text with digits converted to words.
        """
        result = []
        for char in text:
            if char in self.NUMBER_WORDS:
                result.append(self.NUMBER_WORDS[char])
            else:
                result.append(char)
        return ''.join(result)
    
    def _remove_punctuation(self, text: str) -> str:
        """Remove punctuation from text.
        
        Args:
            text: Input text.
            
        Returns:
            Text without punctuation.
        """
        # Keep apostrophes inside words for contractions
        text = re.sub(r"[^\w\s']", ' ', text)
        # Remove standalone apostrophes
        text = re.sub(r"\s+'|'\s+", ' ', text)
        return text

