"""YouTube caption extraction using youtube_transcript_api."""

import logging
import re
from pathlib import Path
from typing import List, Optional, Dict

from youtube_transcript_api import YouTubeTranscriptApi

from src.models.transcript import Caption

logger = logging.getLogger(__name__)


class CaptionExtractor:
    """Extract auto-generated captions from YouTube videos.
    
    Uses youtube_transcript_api for reliable multilingual caption extraction.
    
    Example:
        >>> extractor = CaptionExtractor()
        >>> captions = extractor.extract("https://youtube.com/watch?v=...")
        >>> for caption in captions:
        ...     print(f"{caption.start_time}: {caption.text}")
    """
    
    def __init__(self, output_dir: str = "./output", language: str = "en"):
        """Initialize the caption extractor.
        
        Args:
            output_dir: Directory to save caption files.
            language: Preferred caption language code (e.g., 'en', 'hi', 'auto').
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.language = language
        self._api = YouTubeTranscriptApi()
    
    @staticmethod
    def extract_video_id(url_or_id: str) -> Optional[str]:
        """Extract video ID from a YouTube URL or return the ID if already provided.
        
        Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID
        - VIDEO_ID (direct ID)
        """
        # If it's already just an ID (11 characters, alphanumeric with - and _)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
            return url_or_id
        
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None
    
    def list_available_transcripts(self, url: str) -> List[Dict]:
        """List all available transcripts for a video.
        
        Args:
            url: YouTube video URL or video ID.
            
        Returns:
            List of dicts with transcript info.
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            logger.error(f"Invalid YouTube URL or video ID: {url}")
            return []
        
        try:
            transcript_list = self._api.list(video_id)
            
            transcripts = []
            for transcript in transcript_list:
                transcripts.append({
                    'language': transcript.language,
                    'language_code': transcript.language_code,
                    'is_generated': transcript.is_generated,
                    'is_translatable': transcript.is_translatable,
                })
            
            return transcripts
        except Exception as e:
            logger.error(f"Error listing transcripts: {e}")
            return []
    
    def extract(self, url: str) -> List[Caption]:
        """Extract captions from YouTube video.
        
        First tries to get auto-generated captions in the preferred language,
        then falls back to any available caption.
        
        Args:
            url: YouTube video URL.
            
        Returns:
            List of Caption objects with timestamps.
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            logger.error(f"Invalid YouTube URL: {url}")
            return []
        
        logger.info(f"Extracting captions for video: {video_id}")
        
        try:
            transcript_list = self._api.list(video_id)
            
            transcript = None
            caption_type = None
            found_language = None
            
            # Get languages to try
            languages_to_try = self._get_languages_to_try()
            
            # Strategy 1: Try auto-generated captions in preferred languages
            for lang in languages_to_try:
                try:
                    transcript = transcript_list.find_generated_transcript([lang])
                    caption_type = "auto-generated"
                    found_language = transcript.language
                    logger.info(f"Found auto-generated captions in: {found_language}")
                    break
                except Exception:
                    pass
            
            # Strategy 2: Try manual captions in preferred languages
            if transcript is None:
                for lang in languages_to_try:
                    try:
                        transcript = transcript_list.find_manually_created_transcript([lang])
                        caption_type = "manual"
                        found_language = transcript.language
                        logger.info(f"Found manual captions in: {found_language}")
                        break
                    except Exception:
                        pass
            
            # Strategy 3: Get ANY available transcript as last resort
            if transcript is None:
                try:
                    for t in transcript_list:
                        transcript = t
                        caption_type = "auto-generated" if t.is_generated else "manual"
                        found_language = t.language
                        logger.info(f"Using available captions in: {found_language} ({t.language_code})")
                        break
                except Exception:
                    pass
            
            if transcript is None:
                logger.warning(f"No captions available for video {video_id}")
                return []
            
            # Fetch the captions
            caption_data = transcript.fetch()
            
            logger.info(f"✅ Retrieved {caption_type} captions in {found_language}")
            logger.info(f"   Total segments: {len(caption_data)}")
            
            # Convert to Caption objects
            captions = []
            for segment in caption_data:
                start_time = segment.start
                duration = segment.duration
                end_time = start_time + duration
                text = self._clean_caption_text(segment.text)
                
                if text.strip():
                    captions.append(Caption(
                        text=text,
                        start_time=start_time,
                        end_time=end_time,
                        language=found_language or self.language,
                        source=caption_type or "unknown",
                        video_url=url,
                    ))
            
            logger.info(f"Extracted {len(captions)} caption segments")
            return captions
            
        except Exception as e:
            logger.error(f"Failed to extract captions: {e}")
            return []
    
    def _get_languages_to_try(self) -> List[str]:
        """Get list of languages to try for caption extraction.
        
        Returns:
            List of language codes in priority order.
        """
        if self.language == "auto":
            # For auto, try common languages including Indian languages
            return ["hi", "en", "hi-IN", "en-IN", "en-US", "en-GB", "ta", "te", "mr", "bn"]
        elif self.language == "hi":
            # For Hindi, try Hindi variants first, then English
            return ["hi", "hi-IN", "hi-Latn", "en", "en-IN"]
        elif self.language == "en":
            # For English, try English variants
            return ["en", "en-US", "en-GB", "en-IN", "en-AU"]
        else:
            # For other languages, try the specified language and common fallbacks
            return [self.language, "en", "hi"]
    
    def _clean_caption_text(self, text: str) -> str:
        """Clean caption text artifacts.
        
        Args:
            text: Raw caption text.
            
        Returns:
            Cleaned text.
        """
        import html
        
        # Decode HTML entities (&nbsp;, &amp;, etc.)
        text = html.unescape(text)
        
        # Remove common artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove [Music], [Applause], etc.
        text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
        text = text.replace('\n', ' ')
        
        return text.strip()
    
    def get_caption_for_chunk(
        self, captions: List[Caption], start_time: float, end_time: float,
        alignment_mode: str = "center"
    ) -> str:
        """Get caption text for a specific time range with improved alignment.
        
        Args:
            captions: List of all captions.
            start_time: Chunk start time in seconds.
            end_time: Chunk end time in seconds.
            alignment_mode: How to match captions to chunks:
                - "center": Include caption if its center point is within chunk (default)
                - "majority": Include caption if >50% overlaps with chunk
                - "any": Include caption if any part overlaps (legacy behavior)
            
        Returns:
            Concatenated caption text for the time range.
        """
        relevant_texts = []
        
        for caption in captions:
            include = False
            
            if alignment_mode == "center":
                # Include caption only if its center point falls within the chunk
                caption_center = (caption.start_time + caption.end_time) / 2
                include = start_time <= caption_center <= end_time
                
            elif alignment_mode == "majority":
                # Include caption only if majority (>50%) of it overlaps with chunk
                overlap_start = max(caption.start_time, start_time)
                overlap_end = min(caption.end_time, end_time)
                overlap_duration = max(0, overlap_end - overlap_start)
                caption_duration = caption.end_time - caption.start_time
                
                if caption_duration > 0:
                    overlap_ratio = overlap_duration / caption_duration
                    include = overlap_ratio > 0.5
                    
            else:  # "any" - legacy behavior
                include = caption.end_time >= start_time and caption.start_time <= end_time
            
            if include:
                relevant_texts.append(caption.text)
        
        return ' '.join(relevant_texts)
