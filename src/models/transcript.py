"""Transcript and caption data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Transcript:
    """Represents transcription output from a model.
    
    Attributes:
        text: Transcribed text (after deduplication if applied).
        model_name: Name of the model used ('whisper-tiny', 'faster-whisper', etc.).
        chunk_index: Index of the associated chunk.
        confidence: Model confidence score (0-1).
        language: Detected language code.
        processing_time: Time taken to transcribe in seconds.
        raw_text: Original text before n-gram deduplication.
        deduplicated: Whether n-gram deduplication was applied.
    """
    text: str
    model_name: str
    chunk_index: int
    confidence: float = 0.0
    language: Optional[str] = None
    processing_time: float = 0.0
    raw_text: Optional[str] = None
    deduplicated: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Set raw_text to text if not provided."""
        if self.raw_text is None:
            self.raw_text = self.text
    
    @property
    def word_count(self) -> int:
        """Get the number of words in the transcript."""
        return len(self.text.split())
    
    @property
    def char_count(self) -> int:
        """Get the number of characters in the transcript."""
        return len(self.text)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "model_name": self.model_name,
            "chunk_index": self.chunk_index,
            "confidence": self.confidence,
            "language": self.language,
            "processing_time": self.processing_time,
            "raw_text": self.raw_text,
            "deduplicated": self.deduplicated,
            "word_count": self.word_count,
            "char_count": self.char_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Transcript":
        """Create Transcript from dictionary."""
        return cls(
            text=data["text"],
            model_name=data["model_name"],
            chunk_index=data["chunk_index"],
            confidence=data.get("confidence", 0.0),
            language=data.get("language"),
            processing_time=data.get("processing_time", 0.0),
            raw_text=data.get("raw_text"),
            deduplicated=data.get("deduplicated", False),
        )


@dataclass
class Caption:
    """Represents YouTube auto-generated caption.
    
    Attributes:
        text: Caption text.
        start_time: Start time in video (seconds).
        end_time: End time in video (seconds).
        language: Caption language code.
        source: Caption source ('auto', 'manual', 'translated').
        video_url: Source YouTube URL.
    """
    text: str
    start_time: float
    end_time: float
    language: str = "en"
    source: str = "auto"
    video_url: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Get caption duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def word_count(self) -> int:
        """Get the number of words in the caption."""
        return len(self.text.split())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "language": self.language,
            "source": self.source,
            "video_url": self.video_url,
            "duration": self.duration,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Caption":
        """Create Caption from dictionary."""
        return cls(
            text=data["text"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            language=data.get("language", "en"),
            source=data.get("source", "auto"),
            video_url=data.get("video_url"),
        )

