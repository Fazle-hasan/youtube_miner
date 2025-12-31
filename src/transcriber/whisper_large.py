"""Whisper-Large transcriber for highest accuracy."""

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


class WhisperLargeTranscriber(BaseTranscriber):
    """Transcriber using OpenAI Whisper-Large model.
    
    Whisper-Large is the most accurate Whisper model,
    suitable when quality is more important than speed.
    
    Model size: ~1.5B parameters
    Memory: ~6GB
    Speed: Slowest but most accurate
    
    Example:
        >>> transcriber = WhisperLargeTranscriber()
        >>> transcript = transcriber.transcribe_chunk(chunk)
        >>> print(transcript.text)
    """
    
    def __init__(
        self,
        language: str = "en",
        device: Optional[str] = None,
        model_version: str = "large-v2",
    ):
        """Initialize Whisper-Large transcriber.
        
        Args:
            language: Target language for transcription.
            device: Device to use ('cuda', 'cpu', or None for auto).
            model_version: Model version ('large', 'large-v2', 'large-v3').
        """
        super().__init__(model_name="whisper-large", language=language)
        self.device = device
        self.model_version = model_version
    
    def load_model(self) -> None:
        """Load Whisper-Large model."""
        logger.info(f"Loading Whisper {self.model_version} model...")
        logger.warning("This may take a while and requires ~6GB memory")
        
        # Setup SSL context for model download (fixes macOS certificate issues)
        _setup_ssl_context()
        
        self._model = whisper.load_model(self.model_version, device=self.device)
        
        logger.info("Whisper-Large model loaded successfully")
    
    def transcribe_chunk(self, chunk: Chunk) -> Transcript:
        """Transcribe audio chunk using Whisper-Large.
        
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
        
        # Transcribe with higher quality settings
        result = self._model.transcribe(
            str(chunk.audio_path),
            language=transcribe_language,
            task="transcribe",
            best_of=5,  # More candidates for better quality
            beam_size=5,
            temperature=0.0,  # Greedy decoding for consistency
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
            confidence = 1.0 - avg_confidence
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

