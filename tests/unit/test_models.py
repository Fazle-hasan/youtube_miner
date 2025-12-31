"""Unit tests for data models."""

import pytest
from pathlib import Path
from datetime import datetime

from src.models.audio import AudioFile, Chunk
from src.models.transcript import Transcript, Caption
from src.models.comparison import ComparisonResult, MetricsSummary


class TestAudioFile:
    """Tests for AudioFile model."""
    
    def test_create_audio_file(self, temp_dir):
        """Test creating an AudioFile."""
        path = temp_dir / "test.wav"
        path.touch()
        
        audio = AudioFile(
            path=path,
            format="wav",
            duration=60.0,
            sample_rate=16000,
            channels=1,
        )
        
        assert audio.path == path
        assert audio.format == "wav"
        assert audio.duration == 60.0
        assert audio.sample_rate == 16000
        assert audio.channels == 1
    
    def test_audio_file_exists(self, temp_dir):
        """Test exists property."""
        path = temp_dir / "test.wav"
        path.touch()
        
        audio = AudioFile(path=path, format="wav", duration=60.0)
        assert audio.exists is True
        
        path.unlink()
        assert audio.exists is False
    
    def test_audio_file_to_dict(self, sample_audio_file):
        """Test to_dict method."""
        data = sample_audio_file.to_dict()
        
        assert "path" in data
        assert "format" in data
        assert "duration" in data
        assert data["format"] == "wav"
    
    def test_path_string_conversion(self, temp_dir):
        """Test that string paths are converted to Path objects."""
        path_str = str(temp_dir / "test.wav")
        
        audio = AudioFile(path=path_str, format="wav", duration=60.0)
        
        assert isinstance(audio.path, Path)


class TestChunk:
    """Tests for Chunk model."""
    
    def test_create_chunk(self, temp_dir):
        """Test creating a Chunk."""
        path = temp_dir / "chunk.wav"
        path.touch()
        
        chunk = Chunk(
            index=0,
            audio_path=path,
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
        )
        
        assert chunk.index == 0
        assert chunk.duration == 30.0
        assert chunk.is_speech is True
    
    def test_chunk_to_dict(self, sample_chunk):
        """Test to_dict method."""
        data = sample_chunk.to_dict()
        
        assert data["index"] == 0
        assert data["duration"] == 30.0
        assert data["is_speech"] is True
    
    def test_chunk_from_dict(self, sample_chunk):
        """Test from_dict method."""
        data = sample_chunk.to_dict()
        restored = Chunk.from_dict(data)
        
        assert restored.index == sample_chunk.index
        assert restored.duration == sample_chunk.duration


class TestTranscript:
    """Tests for Transcript model."""
    
    def test_create_transcript(self):
        """Test creating a Transcript."""
        transcript = Transcript(
            text="Hello world",
            model_name="whisper-tiny",
            chunk_index=0,
            confidence=0.9,
        )
        
        assert transcript.text == "Hello world"
        assert transcript.model_name == "whisper-tiny"
        assert transcript.word_count == 2
        assert transcript.char_count == 11
    
    def test_transcript_word_count(self):
        """Test word_count property."""
        transcript = Transcript(
            text="one two three four five",
            model_name="test",
            chunk_index=0,
        )
        
        assert transcript.word_count == 5
    
    def test_transcript_deduplicated_flag(self):
        """Test deduplicated flag and raw_text."""
        transcript = Transcript(
            text="hello world",
            model_name="test",
            chunk_index=0,
            raw_text="hello hello world",
            deduplicated=True,
        )
        
        assert transcript.deduplicated is True
        assert transcript.raw_text == "hello hello world"
        assert transcript.text == "hello world"


class TestCaption:
    """Tests for Caption model."""
    
    def test_create_caption(self):
        """Test creating a Caption."""
        caption = Caption(
            text="Test caption",
            start_time=0.0,
            end_time=5.0,
            language="en",
        )
        
        assert caption.text == "Test caption"
        assert caption.duration == 5.0
    
    def test_caption_duration(self):
        """Test duration property."""
        caption = Caption(
            text="Test",
            start_time=10.0,
            end_time=25.0,
        )
        
        assert caption.duration == 15.0


class TestComparisonResult:
    """Tests for ComparisonResult model."""
    
    def test_create_comparison_result(self):
        """Test creating a ComparisonResult."""
        result = ComparisonResult(
            chunk_index=0,
            normalized_transcript="hello world",
            normalized_caption="hello world",
            wer=0.0,
            cer=0.0,
            semantic_similarity=1.0,
        )
        
        assert result.wer == 0.0
        assert result.semantic_similarity == 1.0
        assert result.hybrid_score is not None
    
    def test_hybrid_score_calculation(self):
        """Test automatic hybrid score calculation."""
        result = ComparisonResult(
            chunk_index=0,
            normalized_transcript="test",
            normalized_caption="test",
            wer=0.2,
            cer=0.1,
            semantic_similarity=0.9,
        )
        
        # hybrid = 0.5 * (1 - 0.2) + 0.5 * 0.9 = 0.4 + 0.45 = 0.85
        assert result.hybrid_score == pytest.approx(0.85, rel=0.01)


class TestMetricsSummary:
    """Tests for MetricsSummary model."""
    
    def test_from_results(self):
        """Test creating summary from results."""
        results = [
            ComparisonResult(0, "a", "a", 0.1, 0.05, 0.9),
            ComparisonResult(1, "b", "b", 0.2, 0.1, 0.8),
            ComparisonResult(2, "c", "c", 0.3, 0.15, 0.7),
        ]
        
        summary = MetricsSummary.from_results(results)
        
        assert summary.avg_wer == pytest.approx(0.2, rel=0.01)
        assert summary.min_wer == pytest.approx(0.1, rel=0.01)
        assert summary.max_wer == pytest.approx(0.3, rel=0.01)
        assert summary.total_chunks == 3
    
    def test_from_empty_results(self):
        """Test creating summary from empty results."""
        summary = MetricsSummary.from_results([])
        
        assert summary.avg_wer == 0.0
        assert summary.total_chunks == 0

