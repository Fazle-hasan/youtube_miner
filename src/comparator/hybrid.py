"""Hybrid scoring combining error rates and semantic similarity."""

import logging
from typing import Dict, Optional

from src.comparator.wer import WERCalculator
from src.comparator.cer import CERCalculator
from src.comparator.semantic import SemanticSimilarity
from src.models.comparison import ComparisonResult

logger = logging.getLogger(__name__)


class HybridScore:
    """Calculate hybrid SeMaScore combining multiple metrics.
    
    SeMaScore combines traditional error rates (WER, CER) with
    semantic similarity to better match human judgments of
    transcript quality.
    
    Formula:
        hybrid = alpha * (1 - WER) + (1 - alpha) * semantic_similarity
    
    Example:
        >>> scorer = HybridScore()
        >>> result = scorer.compare("hello world", "hello there")
        >>> print(f"Hybrid: {result.hybrid_score:.2%}")
    """
    
    def __init__(
        self,
        alpha: float = 0.5,
        normalize: bool = True,
        include_cer: bool = True,
    ):
        """Initialize hybrid scorer.
        
        Args:
            alpha: Weight for WER component (0-1).
                   Higher alpha = more weight on word accuracy.
            normalize: Whether to normalize texts before comparison.
            include_cer: Whether to include CER in scoring.
        """
        self.alpha = alpha
        self.include_cer = include_cer
        
        self.wer_calc = WERCalculator(normalize=normalize)
        self.cer_calc = CERCalculator(normalize=normalize)
        self.semantic_calc = SemanticSimilarity(normalize_text=normalize)
    
    def calculate(
        self,
        reference: str,
        hypothesis: str,
    ) -> Dict[str, float]:
        """Calculate all metrics for a text pair.
        
        Args:
            reference: Reference text (ground truth).
            hypothesis: Hypothesis text (model output).
            
        Returns:
            Dictionary with all metrics.
        """
        wer = self.wer_calc.calculate(reference, hypothesis)
        cer = self.cer_calc.calculate(reference, hypothesis)
        semantic = self.semantic_calc.calculate(reference, hypothesis)
        
        # Calculate hybrid score
        hybrid = self._calculate_hybrid(wer, semantic)
        
        return {
            "wer": wer,
            "cer": cer,
            "semantic_similarity": semantic,
            "hybrid_score": hybrid,
        }
    
    def _calculate_hybrid(self, wer: float, semantic: float) -> float:
        """Calculate hybrid SeMaScore.
        
        Args:
            wer: Word Error Rate.
            semantic: Semantic similarity.
            
        Returns:
            Hybrid score (0-1, higher is better).
        """
        accuracy = 1.0 - min(wer, 1.0)
        return self.alpha * accuracy + (1 - self.alpha) * semantic
    
    def compare(
        self,
        reference: str,
        hypothesis: str,
        chunk_index: int = 0,
    ) -> ComparisonResult:
        """Compare texts and return ComparisonResult.
        
        Args:
            reference: Reference text (e.g., YouTube caption).
            hypothesis: Hypothesis text (e.g., model transcript).
            chunk_index: Index of the chunk being compared.
            
        Returns:
            ComparisonResult with all metrics.
        """
        metrics = self.calculate(reference, hypothesis)
        
        # Get normalized texts for the result
        norm_ref, norm_hyp = self.wer_calc.normalizer.normalize_pair(
            reference, hypothesis
        ) if self.wer_calc.normalizer else (reference, hypothesis)
        
        return ComparisonResult(
            chunk_index=chunk_index,
            normalized_transcript=norm_hyp,
            normalized_caption=norm_ref,
            wer=metrics["wer"],
            cer=metrics["cer"],
            semantic_similarity=metrics["semantic_similarity"],
            hybrid_score=metrics["hybrid_score"],
        )
    
    def compare_all(
        self,
        reference_texts: list,
        hypothesis_texts: list,
    ) -> list:
        """Compare multiple text pairs.
        
        Args:
            reference_texts: List of reference texts.
            hypothesis_texts: List of hypothesis texts.
            
        Returns:
            List of ComparisonResult objects.
        """
        if len(reference_texts) != len(hypothesis_texts):
            raise ValueError("Reference and hypothesis lists must have same length")
        
        results = []
        for i, (ref, hyp) in enumerate(zip(reference_texts, hypothesis_texts)):
            result = self.compare(ref, hyp, chunk_index=i)
            results.append(result)
        
        return results
    
    def unload_models(self) -> None:
        """Unload all models from memory."""
        self.semantic_calc.unload_model()
        logger.info("Hybrid scorer models unloaded")

