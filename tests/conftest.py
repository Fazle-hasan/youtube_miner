"""Shared test fixtures for YouTube Miner tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from src.models.audio import AudioFile, Chunk
from src.models.transcript import Transcript, Caption
from src.models.comparison import ComparisonResult


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_file(temp_dir: Path) -> AudioFile:
    """Create a sample AudioFile for testing."""
    audio_path = temp_dir / "test_audio.wav"
    # Create an empty file (actual audio tests will need real files)
    audio_path.touch()
    
    return AudioFile(
        path=audio_path,
        format="wav",
        duration=60.0,
        sample_rate=16000,
        channels=1,
        source_url="https://youtube.com/watch?v=test123",
    )


@pytest.fixture
def sample_chunk(temp_dir: Path) -> Chunk:
    """Create a sample Chunk for testing."""
    chunk_path = temp_dir / "chunk_000.wav"
    chunk_path.touch()
    
    return Chunk(
        index=0,
        audio_path=chunk_path,
        start_time=0.0,
        end_time=30.0,
        duration=30.0,
        is_speech=True,
        confidence=0.95,
    )


@pytest.fixture
def sample_chunks(temp_dir: Path) -> list:
    """Create multiple sample Chunks for testing."""
    chunks = []
    for i in range(3):
        chunk_path = temp_dir / f"chunk_{i:03d}.wav"
        chunk_path.touch()
        
        chunks.append(Chunk(
            index=i,
            audio_path=chunk_path,
            start_time=i * 30.0,
            end_time=(i + 1) * 30.0,
            duration=30.0,
            is_speech=True,
            confidence=0.95,
        ))
    
    return chunks


@pytest.fixture
def sample_transcript() -> Transcript:
    """Create a sample Transcript for testing."""
    return Transcript(
        text="Hello world this is a test transcription",
        model_name="whisper-tiny",
        chunk_index=0,
        confidence=0.87,
        language="en",
        processing_time=2.5,
    )


@pytest.fixture
def sample_caption() -> Caption:
    """Create a sample Caption for testing."""
    return Caption(
        text="Hello world this is a test caption",
        start_time=0.0,
        end_time=30.0,
        language="en",
        source="auto",
        video_url="https://youtube.com/watch?v=test123",
    )


@pytest.fixture
def sample_comparison_result() -> ComparisonResult:
    """Create a sample ComparisonResult for testing."""
    return ComparisonResult(
        chunk_index=0,
        normalized_transcript="hello world this is a test",
        normalized_caption="hello world this is a test",
        wer=0.1,
        cer=0.05,
        semantic_similarity=0.95,
        hybrid_score=0.925,
    )


# Skip tests that require network/large models
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "network: marks tests that require network access"
    )

