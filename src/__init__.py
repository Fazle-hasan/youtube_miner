"""
YouTube Miner - A data pipeline for YouTube audio processing and transcription comparison.

This package provides tools for:
- Downloading audio from YouTube videos
- Converting audio to WAV format (16kHz, mono)
- Applying Voice Activity Detection to create clean speech chunks
- Transcribing audio using multiple open-source models
- Comparing transcriptions with YouTube auto-captions
"""

__version__ = "1.0.0"
__author__ = "YouTube Miner Team"

from src.pipeline.orchestrator import YouTubeMinerPipeline

__all__ = ["YouTubeMinerPipeline", "__version__"]

