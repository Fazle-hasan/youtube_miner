"""Word Error Rate (WER) calculation."""

import logging
from typing import Tuple

from jiwer import wer as calculate_wer
from jiwer import process_words

from src.comparator.normalizer import TextNormalizer

logger = logging.getLogger(__name__)


class WERCalculator:
    """Calculate Word Error Rate between texts.
    
    WER = (S + D + I) / N
    where:
        S = Substitutions
        D = Deletions
        I = Insertions
        N = Total words in reference
    
    Example:
        >>> wer_calc = WERCalculator()
        >>> wer = wer_calc.calculate("hello world", "hello there world")
        >>> print(f"WER: {wer:.2%}")
    """
    
    def __init__(self, normalize: bool = True):
        """Initialize WER calculator.
        
        Args:
            normalize: Whether to normalize texts before comparison.
        """
        self.normalize = normalize
        self.normalizer = TextNormalizer() if normalize else None
    
    def calculate(self, reference: str, hypothesis: str) -> float:
        """Calculate WER between reference and hypothesis.
        
        Args:
            reference: Reference text (ground truth, e.g., YouTube caption).
            hypothesis: Hypothesis text (model output).
            
        Returns:
            WER as a float (0 = perfect, 1 = 100% errors).
        """
        if self.normalizer:
            reference, hypothesis = self.normalizer.normalize_pair(reference, hypothesis)
        
        # Handle empty cases
        if not reference.strip():
            return 0.0 if not hypothesis.strip() else 1.0
        if not hypothesis.strip():
            return 1.0
        
        try:
            error_rate = calculate_wer(reference, hypothesis)
            # Cap at 1.0 (100% error rate)
            return min(1.0, max(0.0, error_rate))
        except Exception as e:
            logger.warning(f"WER calculation failed: {e}")
            return 1.0
    
    def calculate_detailed(self, reference: str, hypothesis: str) -> dict:
        """Calculate WER with detailed breakdown.
        
        Args:
            reference: Reference text.
            hypothesis: Hypothesis text.
            
        Returns:
            Dictionary with WER and component counts.
        """
        if self.normalizer:
            reference, hypothesis = self.normalizer.normalize_pair(reference, hypothesis)
        
        if not reference.strip():
            return {
                "wer": 0.0 if not hypothesis.strip() else 1.0,
                "substitutions": 0,
                "deletions": 0,
                "insertions": len(hypothesis.split()) if hypothesis.strip() else 0,
                "reference_words": 0,
                "hypothesis_words": len(hypothesis.split()) if hypothesis.strip() else 0,
            }
        
        try:
            output = process_words(reference, hypothesis)
            
            return {
                "wer": min(1.0, output.wer),
                "substitutions": output.substitutions,
                "deletions": output.deletions,
                "insertions": output.insertions,
                "reference_words": len(reference.split()),
                "hypothesis_words": len(hypothesis.split()),
            }
        except Exception as e:
            logger.warning(f"Detailed WER calculation failed: {e}")
            return {
                "wer": 1.0,
                "substitutions": 0,
                "deletions": 0,
                "insertions": 0,
                "reference_words": len(reference.split()),
                "hypothesis_words": len(hypothesis.split()),
            }

