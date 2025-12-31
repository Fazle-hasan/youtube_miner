"""Multi-model transcription module."""

from typing import Dict, Type

from src.transcriber.base import BaseTranscriber
from src.transcriber.whisper_tiny import WhisperTinyTranscriber
from src.transcriber.faster_whisper import FasterWhisperTranscriber
from src.transcriber.indic_seamless import IndicSeamlessTranscriber
from src.transcriber.whisper_large import WhisperLargeTranscriber

# Registry of available transcribers
TRANSCRIBERS: Dict[str, Type[BaseTranscriber]] = {
    "whisper-tiny": WhisperTinyTranscriber,
    "faster-whisper": FasterWhisperTranscriber,
    "indic-seamless": IndicSeamlessTranscriber,
    "whisper-large": WhisperLargeTranscriber,
}


def get_transcriber(model_name: str, **kwargs) -> BaseTranscriber:
    """Get a transcriber instance by model name.
    
    Args:
        model_name: Name of the model ('whisper-tiny', 'faster-whisper', etc.).
        **kwargs: Additional arguments to pass to the transcriber.
        
    Returns:
        Transcriber instance.
        
    Raises:
        ValueError: If model name is not recognized.
    """
    if model_name not in TRANSCRIBERS:
        available = ", ".join(TRANSCRIBERS.keys())
        raise ValueError(f"Unknown model: {model_name}. Available: {available}")
    
    return TRANSCRIBERS[model_name](**kwargs)


def list_available_models() -> list:
    """List all available transcription models.
    
    Returns:
        List of model names.
    """
    return list(TRANSCRIBERS.keys())


__all__ = [
    "BaseTranscriber",
    "WhisperTinyTranscriber",
    "FasterWhisperTranscriber",
    "IndicSeamlessTranscriber",
    "WhisperLargeTranscriber",
    "get_transcriber",
    "list_available_models",
    "TRANSCRIBERS",
]

