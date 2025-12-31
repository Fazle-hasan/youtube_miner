"""Faster-Whisper transcriber using CTranslate2 optimization."""

import logging
import ssl
import time
import urllib.request
from typing import Optional

import certifi
from faster_whisper import WhisperModel

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


class FasterWhisperTranscriber(BaseTranscriber):
    """Transcriber using Faster-Whisper (CTranslate2 optimized).
    
    Faster-Whisper provides 4x faster inference than OpenAI Whisper
    with the same accuracy, using CTranslate2 optimization.
    
    Memory: ~2GB (with int8 quantization)
    Speed: 4x faster than original Whisper
    
    Example:
        >>> transcriber = FasterWhisperTranscriber()
        >>> transcript = transcriber.transcribe_chunk(chunk)
        >>> print(transcript.text)
    """
    
    def __init__(
        self,
        language: str = "en",
        model_size: str = "tiny",
        device: str = "auto",
        compute_type: str = "int8",
    ):
        """Initialize Faster-Whisper transcriber.
        
        Args:
            language: Target language for transcription.
            model_size: Model size ('tiny', 'base', 'small', 'medium', 'large-v2').
            device: Device to use ('cuda', 'cpu', or 'auto').
            compute_type: Compute type ('int8', 'float16', 'float32').
        """
        super().__init__(model_name="faster-whisper", language=language)
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
    
    def load_model(self) -> None:
        """Load Faster-Whisper model."""
        logger.info(f"Loading Faster-Whisper ({self.model_size}) model...")
        
        # Setup SSL context for model download (fixes macOS certificate issues)
        _setup_ssl_context()
        
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        
        logger.info("Faster-Whisper model loaded successfully")
    
    def transcribe_chunk(self, chunk: Chunk) -> Transcript:
        """Transcribe audio chunk using Faster-Whisper.
        
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
        segments, info = self._model.transcribe(
            str(chunk.audio_path),
            language=transcribe_language,
            task="transcribe",
            beam_size=5,
            vad_filter=True,  # Use VAD to filter out non-speech
        )
        
        # Collect text from all segments
        text_parts = []
        total_confidence = 0.0
        segment_count = 0
        
        for segment in segments:
            text_parts.append(segment.text.strip())
            total_confidence += segment.avg_logprob
            segment_count += 1
        
        text = " ".join(text_parts)
        processing_time = time.time() - start_time
        
        # Convert log probability to confidence
        if segment_count > 0:
            avg_logprob = total_confidence / segment_count
            # Log prob is typically negative, convert to 0-1 range
            confidence = min(1.0, max(0.0, 1.0 + avg_logprob / 5))
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
            language=info.language if info else self.language,
            processing_time=processing_time,
        )

