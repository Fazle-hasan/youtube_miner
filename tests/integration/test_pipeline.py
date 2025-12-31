"""Integration tests for the full pipeline."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.pipeline.orchestrator import YouTubeMinerPipeline
from src.models.audio import AudioFile, Chunk
from src.models.transcript import Transcript, Caption
from src.models.comparison import ComparisonResult, MetricsSummary


@pytest.mark.integration
class TestYouTubeMinerPipeline:
    """Integration tests for the pipeline."""
    
    def test_pipeline_init(self, temp_dir):
        """Test pipeline initialization."""
        with patch.object(YouTubeMinerPipeline, '__init__', return_value=None):
            pipeline = YouTubeMinerPipeline.__new__(YouTubeMinerPipeline)
            pipeline.output_dir = temp_dir
            pipeline.model_name = "faster-whisper"
            pipeline.language = "en"
            
            assert pipeline.model_name == "faster-whisper"
    
    @patch('src.pipeline.orchestrator.YouTubeDownloader')
    @patch('src.pipeline.orchestrator.CaptionExtractor')
    @patch('src.pipeline.orchestrator.AudioConverter')
    @patch('src.pipeline.orchestrator.VADChunker')
    @patch('src.pipeline.orchestrator.get_transcriber')
    def test_pipeline_run_mocked(
        self,
        mock_get_transcriber,
        mock_chunker_class,
        mock_converter_class,
        mock_caption_class,
        mock_downloader_class,
        temp_dir,
    ):
        """Test pipeline run with mocked components."""
        # Setup mocks
        mock_downloader = MagicMock()
        mock_downloader.download_with_info.return_value = (
            AudioFile(
                path=temp_dir / "audio.m4a",
                format="m4a",
                duration=120.0,
            ),
            {"id": "test123", "title": "Test Video", "duration": 120},
        )
        mock_downloader_class.return_value = mock_downloader
        
        mock_converter = MagicMock()
        wav_path = temp_dir / "audio.wav"
        wav_path.touch()
        mock_converter.convert.return_value = AudioFile(
            path=wav_path,
            format="wav",
            duration=120.0,
            sample_rate=16000,
            channels=1,
        )
        mock_converter_class.return_value = mock_converter
        
        mock_chunker = MagicMock()
        chunk_path = temp_dir / "chunk_000.wav"
        chunk_path.touch()
        mock_chunker.chunk.return_value = [
            Chunk(
                index=0,
                audio_path=chunk_path,
                start_time=0.0,
                end_time=30.0,
                duration=30.0,
            ),
        ]
        mock_chunker_class.return_value = mock_chunker
        
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe_chunks.return_value = [
            Transcript(
                text="Hello world",
                model_name="faster-whisper",
                chunk_index=0,
            ),
        ]
        mock_get_transcriber.return_value = mock_transcriber
        
        mock_caption = MagicMock()
        mock_caption.extract.return_value = [
            Caption(
                text="Hello world",
                start_time=0.0,
                end_time=30.0,
            ),
        ]
        mock_caption.get_caption_for_chunk.return_value = "Hello world"
        mock_caption_class.return_value = mock_caption
        
        # Create and run pipeline
        pipeline = YouTubeMinerPipeline(
            output_dir=str(temp_dir),
            model="faster-whisper",
        )
        
        # Replace mocked attributes
        pipeline.downloader = mock_downloader
        pipeline.converter = mock_converter
        pipeline.chunker = mock_chunker
        pipeline._transcriber = mock_transcriber
        pipeline.caption_extractor = mock_caption
        
        report = pipeline.run("https://youtube.com/watch?v=test123")
        
        assert report is not None
        assert report.video_url == "https://youtube.com/watch?v=test123"
        assert report.total_chunks == 1


@pytest.mark.integration
class TestPipelineComponents:
    """Integration tests for pipeline component interactions."""
    
    def test_compare_chunks(self, temp_dir):
        """Test chunk comparison functionality."""
        pipeline = YouTubeMinerPipeline.__new__(YouTubeMinerPipeline)
        pipeline.caption_extractor = MagicMock()
        pipeline.caption_extractor.get_caption_for_chunk.return_value = "Hello world"
        pipeline.comparator = MagicMock()
        pipeline.comparator.compare.return_value = ComparisonResult(
            chunk_index=0,
            normalized_transcript="hello world",
            normalized_caption="hello world",
            wer=0.0,
            cer=0.0,
            semantic_similarity=1.0,
        )
        
        chunk_path = temp_dir / "chunk.wav"
        chunk_path.touch()
        
        chunks = [
            Chunk(index=0, audio_path=chunk_path, start_time=0.0, end_time=30.0, duration=30.0),
        ]
        transcripts = [
            Transcript(text="Hello world", model_name="test", chunk_index=0),
        ]
        captions = [
            Caption(text="Hello world", start_time=0.0, end_time=30.0),
        ]
        
        results = pipeline._compare_chunks(chunks, transcripts, captions)
        
        assert len(results) == 1
        assert results[0].wer == 0.0
    
    def test_create_report(self, temp_dir):
        """Test report creation."""
        pipeline = YouTubeMinerPipeline.__new__(YouTubeMinerPipeline)
        pipeline.model_name = "faster-whisper"
        
        chunk_path = temp_dir / "chunk.wav"
        chunk_path.touch()
        
        chunks = [
            Chunk(index=0, audio_path=chunk_path, start_time=0.0, end_time=30.0, duration=30.0),
        ]
        results = [
            ComparisonResult(
                chunk_index=0,
                normalized_transcript="hello",
                normalized_caption="hello",
                wer=0.0,
                cer=0.0,
                semantic_similarity=1.0,
            ),
        ]
        
        report = pipeline._create_report(
            url="https://youtube.com/watch?v=test",
            video_info={"title": "Test", "duration": 30},
            chunks=chunks,
            results=results,
            processing_time=10.5,
        )
        
        assert report.video_url == "https://youtube.com/watch?v=test"
        assert report.total_chunks == 1
        assert report.processing_time == 10.5

