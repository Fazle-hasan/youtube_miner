"""Whisper-Tiny transcriber using OpenAI Whisper."""

import logging
import ssl
import time
import urllib.request
from typing import Optional

import certifi
import whisper

from src.models.audio import Chunk
from src.models.transcript import Transcript
from src.transcriber.base import BaseTranscriber

logger = logging.getLogger(__name__)


def _setup_ssl_context():
    """Setup SSL context with certifi certificates for model downloads."""
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    https_handler = urllib.request.HTTPSHandler(context=ssl_context)
    opener = urllib.request.build_opener(https_handler)
    urllib.request.install_opener(opener)


class WhisperTinyTranscriber(BaseTranscriber):
    """Transcriber using OpenAI Whisper-Tiny model.
    
    Whisper-Tiny is the smallest and fastest Whisper model,
    suitable for quick transcriptions with moderate accuracy.
    
    Model size: ~39M parameters
    Memory: ~1GB
    Speed: Fastest Whisper variant
    
    Example:
        >>> transcriber = WhisperTinyTranscriber()
        >>> transcript = transcriber.transcribe_chunk(chunk)
        >>> print(transcript.text)
    """
    
    def __init__(self, language: str = "en", device: Optional[str] = None):
        """Initialize Whisper-Tiny transcriber.
        
        Args:
            language: Target language for transcription.
            device: Device to use ('cuda', 'cpu', or None for auto).
        """
        super().__init__(model_name="whisper-tiny", language=language)
        self.device = device
    
    def load_model(self) -> None:
        """Load Whisper-Tiny model."""
        logger.info("Loading Whisper-Tiny model...")
        
        # Setup SSL context for model download (fixes macOS certificate issues)
        _setup_ssl_context()
        
        self._model = whisper.load_model("tiny", device=self.device)
        
        logger.info("Whisper-Tiny model loaded successfully")
    
    def transcribe_chunk(self, chunk: Chunk) -> Transcript:
        """Transcribe audio chunk using Whisper-Tiny.
        
        Args:
            chunk: Audio chunk to transcribe.
            
        Returns:
            Transcript object with transcription results.
        """
        if self._model is None:
            self.load_model()
        
        if not chunk.exists:
            raise FileNotFoundError(f"Chunk file not found: {chunk.audio_path}")
        
        start_time = time.time()
        
        # Handle "auto" language - pass None for auto-detection
        transcribe_language = None if self.language == "auto" else self.language
        
        # Transcribe
        result = self._model.transcribe(
            str(chunk.audio_path),
            language=transcribe_language,
            task="transcribe",
        )
        
        processing_time = time.time() - start_time
        
        # Extract text and confidence
        text = result.get("text", "").strip()
        
        # Calculate average confidence from segments
        segments = result.get("segments", [])
        if segments:
            avg_confidence = sum(
                seg.get("no_speech_prob", 0) for seg in segments
            ) / len(segments)
            confidence = 1.0 - avg_confidence  # Convert no_speech_prob to confidence
        else:
            confidence = 0.0
        
        logger.debug(
            f"Transcribed chunk {chunk.index}: {len(text)} chars in {processing_time:.2f}s"
        )
        
        return Transcript(
            text=text,
            model_name=self.model_name,
            chunk_index=chunk.index,
            confidence=confidence,
            language=result.get("language", self.language),
            processing_time=processing_time,
        )

