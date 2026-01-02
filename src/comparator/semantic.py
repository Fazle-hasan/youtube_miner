"""Semantic similarity using sentence embeddings."""

import logging
import os
from pathlib import Path
from typing import Optional

import torch
from sentence_transformers import SentenceTransformer, util

from src.comparator.normalizer import TextNormalizer

# Load environment variables from .env file (optional - graceful fallback)
try:
    from dotenv import load_dotenv
    _project_root = Path(__file__).parent.parent.parent
    load_dotenv(_project_root / ".env")
except ImportError:
    # python-dotenv not installed - user must set env vars manually
    pass

logger = logging.getLogger(__name__)


class SemanticSimilarity:
    """Calculate semantic similarity using sentence embeddings.
    
    Uses sentence-transformers to generate embeddings and
    calculates cosine similarity between them.
    
    Example:
        >>> sim = SemanticSimilarity()
        >>> score = sim.calculate("The cat sat on the mat", "A cat is sitting on a mat")
        >>> print(f"Similarity: {score:.2%}")
    """
    
    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        normalize_text: bool = True,
        device: Optional[str] = None,
    ):
        """Initialize semantic similarity calculator.
        
        Args:
            model_name: Name of sentence-transformers model to use.
            normalize_text: Whether to normalize texts before comparison.
            device: Device to use ('cuda', 'cpu', or None for auto).
        """
        self.model_name = model_name
        self.normalize_text = normalize_text
        self.device = device
        self.normalizer = TextNormalizer() if normalize_text else None
        self._model = None
    
    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        if self._model is None:
            logger.info(f"Loading sentence transformer: {self.model_name}")
            hf_token = os.environ.get("HF_TOKEN")
            try:
                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    token=hf_token,
                )
                logger.info("Sentence transformer loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
                logger.info("Attempting to load without token...")
                self._model = SentenceTransformer(self.model_name, device=self.device)
    
    def calculate(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts.
        
        Args:
            text1: First text.
            text2: Second text.
            
        Returns:
            Cosine similarity score (0-1, higher is more similar).
        """
        self._load_model()
        
        if self.normalizer:
            text1, text2 = self.normalizer.normalize_pair(text1, text2)
        
        # Handle empty cases
        if not text1.strip() or not text2.strip():
            return 1.0 if text1.strip() == text2.strip() else 0.0
        
        try:
            # Generate embeddings
            embeddings = self._model.encode(
                [text1, text2],
                convert_to_tensor=True,
                show_progress_bar=False,
            )
            
            # Calculate cosine similarity
            similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
            
            # Ensure in range [0, 1]
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def calculate_batch(self, text_pairs: list) -> list:
        """Calculate semantic similarity for multiple pairs.
        
        Args:
            text_pairs: List of (text1, text2) tuples.
            
        Returns:
            List of similarity scores.
        """
        self._load_model()
        
        results = []
        for text1, text2 in text_pairs:
            score = self.calculate(text1, text2)
            results.append(score)
        
        return results
    
    def unload_model(self) -> None:
        """Unload model from memory."""
        self._model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Sentence transformer unloaded")