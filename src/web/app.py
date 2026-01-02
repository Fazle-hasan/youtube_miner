"""Flask web application for YouTube Miner."""

import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory

# Load environment variables from .env file at app startup
_project_root = Path(__file__).parent.parent.parent
load_dotenv(_project_root / ".env")

from src.pipeline import YouTubeMinerPipeline, extract_video_id
from src.transcriber import list_available_models
from src.downloader import YouTubeDownloader, CaptionExtractor
from src.converter import AudioConverter
from src.vad import VADChunker
from src.transcriber import get_transcriber
from src.deduplicator import NGramDeduplicator
from src.comparator import HybridScore

# Setup logging to both console and file
LOG_DIR = Path("./output/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "web_server.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE),
    ]
)
logger = logging.getLogger(__name__)

# Store for tracking job status
jobs: Dict[str, Dict[str, Any]] = {}


def create_app(output_dir: str = "./output") -> Flask:
    """Create and configure the Flask application.
    
    Args:
        output_dir: Base directory for pipeline outputs.
        
    Returns:
        Configured Flask application.
    """
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    
    app.config["OUTPUT_DIR"] = output_dir
    app.config["SECRET_KEY"] = os.urandom(24)
    
    @app.route("/")
    def index():
        """Render the main page."""
        return render_template("index.html", models=list_available_models())
    
    @app.route("/api/models", methods=["GET"])
    def get_models():
        """Get available transcription models."""
        model_info = {
            "whisper-tiny": {
                "name": "Whisper Tiny",
                "speed": "Fastest",
                "memory": "~1GB",
                "accuracy": "Basic",
            },
            "faster-whisper": {
                "name": "Faster Whisper",
                "speed": "Fast (4x)",
                "memory": "~2GB",
                "accuracy": "Good",
            },
            "indic-seamless": {
                "name": "Indic Seamless",
                "speed": "Medium",
                "memory": "~4GB",
                "accuracy": "Multilingual",
            },
            "whisper-large": {
                "name": "Whisper Large",
                "speed": "Slow",
                "memory": "~6GB",
                "accuracy": "Best",
            },
        }
        
        models = []
        for model_id in list_available_models():
            info = model_info.get(model_id, {})
            models.append({
                "id": model_id,
                **info,
            })
        
        return jsonify({"models": models})
    
    @app.route("/api/process", methods=["POST"])
    def process_video():
        """Start processing a YouTube video."""
        data = request.get_json()
        
        url = data.get("url")
        model = data.get("model", "faster-whisper")
        language = data.get("language", "en")  # Get language from user selection
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        # Create job ID
        job_id = str(uuid.uuid4())[:8]
        video_id = extract_video_id(url)
        
        # Folder name format: {video_id}_{model}
        folder_name = f"{video_id}_{model}"
        
        jobs[job_id] = {
            "id": job_id,
            "video_id": video_id,
            "folder_name": folder_name,
            "url": url,
            "model": model,
            "language": language,
            "status": "queued",
            "progress": 0,
            "stage": "Initializing...",
            "started_at": time.time(),
            "result": None,
            "error": None,
            # Chunk-wise tracking
            "total_chunks": 0,
            "current_chunk": 0,
            "chunks": [],  # List of chunk results
            "video_title": "",
            "video_duration": 0,
        }
        
        # Run pipeline in background thread
        thread = threading.Thread(
            target=_run_pipeline_with_chunks,
            args=(job_id, url, model, language, app.config["OUTPUT_DIR"]),
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "job_id": job_id,
            "video_id": video_id,
            "folder_name": folder_name,
            "status": "queued",
        })
    
    @app.route("/api/status/<job_id>", methods=["GET"])
    def get_status(job_id: str):
        """Get the status of a processing job including chunk results."""
        job = jobs.get(job_id)
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        return jsonify(job)
    
    @app.route("/api/results/<folder_name>", methods=["GET"])
    def get_results(folder_name: str):
        """Get the results for a processed video.
        
        Args:
            folder_name: Folder name in format {video_id}_{model}
        """
        output_dir = Path(app.config["OUTPUT_DIR"]) / folder_name
        report_path = output_dir / "report.json"
        
        if not report_path.exists():
            return jsonify({"error": "Results not found"}), 404
        
        with open(report_path, "r") as f:
            report = json.load(f)
        
        return jsonify(report)
    
    @app.route("/api/history", methods=["GET"])
    def get_history():
        """Get list of previously processed videos."""
        output_dir = Path(app.config["OUTPUT_DIR"])
        videos = []
        
        if output_dir.exists():
            for item in output_dir.iterdir():
                if item.is_dir() and item.name != "logs":
                    report_path = item / "report.json"
                    if report_path.exists():
                        try:
                            with open(report_path, "r") as f:
                                report = json.load(f)
                            
                            # Folder name format: {video_id}_{model}
                            folder_name = item.name
                            # Extract video_id (everything before last underscore + model)
                            # Handle both old format (just video_id) and new format (video_id_model)
                            parts = folder_name.rsplit("_", 1)
                            if len(parts) == 2 and parts[1] in ["whisper-tiny", "faster-whisper", "indic-seamless", "whisper-large"]:
                                video_id = parts[0]
                            else:
                                video_id = folder_name
                            
                            videos.append({
                                "folder_name": folder_name,
                                "video_id": video_id,
                                "title": report.get("video_title", "Unknown"),
                                "duration": report.get("video_duration", 0),
                                "model": report.get("model_used", "Unknown"),
                                "processed_at": report.get("timestamp", ""),
                                "summary": report.get("summary", {}),
                            })
                        except Exception:
                            pass
        
        # Sort by most recent
        videos.sort(key=lambda x: x.get("processed_at", ""), reverse=True)
        
        return jsonify({"videos": videos})
    
    @app.route("/api/download/<folder_name>/<file_type>", methods=["GET"])
    def download_file(folder_name: str, file_type: str):
        """Download transcription files.
        
        Args:
            folder_name: The video output folder name.
            file_type: One of 'report', 'srt', 'txt'.
        """
        from flask import Response
        
        output_dir = Path(app.config["OUTPUT_DIR"])
        video_dir = output_dir / folder_name
        
        if not video_dir.exists():
            return jsonify({"error": "Video folder not found"}), 404
        
        if file_type == "report":
            # Download JSON report
            report_path = video_dir / "report.json"
            if not report_path.exists():
                return jsonify({"error": "Report not found"}), 404
            
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return Response(
                content,
                mimetype="application/json",
                headers={"Content-Disposition": f"attachment; filename={folder_name}_report.json"}
            )
        
        elif file_type == "srt":
            # Generate and download SRT file
            report_path = video_dir / "report.json"
            if not report_path.exists():
                return jsonify({"error": "Report not found"}), 404
            
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            
            srt_content = _generate_srt(report)
            
            return Response(
                srt_content,
                mimetype="text/plain; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename={folder_name}_transcript.srt"}
            )
        
        elif file_type == "txt":
            # Generate and download TXT file
            report_path = video_dir / "report.json"
            if not report_path.exists():
                return jsonify({"error": "Report not found"}), 404
            
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            
            txt_content = _generate_txt(report)
            
            return Response(
                txt_content,
                mimetype="text/plain; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename={folder_name}_transcript.txt"}
            )
        
        else:
            return jsonify({"error": f"Unknown file type: {file_type}"}), 400
    
    return app


def _generate_srt(report: dict) -> str:
    """Generate SRT subtitle content from report.
    
    Args:
        report: The transcription report dictionary.
        
    Returns:
        SRT formatted string.
    """
    lines = []
    
    # Use chunks data which has timestamps and transcripts
    chunks = report.get("chunks", [])
    
    # If no chunks, fall back to results
    if not chunks:
        chunks = report.get("results", [])
    
    subtitle_index = 1
    for chunk in chunks:
        # Get transcript text - try different field names
        text = (
            chunk.get("transcript", "") or 
            chunk.get("hypothesis", "") or 
            chunk.get("normalized_transcript", "")
        )
        
        if not text or not text.strip():
            continue
        
        start_time = chunk.get("start_time", 0)
        end_time = chunk.get("end_time", start_time + 30)
        
        # Convert to SRT timestamp format (HH:MM:SS,mmm)
        start_srt = _seconds_to_srt_time(start_time)
        end_srt = _seconds_to_srt_time(end_time)
        
        lines.append(str(subtitle_index))
        lines.append(f"{start_srt} --> {end_srt}")
        lines.append(text.strip())
        lines.append("")
        
        subtitle_index += 1
    
    return "\n".join(lines)


def _generate_txt(report: dict) -> str:
    """Generate plain text transcript from report.
    
    Args:
        report: The transcription report dictionary.
        
    Returns:
        Plain text transcript.
    """
    lines = []
    
    # Add header
    title = report.get("video_title", "Unknown")
    model = report.get("model_used", "Unknown")
    duration = report.get("video_duration", 0)
    
    lines.append(f"# {title}")
    lines.append(f"# Model: {model}")
    lines.append(f"# Duration: {_format_duration(duration)}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("")
    
    # Use chunks data which has timestamps and transcripts
    chunks = report.get("chunks", [])
    
    # If no chunks, fall back to results
    if not chunks:
        chunks = report.get("results", [])
    
    # Add full transcript
    full_text = []
    for chunk in chunks:
        text = (
            chunk.get("transcript", "") or 
            chunk.get("hypothesis", "") or 
            chunk.get("normalized_transcript", "")
        )
        if text and text.strip():
            full_text.append(text.strip())
    
    lines.append(" ".join(full_text))
    lines.append("")
    lines.append("=" * 60)
    lines.append("")
    
    # Add timestamped version
    lines.append("# Timestamped Transcript:")
    lines.append("")
    
    for chunk in chunks:
        text = (
            chunk.get("transcript", "") or 
            chunk.get("hypothesis", "") or 
            chunk.get("normalized_transcript", "")
        )
        if text and text.strip():
            start_time = chunk.get("start_time", 0)
            timestamp = _format_timestamp(start_time)
            lines.append(f"[{timestamp}] {text.strip()}")
    
    return "\n".join(lines)


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


def _format_duration(seconds: float) -> str:
    """Format duration as MM:SS or HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _format_timestamp(seconds: float) -> str:
    """Format timestamp as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def _run_pipeline_with_chunks(
    job_id: str,
    url: str,
    model: str,
    language: str,
    output_dir: str,
) -> None:
    """Run the pipeline with chunk-by-chunk progress updates."""
    job = jobs[job_id]
    
    try:
        job["status"] = "running"
        job["stage"] = "Setting up..."
        job["progress"] = 5
        
        # Use folder name format: {video_id}_{model}
        folder_name = job["folder_name"]
        video_dir = Path(output_dir) / folder_name
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Stage 1: Download audio
        job["stage"] = "Downloading audio..."
        job["progress"] = 10
        
        downloader = YouTubeDownloader(
            output_dir=str(video_dir / "audio"),
            quiet=True,
        )
        audio_file, video_info = downloader.download_with_info(url)
        
        job["video_title"] = video_info.get("title", "Unknown")
        job["video_duration"] = video_info.get("duration", 0)
        
        # Stage 2: Convert to WAV
        job["stage"] = "Converting to WAV..."
        job["progress"] = 20
        
        converter = AudioConverter()
        wav_file = converter.convert(audio_file)
        
        # Stage 3: VAD chunking
        job["stage"] = "Detecting speech segments..."
        job["progress"] = 30
        
        chunker = VADChunker(
            output_dir=str(video_dir / "chunks"),
            chunk_duration=30.0,
        )
        chunks = chunker.chunk(wav_file)
        
        job["total_chunks"] = len(chunks)
        job["chunks"] = [{"status": "pending", "index": i} for i in range(len(chunks))]
        
        if not chunks:
            job["status"] = "completed"
            job["stage"] = "No speech detected"
            job["progress"] = 100
            return
        
        # Stage 5: Extract captions (get default YouTube captions)
        job["stage"] = "Extracting YouTube captions..."
        job["progress"] = 35
        
        # Use "auto" to get default YouTube captions without language restriction
        caption_extractor = CaptionExtractor(
            output_dir=str(video_dir / "captions"),
            language="auto",  # Get default captions from YouTube
        )
        captions = caption_extractor.extract(url)
        
        # Stage 4: Initialize transcriber
        job["stage"] = f"Loading {model} model..."
        job["progress"] = 40
        
        transcriber = get_transcriber(model, language=language)
        transcriber.load_model()
        
        deduplicator = NGramDeduplicator()
        comparator = HybridScore()
        
        # Stage 7: Process chunks one by one
        all_results = []
        base_progress = 40
        chunk_progress_range = 55  # 40-95%
        
        for i, chunk in enumerate(chunks):
            job["current_chunk"] = i + 1
            job["stage"] = f"Processing chunk {i + 1}/{len(chunks)}..."
            job["progress"] = base_progress + int((i / len(chunks)) * chunk_progress_range)
            
            # Update chunk status to processing
            job["chunks"][i]["status"] = "processing"
            
            try:
                # Transcribe
                transcript = transcriber.transcribe_chunk(chunk)
                
                # Deduplicate
                cleaned_text = deduplicator.deduplicate_text(transcript.text)
                
                # Get caption for this chunk
                caption_text = caption_extractor.get_caption_for_chunk(
                    captions, chunk.start_time, chunk.end_time
                )
                
                # Compare
                result = comparator.compare(
                    reference=caption_text,
                    hypothesis=cleaned_text,
                    chunk_index=chunk.index,
                )
                
                # Store chunk result
                chunk_result = {
                    "status": "completed",
                    "index": i,
                    "start_time": chunk.start_time,
                    "end_time": chunk.end_time,
                    "duration": chunk.duration,
                    "transcript": cleaned_text,
                    "caption": caption_text,
                    "wer": result.wer,
                    "cer": result.cer,
                    "semantic_similarity": result.semantic_similarity,
                    "hybrid_score": result.hybrid_score,
                }
                
                job["chunks"][i] = chunk_result
                all_results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")
                job["chunks"][i] = {
                    "status": "error",
                    "index": i,
                    "error": str(e),
                }
        
        # Stage 8: Calculate summary
        job["stage"] = "Generating report..."
        job["progress"] = 95
        
        if all_results:
            avg_wer = sum(r.wer for r in all_results) / len(all_results)
            avg_cer = sum(r.cer for r in all_results) / len(all_results)
            avg_semantic = sum(r.semantic_similarity for r in all_results) / len(all_results)
            avg_hybrid = sum(r.hybrid_score for r in all_results) / len(all_results)
        else:
            avg_wer = avg_cer = avg_semantic = avg_hybrid = 0.0
        
        # Create and save report
        from src.models import PipelineReport, MetricsSummary
        
        summary = MetricsSummary(
            avg_wer=avg_wer,
            avg_cer=avg_cer,
            avg_semantic_similarity=avg_semantic,
            avg_hybrid_score=avg_hybrid,
        )
        
        report = PipelineReport(
            video_url=url,
            video_title=job["video_title"],
            video_duration=job["video_duration"],
            model_used=model,
            total_chunks=len(chunks),
            results=all_results,
            summary=summary,
            processing_time=time.time() - job["started_at"],
        )
        
        report_path = video_dir / "report.json"
        report.save_json(str(report_path))
        
        # Save extended report with chunk timestamps for SRT/TXT generation
        extended_report = report.to_dict()
        extended_report["chunks"] = job["chunks"]
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(extended_report, f, indent=2, ensure_ascii=False)
        
        # Unload transcriber model to free GPU memory
        try:
            transcriber.unload_model()
            logger.info("Transcriber model unloaded to free memory")
        except Exception as e:
            logger.warning(f"Failed to unload model: {e}")
        
        # Mark complete
        job["status"] = "completed"
        job["progress"] = 100
        job["stage"] = "Complete!"
        job["result"] = {
            "folder_name": folder_name,
            "video_id": job["video_id"],
            "title": job["video_title"],
            "duration": job["video_duration"],
            "chunks": len(chunks),
            "processing_time": time.time() - job["started_at"],
            "language": language,
            "summary": {
                "avg_wer": avg_wer,
                "avg_cer": avg_cer,
                "avg_semantic_similarity": avg_semantic,
                "avg_hybrid_score": avg_hybrid,
            },
        }
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.exception(f"Pipeline failed for job {job_id}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["stage"] = "Failed"
        
        # Try to unload model even on failure to free memory
        try:
            transcriber.unload_model()  # type: ignore
        except (NameError, AttributeError):
            pass  # transcriber wasn't defined yet


def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Run the Flask development server.
    
    Args:
        host: Host to bind to.
        port: Port to listen on.
        debug: Enable debug mode.
    """
    app = create_app()
    print(f"\n🎬 YouTube Miner Web Interface")
    print(f"   Open http://{host}:{port} in your browser\n")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    run_server(debug=True)