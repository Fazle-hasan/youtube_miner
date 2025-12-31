"""Base transcriber interface."""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from src.models.audio import Chunk
from src.models.transcript import Transcript

logger = logging.getLogger(__name__)


class BaseTranscriber(ABC):
    """Abstract base class for all transcription models.
    
    All transcriber implementations must inherit from this class
    and implement the `transcribe_chunk` method.
    """
    
    def __init__(self, model_name: str, language: str = "en"):
        """Initialize the transcriber.
        
        Args:
            model_name: Name identifier for this model.
            language: Target language for transcription.
        """
        self.model_name = model_name
        self.language = language
        self._model = None
    
    @abstractmethod
    def load_model(self) -> None:
        """Load the transcription model into memory.
        
        This method should be called before transcription.
        """
        pass
    
    @abstractmethod
    def transcribe_chunk(self, chunk: Chunk) -> Transcript:
        """Transcribe a single audio chunk.
        
        Args:
            chunk: Audio chunk to transcribe.
            
        Returns:
            Transcript object with transcription results.
        """
        pass
    
    def transcribe_chunks(self, chunks: List[Chunk]) -> List[Transcript]:
        """Transcribe multiple audio chunks.
        
        Args:
            chunks: List of audio chunks to transcribe.
            
        Returns:
            List of Transcript objects.
        """
        # Ensure model is loaded
        if self._model is None:
            self.load_model()
        
        transcripts = []
        total = len(chunks)
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Transcribing chunk {i + 1}/{total} with {self.model_name}")
            transcript = self.transcribe_chunk(chunk)
            transcripts.append(transcript)
        
        return transcripts
    
    def transcribe_file(self, audio_path: str) -> Transcript:
        """Transcribe a single audio file.
        
        Args:
            audio_path: Path to audio file.
            
        Returns:
            Transcript object.
        """
        # Ensure model is loaded
        if self._model is None:
            self.load_model()
        
        # Create a temporary chunk
        chunk = Chunk(
            index=0,
            audio_path=Path(audio_path),
            start_time=0.0,
            end_time=0.0,
            duration=0.0,
        )
        
        return self.transcribe_chunk(chunk)
    
    def unload_model(self) -> None:
        """Unload the model from memory.
        
        Useful for freeing memory when switching between models.
        """
        self._model = None
        logger.info(f"Unloaded {self.model_name} model")
    
    def _measure_time(self, func):
        """Decorator to measure transcription time.
        
        Args:
            func: Function to wrap.
            
        Returns:
            Wrapper function.
        """
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            return result, elapsed
        return wrapper
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model_name='{self.model_name}')"

