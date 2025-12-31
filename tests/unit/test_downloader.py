"""Unit tests for YouTube downloader."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.downloader.youtube import YouTubeDownloader


class TestYouTubeDownloader:
    """Tests for YouTubeDownloader."""
    
    def test_extract_video_id_standard_url(self):
        """Test extracting video ID from standard URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = YouTubeDownloader.extract_video_id(url)
        
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_short_url(self):
        """Test extracting video ID from short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = YouTubeDownloader.extract_video_id(url)
        
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_embed_url(self):
        """Test extracting video ID from embed URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = YouTubeDownloader.extract_video_id(url)
        
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_invalid_url(self):
        """Test extracting video ID from invalid URL."""
        url = "https://example.com/video"
        video_id = YouTubeDownloader.extract_video_id(url)
        
        assert video_id is None
    
    def test_extract_video_id_with_extra_params(self):
        """Test extracting video ID with extra URL parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s&list=PLxxx"
        video_id = YouTubeDownloader.extract_video_id(url)
        
        assert video_id == "dQw4w9WgXcQ"
    
    def test_init_creates_output_dir(self, temp_dir):
        """Test that initialization creates output directory."""
        output_path = temp_dir / "downloads"
        
        downloader = YouTubeDownloader(output_dir=str(output_path))
        
        assert output_path.exists()
        assert downloader.output_dir == output_path
    
    def test_download_invalid_url_raises(self, temp_dir):
        """Test that invalid URL raises ValueError."""
        downloader = YouTubeDownloader(output_dir=str(temp_dir))
        
        with pytest.raises(ValueError, match="Invalid YouTube URL"):
            downloader.download("https://example.com/invalid")
    
    @patch('src.downloader.youtube.yt_dlp.YoutubeDL')
    def test_get_video_info(self, mock_ydl_class, temp_dir):
        """Test getting video metadata."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info.return_value = {
            'id': 'test123',
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
        }
        
        downloader = YouTubeDownloader(output_dir=str(temp_dir))
        info = downloader.get_video_info("https://youtube.com/watch?v=test123")
        
        assert info['id'] == 'test123'
        assert info['title'] == 'Test Video'
        assert info['duration'] == 120

