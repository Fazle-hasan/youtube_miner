"""Configuration management."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class Config:
    """Pipeline configuration.
    
    Can be loaded from YAML file or created programmatically.
    
    Example:
        >>> config = Config.from_yaml("config.yaml")
        >>> print(config.default_model)
    """
    
    # Model settings
    default_model: str = "faster-whisper"
    language: str = "en"
    
    # Chunking settings
    chunk_duration: float = 30.0
    min_speech_duration: float = 0.5
    vad_threshold: float = 0.5
    
    # Comparison settings
    normalize_text: bool = True
    hybrid_alpha: float = 0.5
    
    # Output settings
    output_format: str = "json"
    output_dir: str = "./output"
    
    # Processing settings
    verbose: bool = False
    
    # Metrics to compute
    comparison_metrics: List[str] = field(
        default_factory=lambda: ["wer", "cer", "semantic_similarity", "hybrid_score"]
    )
    
    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file.
        
        Args:
            path: Path to YAML configuration file.
            
        Returns:
            Config instance.
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
    
    def to_yaml(self, path: str) -> None:
        """Save configuration to YAML file.
        
        Args:
            path: Output path for YAML file.
        """
        data = {
            "default_model": self.default_model,
            "language": self.language,
            "chunk_duration": self.chunk_duration,
            "min_speech_duration": self.min_speech_duration,
            "vad_threshold": self.vad_threshold,
            "normalize_text": self.normalize_text,
            "hybrid_alpha": self.hybrid_alpha,
            "output_format": self.output_format,
            "output_dir": self.output_dir,
            "verbose": self.verbose,
            "comparison_metrics": self.comparison_metrics,
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "default_model": self.default_model,
            "language": self.language,
            "chunk_duration": self.chunk_duration,
            "min_speech_duration": self.min_speech_duration,
            "vad_threshold": self.vad_threshold,
            "normalize_text": self.normalize_text,
            "hybrid_alpha": self.hybrid_alpha,
            "output_format": self.output_format,
            "output_dir": self.output_dir,
            "verbose": self.verbose,
            "comparison_metrics": self.comparison_metrics,
        }

