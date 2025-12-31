"""YouTube audio downloader using yt-dlp."""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple

import yt_dlp

from src.models.audio import AudioFile

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Download audio from YouTube videos using yt-dlp.
    
    Example:
        >>> downloader = YouTubeDownloader(output_dir="./downloads")
        >>> audio_file = downloader.download("https://youtube.com/watch?v=...")
        >>> print(audio_file.path)
    """
    
    def __init__(self, output_dir: str = "./output", quiet: bool = False):
        """Initialize the downloader.
        
        Args:
            output_dir: Directory to save downloaded audio files.
            quiet: If True, suppress yt-dlp output.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.quiet = quiet
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL.
        
        Args:
            url: YouTube video URL.
            
        Returns:
            Video ID or None if not found.
        """
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be/)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info(self, url: str) -> dict:
        """Get video metadata without downloading.
        
        Args:
            url: YouTube video URL.
            
        Returns:
            Dictionary containing video metadata.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'id': info.get('id'),
                'title': info.get('title'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'description': info.get('description', '')[:500],
                'view_count': info.get('view_count'),
            }
    
    def download(self, url: str, filename: Optional[str] = None) -> AudioFile:
        """Download audio from YouTube video.
        
        Args:
            url: YouTube video URL.
            filename: Optional custom filename (without extension).
            
        Returns:
            AudioFile object representing the downloaded audio.
            
        Raises:
            ValueError: If URL is invalid.
            RuntimeError: If download fails.
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")
        
        if filename is None:
            filename = video_id
        
        output_template = str(self.output_dir / filename)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template + '.%(ext)s',
            'quiet': self.quiet,
            'no_warnings': self.quiet,
            'extract_audio': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',  # Use MP3 for better compatibility
                'preferredquality': '192',
            }],
        }
        
        logger.info(f"Downloading audio from: {url}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                duration = info.get('duration', 0)
                title = info.get('title', 'Unknown')
                
            # Find the downloaded file
            output_path = Path(output_template + '.mp3')
            if not output_path.exists():
                # Try other common extensions
                for ext in ['.m4a', '.webm', '.opus', '.wav']:
                    alt_path = Path(output_template + ext)
                    if alt_path.exists():
                        output_path = alt_path
                        break
            
            if not output_path.exists():
                raise RuntimeError(f"Downloaded file not found: {output_path}")
            
            logger.info(f"Downloaded: {output_path} ({duration}s)")
            
            return AudioFile(
                path=output_path,
                format=output_path.suffix[1:],  # Remove the dot
                duration=float(duration),
                sample_rate=0,  # Will be set after conversion
                channels=0,  # Will be set after conversion
                source_url=url,
            )
            
        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(f"Download failed: {e}")
    
    def download_with_info(self, url: str) -> Tuple[AudioFile, dict]:
        """Download audio and return both file and metadata.
        
        Args:
            url: YouTube video URL.
            
        Returns:
            Tuple of (AudioFile, metadata dict).
        """
        info = self.get_video_info(url)
        audio_file = self.download(url, filename=info['id'])
        return audio_file, info

