"""Unit tests for caption extractor."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.downloader.captions import CaptionExtractor
from src.models.transcript import Caption


class TestCaptionExtractor:
    """Tests for CaptionExtractor."""
    
    def test_init(self, temp_dir):
        """Test initialization."""
        extractor = CaptionExtractor(
            output_dir=str(temp_dir),
            language="en",
        )
        
        assert extractor.language == "en"
        assert temp_dir.exists()
    
    def test_parse_timestamp(self):
        """Test VTT timestamp parsing."""
        extractor = CaptionExtractor()
        
        # Test standard timestamp
        result = extractor._parse_timestamp("00:01:30.500")
        assert result == 90.5
        
        # Test zero timestamp
        result = extractor._parse_timestamp("00:00:00.000")
        assert result == 0.0
        
        # Test hour timestamp
        result = extractor._parse_timestamp("01:30:00.000")
        assert result == 5400.0
    
    def test_clean_vtt_text(self):
        """Test VTT text cleaning."""
        extractor = CaptionExtractor()
        
        # Test removing music tags
        result = extractor._clean_vtt_text("[Music] Hello world [Applause]")
        assert result == "Hello world"
        
        # Test collapsing whitespace
        result = extractor._clean_vtt_text("hello   world")
        assert result == "hello world"
    
    def test_parse_vtt(self):
        """Test VTT content parsing."""
        extractor = CaptionExtractor()
        
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello world

00:00:10.000 --> 00:00:15.000
This is a test
"""
        
        captions = extractor._parse_vtt(
            vtt_content,
            "https://youtube.com/watch?v=test",
            "auto",
        )
        
        assert len(captions) >= 1
        # First caption should be "Hello world"
        assert "Hello world" in captions[0].text
    
    def test_merge_overlapping_captions(self):
        """Test merging overlapping captions."""
        extractor = CaptionExtractor()
        
        captions = [
            Caption(text="Hello", start_time=0.0, end_time=2.0),
            Caption(text="world", start_time=1.9, end_time=4.0),
            Caption(text="test", start_time=10.0, end_time=12.0),
        ]
        
        merged = extractor._merge_captions(captions)
        
        # First two should merge, third stays separate
        assert len(merged) == 2
        assert "Hello" in merged[0].text
        assert "world" in merged[0].text
    
    def test_get_caption_for_chunk(self):
        """Test getting captions for a specific time range."""
        extractor = CaptionExtractor()
        
        captions = [
            Caption(text="First", start_time=0.0, end_time=10.0),
            Caption(text="Second", start_time=10.0, end_time=20.0),
            Caption(text="Third", start_time=20.0, end_time=30.0),
            Caption(text="Fourth", start_time=30.0, end_time=40.0),
        ]
        
        # Get captions for 5-25 second range
        result = extractor.get_caption_for_chunk(captions, 5.0, 25.0)
        
        assert "First" in result
        assert "Second" in result
        assert "Third" in result
        assert "Fourth" not in result
    
    def test_get_caption_for_chunk_no_overlap(self):
        """Test getting captions when no overlap."""
        extractor = CaptionExtractor()
        
        captions = [
            Caption(text="First", start_time=0.0, end_time=10.0),
        ]
        
        result = extractor.get_caption_for_chunk(captions, 20.0, 30.0)
        
        assert result == ""
    
    @patch('src.downloader.captions.yt_dlp.YoutubeDL')
    def test_extract_no_captions(self, mock_ydl_class):
        """Test extraction when no captions available."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info.return_value = {
            'automatic_captions': {},
            'subtitles': {},
        }
        
        extractor = CaptionExtractor()
        captions = extractor.extract("https://youtube.com/watch?v=test")
        
        assert captions == []

