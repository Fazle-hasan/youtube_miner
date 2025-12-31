"""Unit tests for audio converter."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.converter.audio import AudioConverter
from src.models.audio import AudioFile


class TestAudioConverter:
    """Tests for AudioConverter."""
    
    def test_init_default_settings(self):
        """Test default initialization settings."""
        converter = AudioConverter()
        
        assert converter.sample_rate == 16000
        assert converter.channels == 1
    
    def test_init_custom_settings(self):
        """Test custom initialization settings."""
        converter = AudioConverter(sample_rate=22050, channels=2)
        
        assert converter.sample_rate == 22050
        assert converter.channels == 2
    
    def test_convert_file_not_found(self, temp_dir):
        """Test conversion with non-existent file."""
        converter = AudioConverter()
        
        audio_file = AudioFile(
            path=temp_dir / "nonexistent.wav",
            format="wav",
            duration=60.0,
        )
        
        with pytest.raises(FileNotFoundError):
            converter.convert(audio_file)
    
    @patch('src.converter.audio.AudioSegment')
    def test_convert_already_correct_format(self, mock_audio_segment, temp_dir):
        """Test that correctly formatted file is not reconverted."""
        # Create a file
        wav_path = temp_dir / "test.wav"
        wav_path.touch()
        
        audio_file = AudioFile(
            path=wav_path,
            format="wav",
            duration=60.0,
            sample_rate=16000,
            channels=1,
        )
        
        converter = AudioConverter()
        result = converter.convert(audio_file)
        
        # Should return same file without conversion
        assert result.path == wav_path
        mock_audio_segment.from_file.assert_not_called()
    
    @patch('src.converter.audio.AudioSegment')
    def test_convert_from_path(self, mock_audio_segment, temp_dir):
        """Test convert_from_path method."""
        # Setup mock
        mock_audio = MagicMock()
        mock_audio.channels = 2
        mock_audio.frame_rate = 44100
        mock_audio.__len__ = Mock(return_value=60000)  # 60 seconds in ms
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio_segment.from_file.return_value = mock_audio
        
        # Create input file
        input_path = temp_dir / "test.m4a"
        input_path.touch()
        
        converter = AudioConverter()
        
        # Call convert_from_path - the mock should make this work
        result = converter.convert_from_path(str(input_path))
        
        # Verify the result
        assert result is not None
        assert result.format == "wav"
    
    @patch('src.converter.audio.AudioSegment')
    def test_get_audio_info(self, mock_audio_segment, temp_dir):
        """Test get_audio_info static method."""
        mock_audio = MagicMock()
        mock_audio.frame_rate = 44100
        mock_audio.channels = 2
        mock_audio.sample_width = 2
        mock_audio.__len__ = Mock(return_value=60000)
        mock_audio.get_array_of_samples.return_value = [0] * 1000
        mock_audio_segment.from_file.return_value = mock_audio
        
        info = AudioConverter.get_audio_info("test.wav")
        
        assert info["sample_rate"] == 44100
        assert info["channels"] == 2
        assert info["duration"] == 60.0

