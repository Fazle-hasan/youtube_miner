"""Audio-related data models."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class AudioFile:
    """Represents a downloaded or processed audio file.
    
    Attributes:
        path: File system path to the audio file.
        format: Audio format ('wav', 'm4a', 'webm', etc.).
        duration: Duration in seconds.
        sample_rate: Sample rate in Hz (target: 16000).
        channels: Number of audio channels (target: 1 for mono).
        source_url: Original YouTube URL if applicable.
        created_at: Timestamp when file was created/downloaded.
    """
    path: Path
    format: str
    duration: float
    sample_rate: int = 16000
    channels: int = 1
    source_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Ensure path is a Path object."""
        if isinstance(self.path, str):
            self.path = Path(self.path)
    
    @property
    def exists(self) -> bool:
        """Check if the audio file exists on disk."""
        return self.path.exists()
    
    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        if self.exists:
            return self.path.stat().st_size / (1024 * 1024)
        return 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "format": self.format,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Chunk:
    """Represents a speech segment extracted via VAD.
    
    Attributes:
        index: Chunk number (0-indexed).
        audio_path: Path to the chunk WAV file.
        start_time: Start time in original audio (seconds).
        end_time: End time in original audio (seconds).
        duration: Actual chunk duration in seconds.
        is_speech: Whether this chunk is confirmed as speech by VAD.
        confidence: VAD confidence score (0-1).
        parent_audio_path: Path to the source audio file.
    """
    index: int
    audio_path: Path
    start_time: float
    end_time: float
    duration: float
    is_speech: bool = True
    confidence: float = 1.0
    parent_audio_path: Optional[Path] = None
    
    def __post_init__(self) -> None:
        """Ensure paths are Path objects."""
        if isinstance(self.audio_path, str):
            self.audio_path = Path(self.audio_path)
        if isinstance(self.parent_audio_path, str):
            self.parent_audio_path = Path(self.parent_audio_path)
    
    @property
    def exists(self) -> bool:
        """Check if the chunk file exists on disk."""
        return self.audio_path.exists()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "index": self.index,
            "audio_path": str(self.audio_path),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "is_speech": self.is_speech,
            "confidence": self.confidence,
            "parent_audio_path": str(self.parent_audio_path) if self.parent_audio_path else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        """Create Chunk from dictionary."""
        return cls(
            index=data["index"],
            audio_path=Path(data["audio_path"]),
            start_time=data["start_time"],
            end_time=data["end_time"],
            duration=data["duration"],
            is_speech=data.get("is_speech", True),
            confidence=data.get("confidence", 1.0),
            parent_audio_path=Path(data["parent_audio_path"]) if data.get("parent_audio_path") else None,
        )

