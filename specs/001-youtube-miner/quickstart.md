# YouTube Miner - Quick Start Guide

## Prerequisites

- Python 3.10 or higher
- FFmpeg installed on system
- At least 8GB RAM (for model loading)
- ~5GB disk space (for models and cache)

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
```bash
# Using chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd youtube_miner
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Verify Installation

```bash
youtube-miner --version
```

---

## Three Ways to Use YouTube Miner

| Method | Best For | Command |
|--------|----------|---------|
| 🌐 **Web Frontend** | Visual interface | `youtube-miner web start` |
| 💻 **CLI Tool** | Quick tasks | `youtube-miner run URL` |
| 🐍 **Python Script** | Custom workflows | `from src.pipeline import ...` |

---

## 🌐 Option 1: Web Frontend

The easiest way - a beautiful browser-based interface!

### Start the Server

```bash
# Start in foreground
youtube-miner web start

# Start in background (daemon mode)
youtube-miner web start --background
```

### Stop the Server

```bash
# Stop the running server
youtube-miner web stop

# Check server status
youtube-miner web status
```

### Open Your Browser

Navigate to: **http://127.0.0.1:5000**

### What You Can Do

1. Paste any YouTube URL
2. Select a transcription model
3. Language is automatically detected using Whisper Turbo
4. Watch real-time progress
5. View beautiful metric visualizations
6. Browse history of processed videos

### Server Options

```bash
# Custom port
youtube-miner web start --port 8080

# Allow external connections
youtube-miner web start --host 0.0.0.0

# Enable debug mode
youtube-miner web start --debug

# Background mode with custom settings
youtube-miner web start --background --port 8080
```

---

## 💻 Option 2: CLI Tool

Command-line interface for power users and automation.

### Full Pipeline (One Command)

```bash
# Process a YouTube video
youtube-miner run "https://www.youtube.com/watch?v=VIDEO_ID"

# Specify model and output
youtube-miner run "https://www.youtube.com/watch?v=VIDEO_ID" \
    --model faster-whisper \
    --output ./results \
    --verbose
```

### Individual Commands

```bash
# Download audio only
youtube-miner download "URL" -o ./audio

# Convert to WAV
youtube-miner convert ./audio/video.m4a -o ./audio/video.wav

# Chunk with VAD
youtube-miner chunk ./audio/video.wav -o ./chunks -d 30

# Transcribe
youtube-miner transcribe ./chunks/chunk_000.wav -m faster-whisper

# Extract captions
youtube-miner captions "URL"

# Compare two texts
youtube-miner compare "reference text" "hypothesis text"
```

### List Models

```bash
youtube-miner models
```

---

## 🐍 Option 3: Python Script

For integration into your own applications.

### Basic Pipeline

```python
from src.pipeline import YouTubeMinerPipeline

# Create pipeline
pipeline = YouTubeMinerPipeline(
    output_dir="./output",
    model="faster-whisper",
    language="en",
)

# Run on a video
report = pipeline.run("https://www.youtube.com/watch?v=VIDEO_ID")

# Access results
print(f"Video: {report.video_title}")
print(f"Average WER: {report.summary.avg_wer:.2%}")
print(f"Semantic Similarity: {report.summary.avg_semantic_similarity:.2%}")
```

### Compare Texts Directly

```python
from src.comparator import HybridScore

scorer = HybridScore()
result = scorer.compare(
    reference="The quick brown fox",
    hypothesis="A quick brown fox"
)

print(f"WER: {result.wer:.2%}")
print(f"Semantic Similarity: {result.semantic_similarity:.2%}")
```

---

## Available Models

| Model | Command Flag | Speed | Accuracy | Memory |
|-------|-------------|-------|----------|--------|
| Whisper-Tiny | `whisper-tiny` | ⭐⭐⭐⭐⭐ | ⭐⭐ | ~1GB |
| Faster-Whisper | `faster-whisper` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ~2GB |
| Indic-Seamless | `indic-seamless` | ⭐⭐⭐ | ⭐⭐⭐⭐ | ~4GB |
| Whisper-Large | `whisper-large` | ⭐⭐ | ⭐⭐⭐⭐⭐ | ~6GB |

---

## Output Structure

Each video creates its own folder:

```
output/
├── VIDEO_ID_1/
│   ├── audio/          # Downloaded audio
│   ├── chunks/         # VAD-segmented chunks
│   └── report.json     # Comparison results
├── VIDEO_ID_2/
│   └── ...
```

---

## Common Issues

### FFmpeg not found

```bash
# Install FFmpeg first
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

### Out of memory

```bash
# Use a smaller model
youtube-miner run URL --model whisper-tiny
```

### SSL Certificate Error (macOS)

```bash
# Install certificates
pip install certifi
```

### No captions available

Some videos don't have auto-captions. The pipeline will still transcribe but comparison metrics will be empty.

---

## Development

### Run Tests

```bash
pytest tests/ -v --cov=src
```

### Run Linting

```bash
flake8 src/ tests/
black src/ tests/ --check
```
