"""Comparison result data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ComparisonResult:
    """Represents comparison metrics between transcript and caption.
    
    Attributes:
        chunk_index: Index of the associated chunk.
        normalized_transcript: Normalized model transcription text.
        normalized_caption: Normalized YouTube caption text.
        wer: Word Error Rate (0-1, lower is better).
        cer: Character Error Rate (0-1, lower is better).
        semantic_similarity: Cosine similarity of embeddings (0-1, higher is better).
        hybrid_score: Combined SeMaScore metric.
        computed_at: Timestamp when comparison was computed.
    """
    chunk_index: int
    normalized_transcript: str
    normalized_caption: str
    wer: float
    cer: float
    semantic_similarity: float
    hybrid_score: Optional[float] = None
    computed_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Calculate hybrid score if not provided."""
        if self.hybrid_score is None:
            # SeMaScore: weighted combination of (1-WER) and semantic similarity
            self.hybrid_score = self._calculate_hybrid_score()
    
    def _calculate_hybrid_score(self, alpha: float = 0.5) -> float:
        """Calculate hybrid SeMaScore.
        
        Args:
            alpha: Weight for error rate component (default 0.5).
                   Higher alpha gives more weight to WER.
        
        Returns:
            Hybrid score between 0 and 1 (higher is better).
        """
        accuracy = 1.0 - min(self.wer, 1.0)  # Cap WER at 1.0
        return alpha * accuracy + (1 - alpha) * self.semantic_similarity
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "chunk_index": self.chunk_index,
            "normalized_transcript": self.normalized_transcript,
            "normalized_caption": self.normalized_caption,
            "wer": round(self.wer, 4),
            "cer": round(self.cer, 4),
            "semantic_similarity": round(self.semantic_similarity, 4),
            "hybrid_score": round(self.hybrid_score, 4) if self.hybrid_score else None,
            "computed_at": self.computed_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ComparisonResult":
        """Create ComparisonResult from dictionary."""
        return cls(
            chunk_index=data["chunk_index"],
            normalized_transcript=data["normalized_transcript"],
            normalized_caption=data["normalized_caption"],
            wer=data["wer"],
            cer=data["cer"],
            semantic_similarity=data["semantic_similarity"],
            hybrid_score=data.get("hybrid_score"),
        )


@dataclass
class MetricsSummary:
    """Aggregated metrics summary across all chunks.
    
    Attributes:
        avg_wer: Average Word Error Rate.
        avg_cer: Average Character Error Rate.
        avg_semantic_similarity: Average semantic similarity.
        avg_hybrid_score: Average hybrid SeMaScore.
        min_wer: Minimum WER (best chunk).
        max_wer: Maximum WER (worst chunk).
        std_wer: Standard deviation of WER.
        total_chunks: Number of chunks compared.
    """
    avg_wer: float
    avg_cer: float
    avg_semantic_similarity: float
    avg_hybrid_score: float
    min_wer: float = 0.0
    max_wer: float = 0.0
    std_wer: float = 0.0
    min_cer: float = 0.0
    max_cer: float = 0.0
    std_cer: float = 0.0
    total_chunks: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "avg_wer": round(self.avg_wer, 4),
            "avg_cer": round(self.avg_cer, 4),
            "avg_semantic_similarity": round(self.avg_semantic_similarity, 4),
            "avg_hybrid_score": round(self.avg_hybrid_score, 4),
            "min_wer": round(self.min_wer, 4),
            "max_wer": round(self.max_wer, 4),
            "std_wer": round(self.std_wer, 4),
            "min_cer": round(self.min_cer, 4),
            "max_cer": round(self.max_cer, 4),
            "std_cer": round(self.std_cer, 4),
            "total_chunks": self.total_chunks,
        }
    
    @classmethod
    def from_results(cls, results: List[ComparisonResult]) -> "MetricsSummary":
        """Calculate summary from list of comparison results."""
        if not results:
            return cls(
                avg_wer=0.0,
                avg_cer=0.0,
                avg_semantic_similarity=0.0,
                avg_hybrid_score=0.0,
            )
        
        import statistics
        
        wers = [r.wer for r in results]
        cers = [r.cer for r in results]
        sims = [r.semantic_similarity for r in results]
        hybrids = [r.hybrid_score for r in results if r.hybrid_score is not None]
        
        return cls(
            avg_wer=statistics.mean(wers),
            avg_cer=statistics.mean(cers),
            avg_semantic_similarity=statistics.mean(sims),
            avg_hybrid_score=statistics.mean(hybrids) if hybrids else 0.0,
            min_wer=min(wers),
            max_wer=max(wers),
            std_wer=statistics.stdev(wers) if len(wers) > 1 else 0.0,
            min_cer=min(cers),
            max_cer=max(cers),
            std_cer=statistics.stdev(cers) if len(cers) > 1 else 0.0,
            total_chunks=len(results),
        )


@dataclass
class PipelineReport:
    """Final output of the complete pipeline.
    
    Attributes:
        video_url: Original YouTube URL.
        video_title: Video title.
        video_duration: Total video duration in seconds.
        processed_at: Timestamp when processing completed.
        processing_time: Total pipeline time in seconds.
        model_used: Transcription model name.
        total_chunks: Number of chunks processed.
        results: List of per-chunk comparison results.
        summary: Aggregated metrics summary.
    """
    video_url: str
    video_title: str
    video_duration: float
    model_used: str
    total_chunks: int
    results: List[ComparisonResult]
    summary: MetricsSummary
    processed_at: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "video_url": self.video_url,
            "video_title": self.video_title,
            "video_duration": self.video_duration,
            "processed_at": self.processed_at.isoformat(),
            "processing_time": round(self.processing_time, 2),
            "model_used": self.model_used,
            "total_chunks": self.total_chunks,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary.to_dict(),
        }
    
    def save_json(self, path: str) -> None:
        """Save report to JSON file."""
        import json
        from pathlib import Path
        
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

