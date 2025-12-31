"""End-to-end pipeline orchestrator."""

import json
import logging
import re
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

from src.downloader import YouTubeDownloader, CaptionExtractor
from src.converter import AudioConverter
from src.vad import VADChunker
from src.transcriber import get_transcriber, list_available_models
from src.deduplicator import NGramDeduplicator
from src.comparator import HybridScore
from src.models import (
    AudioFile,
    Chunk,
    Transcript,
    Caption,
    ComparisonResult,
    MetricsSummary,
    PipelineReport,
)

logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL.
    
    Supports various YouTube URL formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    
    Args:
        url: YouTube video URL.
        
    Returns:
        Video ID string.
    """
    # Try parsing as youtube.com URL
    parsed = urlparse(url)
    
    if 'youtube.com' in parsed.netloc:
        # Standard watch URL
        if parsed.path == '/watch':
            query = parse_qs(parsed.query)
            if 'v' in query:
                return query['v'][0]
        # Embed URL
        elif '/embed/' in parsed.path:
            return parsed.path.split('/embed/')[1].split('/')[0]
    
    # youtu.be short URL
    elif 'youtu.be' in parsed.netloc:
        return parsed.path.lstrip('/')
    
    # Fallback: try to find video ID pattern in URL
    match = re.search(r'([a-zA-Z0-9_-]{11})', url)
    if match:
        return match.group(1)
    
    # If all else fails, use a hash of the URL
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()[:11]


class YouTubeMinerPipeline:
    """End-to-end pipeline for YouTube audio processing and comparison.
    
    This orchestrator coordinates all pipeline stages:
    1. Download audio from YouTube
    2. Convert to WAV format
    3. Apply VAD to create speech chunks
    4. Transcribe chunks with selected model
    5. Extract YouTube captions
    6. Compare transcriptions with captions
    7. Generate report
    
    Example:
        >>> pipeline = YouTubeMinerPipeline(output_dir="./output")
        >>> report = pipeline.run("https://youtube.com/watch?v=...")
        >>> print(f"Average WER: {report.summary.avg_wer:.2%}")
    """
    
    def __init__(
        self,
        output_dir: str = "./output",
        model: str = "faster-whisper",
        language: str = "en",
        chunk_duration: float = 30.0,
        verbose: bool = False,
    ):
        """Initialize the pipeline.
        
        Args:
            output_dir: Base directory for all output files.
            model: Transcription model to use.
            language: Target language for transcription.
            chunk_duration: Target duration for audio chunks.
            verbose: Enable verbose logging.
        """
        self.base_output_dir = Path(output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_name = model
        self.language = language
        self.chunk_duration = chunk_duration
        self.verbose = verbose
        
        # Components will be initialized per-video in _setup_video_dir
        self.converter = AudioConverter()
        self.deduplicator = NGramDeduplicator()
        self.comparator = HybridScore()
        
        # Will be initialized when needed
        self._transcriber = None
        
        # Current video output directory (set during run)
        self._video_output_dir = None
        self._downloader = None
        self._caption_extractor = None
        self._chunker = None
    
    def _setup_video_dir(self, url: str) -> Path:
        """Create output directory for a specific video.
        
        Args:
            url: YouTube video URL.
            
        Returns:
            Path to the video-specific output directory.
        """
        video_id = extract_video_id(url)
        # Create folder named: {video_id}_{model_name}
        folder_name = f"{video_id}_{self.model_name}"
        video_dir = self.base_output_dir / folder_name
        video_dir.mkdir(parents=True, exist_ok=True)
        
        self._video_output_dir = video_dir
        
        # Initialize components with video-specific paths
        self._downloader = YouTubeDownloader(
            output_dir=str(video_dir / "audio"),
            quiet=not self.verbose,
        )
        self._caption_extractor = CaptionExtractor(
            output_dir=str(video_dir / "captions"),
            language=self.language,
        )
        self._chunker = VADChunker(
            output_dir=str(video_dir / "chunks"),
            chunk_duration=self.chunk_duration,
        )
        
        logger.info(f"Output directory for video {video_id} with model {self.model_name}: {video_dir}")
        return video_dir
    
    @property
    def downloader(self):
        """Get downloader (must call _setup_video_dir first)."""
        if self._downloader is None:
            raise RuntimeError("Call _setup_video_dir before accessing downloader")
        return self._downloader
    
    @property
    def caption_extractor(self):
        """Get caption extractor (must call _setup_video_dir first)."""
        if self._caption_extractor is None:
            raise RuntimeError("Call _setup_video_dir before accessing caption_extractor")
        return self._caption_extractor
    
    @property
    def chunker(self):
        """Get VAD chunker (must call _setup_video_dir first)."""
        if self._chunker is None:
            raise RuntimeError("Call _setup_video_dir before accessing chunker")
        return self._chunker
    
    @property
    def transcriber(self):
        """Lazy load transcriber."""
        if self._transcriber is None:
            self._transcriber = get_transcriber(self.model_name, language=self.language)
        return self._transcriber
    
    def run(self, url: str) -> PipelineReport:
        """Run the complete pipeline on a YouTube video.
        
        Args:
            url: YouTube video URL.
            
        Returns:
            PipelineReport with all results and metrics.
        """
        start_time = time.time()
        logger.info(f"Starting pipeline for: {url}")
        
        # Setup video-specific output directory
        video_dir = self._setup_video_dir(url)
        logger.info(f"Output directory: {video_dir}")
        
        # Stage 1: Download audio
        logger.info("Stage 1/7: Downloading audio...")
        audio_file, video_info = self.downloader.download_with_info(url)
        
        # Stage 2: Convert to WAV
        logger.info("Stage 2/7: Converting to WAV...")
        wav_file = self.converter.convert(audio_file)
        
        # Stage 3: VAD chunking
        logger.info("Stage 3/7: Chunking with VAD...")
        chunks = self.chunker.chunk(wav_file)
        
        if not chunks:
            logger.warning("No speech chunks detected!")
            return self._create_empty_report(url, video_info, start_time)
        
        # Stage 4: Transcription
        logger.info(f"Stage 4/7: Transcribing with {self.model_name}...")
        transcripts = self.transcriber.transcribe_chunks(chunks)
        
        # Stage 5: Deduplication
        logger.info("Stage 5/7: Removing repetitions...")
        transcripts = self.deduplicator.deduplicate_transcripts(transcripts)
        
        # Stage 6: Extract captions
        logger.info("Stage 6/7: Extracting YouTube captions...")
        captions = self.caption_extractor.extract(url)
        
        # Stage 7: Compare
        logger.info("Stage 7/7: Comparing transcriptions...")
        results = self._compare_chunks(chunks, transcripts, captions)
        
        # Create report
        processing_time = time.time() - start_time
        report = self._create_report(
            url, video_info, chunks, results, processing_time
        )
        
        # Save report in video-specific directory
        report_path = self._video_output_dir / "report.json"
        report.save_json(str(report_path))
        logger.info(f"Report saved to: {report_path}")
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _compare_chunks(
        self,
        chunks: List[Chunk],
        transcripts: List[Transcript],
        captions: List[Caption],
    ) -> List[ComparisonResult]:
        """Compare transcripts with captions for each chunk.
        
        Args:
            chunks: Audio chunks.
            transcripts: Model transcriptions.
            captions: YouTube captions.
            
        Returns:
            List of comparison results.
        """
        results = []
        
        for chunk, transcript in zip(chunks, transcripts):
            # Get caption text for this chunk's time range
            caption_text = self.caption_extractor.get_caption_for_chunk(
                captions, chunk.start_time, chunk.end_time
            )
            
            # Compare
            result = self.comparator.compare(
                reference=caption_text,
                hypothesis=transcript.text,
                chunk_index=chunk.index,
            )
            results.append(result)
        
        return results
    
    def _create_report(
        self,
        url: str,
        video_info: dict,
        chunks: List[Chunk],
        results: List[ComparisonResult],
        processing_time: float,
    ) -> PipelineReport:
        """Create the final pipeline report.
        
        Args:
            url: YouTube URL.
            video_info: Video metadata.
            chunks: Processed chunks.
            results: Comparison results.
            processing_time: Total processing time.
            
        Returns:
            PipelineReport object.
        """
        summary = MetricsSummary.from_results(results)
        
        return PipelineReport(
            video_url=url,
            video_title=video_info.get("title", "Unknown"),
            video_duration=video_info.get("duration", 0),
            model_used=self.model_name,
            total_chunks=len(chunks),
            results=results,
            summary=summary,
            processing_time=processing_time,
        )
    
    def _create_empty_report(
        self, url: str, video_info: dict, start_time: float
    ) -> PipelineReport:
        """Create an empty report when no speech is detected."""
        return PipelineReport(
            video_url=url,
            video_title=video_info.get("title", "Unknown"),
            video_duration=video_info.get("duration", 0),
            model_used=self.model_name,
            total_chunks=0,
            results=[],
            summary=MetricsSummary(
                avg_wer=0, avg_cer=0, avg_semantic_similarity=0, avg_hybrid_score=0
            ),
            processing_time=time.time() - start_time,
        )
    
    def _print_summary(self, report: PipelineReport) -> None:
        """Print a summary of the pipeline results."""
        print("\n" + "=" * 60)
        print("YOUTUBE MINER PIPELINE - RESULTS")
        print("=" * 60)
        print(f"Video: {report.video_title}")
        print(f"Duration: {report.video_duration:.1f}s")
        print(f"Model: {report.model_used}")
        print(f"Chunks: {report.total_chunks}")
        print(f"Processing Time: {report.processing_time:.1f}s")
        print("-" * 60)
        print("COMPARISON METRICS (vs YouTube captions)")
        print(f"  Average WER: {report.summary.avg_wer:.2%}")
        print(f"  Average CER: {report.summary.avg_cer:.2%}")
        print(f"  Average Semantic Similarity: {report.summary.avg_semantic_similarity:.2%}")
        print(f"  Average Hybrid Score: {report.summary.avg_hybrid_score:.2%}")
        print("=" * 60 + "\n")
    
    def run_step_by_step(self, url: str) -> dict:
        """Run pipeline and return intermediate results.
        
        Useful for debugging or accessing individual stage outputs.
        
        Args:
            url: YouTube video URL.
            
        Returns:
            Dictionary with all intermediate results.
        """
        # Setup video-specific output directory
        video_dir = self._setup_video_dir(url)
        
        results = {}
        results["video_dir"] = video_dir
        
        # Download
        audio_file, video_info = self.downloader.download_with_info(url)
        results["audio_file"] = audio_file
        results["video_info"] = video_info
        
        # Convert
        wav_file = self.converter.convert(audio_file)
        results["wav_file"] = wav_file
        
        # Chunk
        chunks = self.chunker.chunk(wav_file)
        results["chunks"] = chunks
        
        # Transcribe
        transcripts = self.transcriber.transcribe_chunks(chunks)
        results["raw_transcripts"] = transcripts
        
        # Deduplicate
        transcripts = self.deduplicator.deduplicate_transcripts(transcripts)
        results["transcripts"] = transcripts
        
        # Captions
        captions = self.caption_extractor.extract(url)
        results["captions"] = captions
        
        # Compare
        comparisons = self._compare_chunks(chunks, transcripts, captions)
        results["comparisons"] = comparisons
        
        return results

