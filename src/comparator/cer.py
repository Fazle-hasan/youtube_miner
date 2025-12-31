"""Character Error Rate (CER) calculation."""

import logging

from jiwer import cer as calculate_cer

from src.comparator.normalizer import TextNormalizer

logger = logging.getLogger(__name__)


class CERCalculator:
    """Calculate Character Error Rate between texts.
    
    CER is similar to WER but operates at the character level,
    making it more sensitive to small differences and typos.
    
    Example:
        >>> cer_calc = CERCalculator()
        >>> cer = cer_calc.calculate("hello", "helo")
        >>> print(f"CER: {cer:.2%}")
    """
    
    def __init__(self, normalize: bool = True):
        """Initialize CER calculator.
        
        Args:
            normalize: Whether to normalize texts before comparison.
        """
        self.normalize = normalize
        self.normalizer = TextNormalizer() if normalize else None
    
    def calculate(self, reference: str, hypothesis: str) -> float:
        """Calculate CER between reference and hypothesis.
        
        Args:
            reference: Reference text (ground truth).
            hypothesis: Hypothesis text (model output).
            
        Returns:
            CER as a float (0 = perfect, 1 = 100% errors).
        """
        if self.normalizer:
            reference, hypothesis = self.normalizer.normalize_pair(reference, hypothesis)
        
        # Handle empty cases
        if not reference.strip():
            return 0.0 if not hypothesis.strip() else 1.0
        if not hypothesis.strip():
            return 1.0
        
        try:
            error_rate = calculate_cer(reference, hypothesis)
            # Cap at 1.0 (100% error rate)
            return min(1.0, max(0.0, error_rate))
        except Exception as e:
            logger.warning(f"CER calculation failed: {e}")
            return 1.0
    
    def calculate_detailed(self, reference: str, hypothesis: str) -> dict:
        """Calculate CER with detailed breakdown.
        
        Args:
            reference: Reference text.
            hypothesis: Hypothesis text.
            
        Returns:
            Dictionary with CER and character counts.
        """
        if self.normalizer:
            reference, hypothesis = self.normalizer.normalize_pair(reference, hypothesis)
        
        cer = self.calculate(reference, hypothesis)
        
        return {
            "cer": cer,
            "reference_chars": len(reference),
            "hypothesis_chars": len(hypothesis),
            "char_difference": abs(len(reference) - len(hypothesis)),
        }

