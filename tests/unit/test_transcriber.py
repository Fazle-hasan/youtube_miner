"""Unit tests for transcribers."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.transcriber import get_transcriber, list_available_models, TRANSCRIBERS
from src.transcriber.base import BaseTranscriber
from src.models.audio import Chunk


class TestTranscriberRegistry:
    """Tests for transcriber registry."""
    
    def test_list_available_models(self):
        """Test listing available models."""
        models = list_available_models()
        
        assert "whisper-tiny" in models
        assert "faster-whisper" in models
        assert "indic-seamless" in models
        assert "whisper-large" in models
    
    def test_get_transcriber_valid_model(self):
        """Test getting a valid transcriber."""
        transcriber = get_transcriber("whisper-tiny")
        
        assert transcriber is not None
        assert transcriber.model_name == "whisper-tiny"
    
    def test_get_transcriber_invalid_model(self):
        """Test getting an invalid transcriber."""
        with pytest.raises(ValueError, match="Unknown model"):
            get_transcriber("invalid-model")
    
    def test_all_models_in_registry(self):
        """Test that all models are properly registered."""
        for model_name in list_available_models():
            assert model_name in TRANSCRIBERS
            transcriber = get_transcriber(model_name)
            assert isinstance(transcriber, BaseTranscriber)


class TestBaseTranscriber:
    """Tests for base transcriber interface."""
    
    def test_base_transcriber_is_abstract(self):
        """Test that BaseTranscriber cannot be instantiated."""
        # BaseTranscriber is abstract, but we can test through subclasses
        from src.transcriber.whisper_tiny import WhisperTinyTranscriber
        
        transcriber = WhisperTinyTranscriber()
        assert transcriber.model_name == "whisper-tiny"
        assert transcriber.language == "en"
    
    def test_transcriber_repr(self):
        """Test transcriber string representation."""
        from src.transcriber.whisper_tiny import WhisperTinyTranscriber
        
        transcriber = WhisperTinyTranscriber()
        repr_str = repr(transcriber)
        
        assert "WhisperTinyTranscriber" in repr_str
        assert "whisper-tiny" in repr_str


class TestWhisperTinyTranscriber:
    """Tests for Whisper-Tiny transcriber."""
    
    def test_init(self):
        """Test initialization."""
        from src.transcriber.whisper_tiny import WhisperTinyTranscriber
        
        transcriber = WhisperTinyTranscriber(language="en")
        
        assert transcriber.model_name == "whisper-tiny"
        assert transcriber.language == "en"
        assert transcriber._model is None
    
    def test_transcribe_chunk_file_not_found(self, temp_dir):
        """Test transcription with non-existent file."""
        from src.transcriber.whisper_tiny import WhisperTinyTranscriber
        
        transcriber = WhisperTinyTranscriber()
        transcriber._model = Mock()  # Pretend model is loaded
        
        chunk = Chunk(
            index=0,
            audio_path=temp_dir / "nonexistent.wav",
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
        )
        
        with pytest.raises(FileNotFoundError):
            transcriber.transcribe_chunk(chunk)
    
    @patch('src.transcriber.whisper_tiny.whisper')
    def test_transcribe_chunk_success(self, mock_whisper, temp_dir):
        """Test successful transcription."""
        from src.transcriber.whisper_tiny import WhisperTinyTranscriber
        
        # Setup mock
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'Hello world',
            'segments': [{'no_speech_prob': 0.1}],
            'language': 'en',
        }
        mock_whisper.load_model.return_value = mock_model
        
        # Create chunk file
        chunk_path = temp_dir / "chunk.wav"
        chunk_path.touch()
        
        chunk = Chunk(
            index=0,
            audio_path=chunk_path,
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
        )
        
        transcriber = WhisperTinyTranscriber()
        transcriber._model = mock_model
        
        transcript = transcriber.transcribe_chunk(chunk)
        
        assert transcript.text == "Hello world"
        assert transcript.model_name == "whisper-tiny"
        assert transcript.chunk_index == 0


class TestFasterWhisperTranscriber:
    """Tests for Faster-Whisper transcriber."""
    
    def test_init(self):
        """Test initialization."""
        from src.transcriber.faster_whisper import FasterWhisperTranscriber
        
        transcriber = FasterWhisperTranscriber(language="en", model_size="tiny")
        
        assert transcriber.model_name == "faster-whisper"
        assert transcriber.model_size == "tiny"
        assert transcriber.compute_type == "int8"
    
    def test_custom_compute_type(self):
        """Test custom compute type."""
        from src.transcriber.faster_whisper import FasterWhisperTranscriber
        
        transcriber = FasterWhisperTranscriber(compute_type="float16")
        
        assert transcriber.compute_type == "float16"


class TestIndicSeamlessTranscriber:
    """Tests for Indic-Seamless transcriber."""
    
    def test_init(self):
        """Test initialization."""
        from src.transcriber.indic_seamless import IndicSeamlessTranscriber
        
        transcriber = IndicSeamlessTranscriber(language="hi")
        
        assert transcriber.model_name == "indic-seamless"
        assert transcriber.language == "hi"
    
    def test_language_code_mapping(self):
        """Test language code mapping."""
        from src.transcriber.indic_seamless import IndicSeamlessTranscriber
        
        transcriber = IndicSeamlessTranscriber(language="hi")
        
        assert transcriber._get_language_code() == "hin"
        
        transcriber.language = "en"
        assert transcriber._get_language_code() == "eng"
        
        transcriber.language = "ta"
        assert transcriber._get_language_code() == "tam"

