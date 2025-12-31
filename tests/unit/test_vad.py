"""Unit tests for VAD chunker."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import torch

from src.vad.chunker import VADChunker
from src.models.audio import AudioFile


class TestVADChunker:
    """Tests for VADChunker."""
    
    def test_init_creates_output_dir(self, temp_dir):
        """Test that initialization creates output directory."""
        with patch.object(VADChunker, '_load_vad_model', return_value=(Mock(), [])):
            output_path = temp_dir / "chunks"
            
            chunker = VADChunker(output_dir=str(output_path))
            
            assert output_path.exists()
    
    def test_init_default_settings(self, temp_dir):
        """Test default initialization settings."""
        with patch.object(VADChunker, '_load_vad_model', return_value=(Mock(), [])):
            chunker = VADChunker(output_dir=str(temp_dir))
            
            assert chunker.chunk_duration == 30.0
            assert chunker.min_speech_duration == 0.5
            assert chunker.threshold == 0.5
    
    def test_init_custom_settings(self, temp_dir):
        """Test custom initialization settings."""
        with patch.object(VADChunker, '_load_vad_model', return_value=(Mock(), [])):
            chunker = VADChunker(
                output_dir=str(temp_dir),
                chunk_duration=60.0,
                threshold=0.7,
            )
            
            assert chunker.chunk_duration == 60.0
            assert chunker.threshold == 0.7
    
    def test_chunk_file_not_found(self, temp_dir):
        """Test chunking with non-existent file."""
        with patch.object(VADChunker, '_load_vad_model', return_value=(Mock(), [])):
            chunker = VADChunker(output_dir=str(temp_dir))
            
            audio_file = AudioFile(
                path=temp_dir / "nonexistent.wav",
                format="wav",
                duration=60.0,
            )
            
            with pytest.raises(FileNotFoundError):
                chunker.chunk(audio_file)
    
    @patch('src.vad.chunker.torchaudio')
    @patch('src.vad.chunker.torch.hub')
    def test_detect_speech_segments(self, mock_hub, mock_torchaudio, temp_dir):
        """Test speech segment detection."""
        # Setup mocks
        mock_model = Mock()
        mock_get_timestamps = Mock(return_value=[
            {'start': 0, 'end': 16000},  # 0-1 second
            {'start': 32000, 'end': 64000},  # 2-4 seconds
        ])
        mock_hub.load.return_value = (mock_model, [mock_get_timestamps])
        
        mock_waveform = torch.zeros(1, 160000)  # 10 seconds at 16kHz
        mock_torchaudio.load.return_value = (mock_waveform, 16000)
        
        # Create file
        audio_path = temp_dir / "test.wav"
        audio_path.touch()
        
        chunker = VADChunker(output_dir=str(temp_dir))
        segments = chunker.detect_speech_segments(audio_path)
        
        assert len(segments) == 2
        assert segments[0] == (0.0, 1.0)
        assert segments[1] == (2.0, 4.0)


class TestChunkCreation:
    """Tests for chunk creation logic."""
    
    @patch.object(VADChunker, '_load_vad_model', return_value=(Mock(), []))
    def test_create_chunks_empty_segments(self, mock_load, temp_dir):
        """Test chunk creation with no segments."""
        chunker = VADChunker(output_dir=str(temp_dir))
        
        waveform = torch.zeros(1, 16000)
        chunks = chunker._create_chunks(waveform, [], Path("test.wav"))
        
        assert chunks == []
    
    @patch.object(VADChunker, '_load_vad_model', return_value=(Mock(), []))
    @patch('src.vad.chunker.torchaudio.save')
    def test_create_chunks_single_segment(self, mock_save, mock_load, temp_dir):
        """Test chunk creation with single segment."""
        chunker = VADChunker(output_dir=str(temp_dir))
        
        # 60 seconds of audio at 16kHz
        waveform = torch.zeros(1, 960000)
        segments = [(0.0, 30.0)]  # One 30-second segment
        
        chunks = chunker._create_chunks(waveform, segments, Path("test.wav"))
        
        assert len(chunks) == 1
        assert chunks[0].index == 0
        assert chunks[0].duration <= 30.0

