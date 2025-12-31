"""Command-line interface for YouTube Miner."""

import logging
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.pipeline import YouTubeMinerPipeline
from src.transcriber import list_available_models

console = Console()

# PID file location for tracking web server
PID_FILE = Path.home() / ".youtube_miner_web.pid"


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with Rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group()
@click.version_option(version="1.0.0", prog_name="youtube-miner")
def cli():
    """YouTube Miner - Audio extraction, transcription, and comparison pipeline."""
    pass


@cli.command()
@click.argument("url")
@click.option(
    "--output", "-o",
    default="./output",
    help="Output directory for results",
    type=click.Path(),
)
@click.option(
    "--model", "-m",
    default="faster-whisper",
    type=click.Choice(list_available_models()),
    help="Transcription model to use",
)
@click.option(
    "--language", "-l",
    default="en",
    help="Target language for transcription",
)
@click.option(
    "--chunk-duration", "-c",
    default=30.0,
    type=float,
    help="Target chunk duration in seconds",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output",
)
def run(
    url: str,
    output: str,
    model: str,
    language: str,
    chunk_duration: float,
    verbose: bool,
):
    """Run the complete pipeline on a YouTube video.
    
    URL: YouTube video URL to process
    
    Example:
        youtube-miner run "https://youtube.com/watch?v=..." -m faster-whisper
    """
    setup_logging(verbose)
    
    console.print(f"[bold blue]YouTube Miner[/bold blue] - Processing video...")
    console.print(f"URL: {url}")
    console.print(f"Model: {model}")
    console.print(f"Output: {output}")
    console.print()
    
    try:
        pipeline = YouTubeMinerPipeline(
            output_dir=output,
            model=model,
            language=language,
            chunk_duration=chunk_duration,
            verbose=verbose,
        )
        
        report = pipeline.run(url)
        
        console.print("[bold green]✓ Pipeline completed successfully![/bold green]")
        console.print(f"Report saved to: {Path(output) / 'report.json'}")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option("--output", "-o", default="./output", help="Output directory")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def download(url: str, output: str, verbose: bool):
    """Download audio from a YouTube video.
    
    URL: YouTube video URL
    """
    setup_logging(verbose)
    
    from src.downloader import YouTubeDownloader
    
    console.print(f"[bold]Downloading audio from:[/bold] {url}")
    
    try:
        downloader = YouTubeDownloader(output_dir=output, quiet=not verbose)
        audio_file, info = downloader.download_with_info(url)
        
        console.print(f"[green]✓ Downloaded:[/green] {audio_file.path}")
        console.print(f"  Duration: {audio_file.duration:.1f}s")
        console.print(f"  Title: {info.get('title', 'Unknown')}")
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output WAV path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def convert(input_path: str, output: Optional[str], verbose: bool):
    """Convert audio file to WAV format (16kHz, mono).
    
    INPUT_PATH: Path to audio file
    """
    setup_logging(verbose)
    
    from src.converter import AudioConverter
    
    console.print(f"[bold]Converting:[/bold] {input_path}")
    
    try:
        converter = AudioConverter()
        wav_file = converter.convert_from_path(input_path, output)
        
        console.print(f"[green]✓ Converted:[/green] {wav_file.path}")
        console.print(f"  Sample Rate: {wav_file.sample_rate}Hz")
        console.print(f"  Duration: {wav_file.duration:.1f}s")
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--output", "-o", default="./output/chunks", help="Output directory")
@click.option("--duration", "-d", default=30.0, type=float, help="Chunk duration")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def chunk(input_path: str, output: str, duration: float, verbose: bool):
    """Chunk audio file using Voice Activity Detection.
    
    INPUT_PATH: Path to WAV audio file
    """
    setup_logging(verbose)
    
    from src.vad import VADChunker
    
    console.print(f"[bold]Chunking:[/bold] {input_path}")
    
    try:
        chunker = VADChunker(output_dir=output, chunk_duration=duration)
        chunks = chunker.chunk_from_path(input_path)
        
        console.print(f"[green]✓ Created {len(chunks)} chunks[/green]")
        for chunk in chunks[:5]:  # Show first 5
            console.print(f"  Chunk {chunk.index}: {chunk.duration:.1f}s")
        if len(chunks) > 5:
            console.print(f"  ... and {len(chunks) - 5} more")
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--model", "-m",
    default="faster-whisper",
    type=click.Choice(list_available_models()),
    help="Transcription model",
)
@click.option("--language", "-l", default="en", help="Language code")
@click.option("--output", "-o", help="Output JSON path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def transcribe(
    input_path: str,
    model: str,
    language: str,
    output: Optional[str],
    verbose: bool,
):
    """Transcribe an audio file.
    
    INPUT_PATH: Path to audio file
    """
    setup_logging(verbose)
    
    from src.transcriber import get_transcriber
    
    console.print(f"[bold]Transcribing:[/bold] {input_path}")
    console.print(f"Model: {model}")
    
    try:
        transcriber = get_transcriber(model, language=language)
        transcript = transcriber.transcribe_file(input_path)
        
        console.print(f"[green]✓ Transcription complete[/green]")
        console.print(f"  Words: {transcript.word_count}")
        console.print(f"  Processing time: {transcript.processing_time:.2f}s")
        console.print()
        console.print("[bold]Text:[/bold]")
        console.print(transcript.text[:500] + "..." if len(transcript.text) > 500 else transcript.text)
        
        if output:
            import json
            Path(output).write_text(json.dumps(transcript.to_dict(), indent=2))
            console.print(f"\nSaved to: {output}")
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option("--output", "-o", default="./output/captions", help="Output directory")
@click.option("--language", "-l", default="en", help="Caption language")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def captions(url: str, output: str, language: str, verbose: bool):
    """Extract captions from a YouTube video.
    
    URL: YouTube video URL
    """
    setup_logging(verbose)
    
    from src.downloader import CaptionExtractor
    
    console.print(f"[bold]Extracting captions from:[/bold] {url}")
    
    try:
        extractor = CaptionExtractor(output_dir=output, language=language)
        caps = extractor.extract(url)
        
        if caps:
            console.print(f"[green]✓ Extracted {len(caps)} caption segments[/green]")
            for cap in caps[:5]:
                console.print(f"  [{cap.start_time:.1f}s] {cap.text[:50]}...")
            if len(caps) > 5:
                console.print(f"  ... and {len(caps) - 5} more")
        else:
            console.print("[yellow]⚠ No captions found for this video[/yellow]")
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("text1")
@click.argument("text2")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def compare(text1: str, text2: str, verbose: bool):
    """Compare two texts and show metrics.
    
    TEXT1: Reference text (e.g., YouTube caption)
    TEXT2: Hypothesis text (e.g., model output)
    """
    setup_logging(verbose)
    
    from src.comparator import HybridScore
    
    console.print("[bold]Comparing texts...[/bold]")
    
    try:
        scorer = HybridScore()
        result = scorer.compare(text1, text2)
        
        console.print()
        console.print("[bold]Comparison Results:[/bold]")
        console.print(f"  WER: {result.wer:.2%}")
        console.print(f"  CER: {result.cer:.2%}")
        console.print(f"  Semantic Similarity: {result.semantic_similarity:.2%}")
        console.print(f"  Hybrid Score: {result.hybrid_score:.2%}")
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
def models():
    """List available transcription models."""
    console.print("[bold]Available Transcription Models:[/bold]")
    console.print()
    
    model_info = {
        "whisper-tiny": ("Fastest", "~1GB", "Basic accuracy"),
        "faster-whisper": ("Fast (4x)", "~2GB", "Good accuracy"),
        "indic-seamless": ("Medium", "~4GB", "Multilingual (100+ languages)"),
        "whisper-large": ("Slow", "~6GB", "Best accuracy"),
    }
    
    for model in list_available_models():
        info = model_info.get(model, ("Unknown", "Unknown", "Unknown"))
        console.print(f"  [bold cyan]{model}[/bold cyan]")
        console.print(f"    Speed: {info[0]}, Memory: {info[1]}")
        console.print(f"    {info[2]}")
        console.print()


@cli.group()
def web():
    """Web interface commands (start/stop)."""
    pass


@web.command()
@click.option(
    "--host", "-h",
    default="127.0.0.1",
    help="Host to bind to",
)
@click.option(
    "--port", "-p",
    default=5000,
    type=int,
    help="Port to listen on",
)
@click.option(
    "--output", "-o",
    default="./output",
    help="Output directory for results",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
)
@click.option(
    "--background", "-b",
    is_flag=True,
    help="Run in background (daemon mode)",
)
def start(host: str, port: int, output: str, debug: bool, background: bool):
    """Start the web interface.
    
    Opens a browser-based UI for processing YouTube videos.
    
    Examples:
        youtube-miner web start
        youtube-miner web start --port 8080
        youtube-miner web start --background
    """
    # Check if already running
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Check if process is still running
            os.kill(pid, 0)
            console.print(f"[yellow]⚠ Web server already running (PID: {pid})[/yellow]")
            console.print(f"   Use [bold]youtube-miner web stop[/bold] to stop it first")
            return
        except (ProcessLookupError, ValueError):
            # Process not running, remove stale PID file
            PID_FILE.unlink()
    
    if background:
        # Start in background mode
        console.print()
        console.print("[bold green]⛏️  YouTube Miner Web Interface[/bold green]")
        console.print()
        
        # Use subprocess to start in background
        cmd = [
            sys.executable, "-c",
            f"""
import os
os.chdir("{os.getcwd()}")
from src.web.app import run_server
run_server(host="{host}", port={port}, debug={debug})
"""
        ]
        
        # Start process in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        
        # Save PID
        PID_FILE.write_text(str(process.pid))
        
        console.print(f"   [green]✓ Started in background[/green] (PID: {process.pid})")
        console.print(f"   [dim]Open your browser at:[/dim] [bold cyan]http://{host}:{port}[/bold cyan]")
        console.print()
        console.print(f"   [dim]Logs:[/dim] output/logs/web_server.log")
        console.print(f"   [dim]Stop with:[/dim] [bold]youtube-miner web stop[/bold]")
        console.print()
    else:
        # Run in foreground
        from src.web.app import run_server
        
        # Save current PID
        PID_FILE.write_text(str(os.getpid()))
        
        console.print()
        console.print("[bold green]⛏️  YouTube Miner Web Interface[/bold green]")
        console.print()
        console.print(f"   [dim]Open your browser at:[/dim] [bold cyan]http://{host}:{port}[/bold cyan]")
        console.print()
        console.print("   [dim]Press Ctrl+C to stop[/dim]")
        console.print()
        
        try:
            run_server(host=host, port=port, debug=debug)
        finally:
            # Clean up PID file
            if PID_FILE.exists():
                PID_FILE.unlink()


@web.command()
@click.option(
    "--port", "-p",
    default=5000,
    type=int,
    help="Port to stop server on (default: 5000)",
)
def stop(port: int):
    """Stop the running web server.
    
    Example:
        youtube-miner web stop
        youtube-miner web stop --port 8080
    """
    pid = None
    
    # Try to get PID from file first
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
        except ValueError:
            PID_FILE.unlink()
    
    # If no PID file, check port
    if pid is None:
        pid = _check_port_in_use(port)
    
    if pid is None:
        console.print(f"[yellow]⚠ No web server running on port {port}[/yellow]")
        return
    
    # Try to terminate gracefully first
    console.print(f"[dim]Stopping web server (PID: {pid})...[/dim]")
    
    try:
        os.kill(pid, signal.SIGTERM)
        console.print("[green]✓ Web server stopped[/green]")
    except ProcessLookupError:
        console.print("[yellow]⚠ Process not found (already stopped?)[/yellow]")
    
    # Remove PID file if exists
    if PID_FILE.exists():
        PID_FILE.unlink()


def _check_port_in_use(port: int = 5000) -> Optional[int]:
    """Check if a port is in use and return the PID if found."""
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Return the first PID
            pids = result.stdout.strip().split('\n')
            return int(pids[0]) if pids else None
    except Exception:
        pass
    return None


@web.command()
@click.option(
    "--port", "-p",
    default=5000,
    type=int,
    help="Port to check (default: 5000)",
)
def status(port: int):
    """Check web server status.
    
    Example:
        youtube-miner web status
        youtube-miner web status --port 8080
    """
    # First check PID file
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            
            # Check if process is running
            try:
                os.kill(pid, 0)
                console.print(f"[green]✓ Web server is running[/green] (PID: {pid})")
                console.print(f"   [dim]Stop with:[/dim] [bold]youtube-miner web stop[/bold]")
                return
            except ProcessLookupError:
                # Process not running, remove stale PID file
                PID_FILE.unlink()
                
        except ValueError:
            PID_FILE.unlink()
    
    # Check if port is in use (server started externally)
    port_pid = _check_port_in_use(port)
    if port_pid:
        console.print(f"[green]✓ Web server is running[/green] on port {port} (PID: {port_pid})")
        console.print(f"   [dim]Stop with:[/dim] [bold]kill {port_pid}[/bold] or [bold]youtube-miner web stop[/bold]")
        # Save PID so we can stop it later
        PID_FILE.write_text(str(port_pid))
    else:
        console.print(f"[dim]Web server is [bold red]not running[/bold red] on port {port}[/dim]")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()

