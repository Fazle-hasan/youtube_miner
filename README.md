# YouTube Miner ⛏️🎬

A powerful Python data pipeline for YouTube audio extraction, Voice Activity Detection (VAD) chunking, multi-model transcription, and automated comparison with YouTube captions.

**100% Open Source • No Paid APIs • Cross-Platform**

---

## 🏗️ Architecture

![YouTube Miner Pipeline Architecture](docs/architecture.png)

### Pipeline Stages Explained

| Stage | Component | Description |
|-------|-----------|-------------|
| **Stage 1** | 📥 Download | Extract audio from YouTube using `yt-dlp` (MP3 format) |
| **Stage 2** | 🔊 Convert | Convert to WAV format (16kHz, mono) using `pydub` + FFmpeg |
| **Stage 3** | 🎯 VAD Chunk | Split into ~30s speech-only segments using Silero VAD |
| **Stage 4a** | 🗣️ Transcribe | Transcribe chunks using selected ASR model |
| **Stage 4b** | 📝 Captions | Extract YouTube auto-captions (parallel path) via `youtube-transcript-api` |
| **Stage 5** | 🔁 Deduplicate | Remove repetitive phrases using N-gram analysis |
| **Stage 6** | 📋 Normalize | Text preprocessing for fair comparison |
| **Stage 7** | ⚖️ Compare | Calculate WER, CER, Semantic Similarity, Hybrid Score |
| **Stage 8** | 📄 Report | Generate JSON report with per-chunk and summary metrics |
| **Stage 9** | 📥 Download | Export results as JSON Report, SRT Subtitles, or TXT Transcript |

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- FFmpeg
- 8GB+ RAM

### Step 1: Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
choco install ffmpeg
```

### Step 2: Install YouTube Miner

```bash
# Clone repository
git clone <repository-url>
cd youtube_miner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Step 3: Verify Installation

```bash
# Check CLI is available
youtube-miner --help

# Verify FFmpeg
ffmpeg -version
```

---

## 🌐 Quick Start: Web Interface

The easiest way to use YouTube Miner! Perfect for beginners.

### Start the Server

```bash
# Start web interface
youtube-miner web start

# Start in background
youtube-miner web start --background

# Custom host/port
youtube-miner web start --host 0.0.0.0 --port 8080
```

### Use the Web UI

1. **Open browser** → `http://127.0.0.1:5000`
2. **Paste** any YouTube URL
3. **Select** transcription model (recommend: `faster-whisper`)
4. **Select** language (English, Hindi, Auto)
5. **Click Process** and watch real-time progress!
6. **View results** with expandable chunk comparisons
7. **Download** as JSON, SRT, or TXT

### Features

- ✅ Paste any YouTube URL
- ✅ Select transcription model
- ✅ Real-time progress tracking
- ✅ Beautiful metric visualization
- ✅ Download JSON, SRT, or TXT files
- ✅ Processing history

### Stop the Server

```bash
youtube-miner web stop
```

---

## 💻 CLI Tool

For automation and scripting workflows.

### Full Pipeline

```bash
# Process a video
youtube-miner run "https://www.youtube.com/watch?v=VIDEO_ID"

# Specify model and output
youtube-miner run "URL" --model faster-whisper --output ./results
```

### Individual Commands

```bash
# Download audio
youtube-miner download "URL" -o ./audio

# Convert to WAV
youtube-miner convert audio.m4a -o audio.wav

# Create speech chunks
youtube-miner chunk audio.wav -o ./chunks

# Transcribe
youtube-miner transcribe chunk.wav -m faster-whisper

# Extract captions
youtube-miner captions "URL"

# Compare texts
youtube-miner compare "reference text" "hypothesis text"

# List models
youtube-miner models
```

---

## 🐍 Python API

For custom workflows and integration.

### Basic Usage

```python
from src.pipeline import YouTubeMinerPipeline

# Create pipeline
pipeline = YouTubeMinerPipeline(
    output_dir="./output",
    model="faster-whisper",
    language="en",
)

# Process video
report = pipeline.run("https://www.youtube.com/watch?v=VIDEO_ID")

# Access results
print(f"Video: {report.video_title}")
print(f"Hybrid Score: {report.summary.avg_hybrid_score:.2%}")
```

### Using Individual Components

```python
from src.downloader import YouTubeDownloader
from src.transcriber import get_transcriber
from src.comparator import HybridScore

# Download
downloader = YouTubeDownloader(output_dir="./output")
audio, info = downloader.download_with_info(url)

# Transcribe
transcriber = get_transcriber("faster-whisper")
transcripts = transcriber.transcribe_chunks(chunks)

# Compare
scorer = HybridScore()
result = scorer.compare(reference, hypothesis)
print(f"Hybrid Score: {result.hybrid_score:.2%}")
```

---

## 🤖 Model Comparison & Recommendations

YouTube Miner supports 4 open-source transcription models. Here's our analysis based on extensive testing:

### Quick Comparison

| Model | Speed | Accuracy | Memory | Best For |
|-------|-------|----------|--------|----------|
| **whisper-tiny** | ⚡⚡⚡⚡⚡ | ~70%+ | ~1GB | Quick drafts, testing |
| **faster-whisper** | ⚡⚡⚡⚡⚡ | ~80-90% | ~2GB | **Production default** ✅ |
| **indic-seamless** | ⚡⚡⚡ | ~75-85% | ~4GB | Hindi & Indian languages |
| **whisper-large** | ⚡ | ~95%+ | ~6GB | Maximum accuracy (GPU) |

### Detailed Model Analysis

#### ⚡ Whisper-Tiny
- **Hybrid Score:** 70%+ on basic English videos
- **Speed:** Fastest of all models
- **Use Case:** Quick previews, resource-constrained environments
- **Trade-off:** Lower accuracy, may miss complex speech
- **Recommendation:** Use for testing or when speed is critical

#### ⭐ Faster-Whisper (RECOMMENDED DEFAULT)
- **Hybrid Score:** 80-90% on clear English videos
- **Speed:** 4x faster than original Whisper
- **Use Case:** Production transcription, general English content
- **Trade-off:** Best balance of speed and accuracy
- **Recommendation:** **Default choice for most use cases**

#### 🇮🇳 Indic-Seamless
- **Hybrid Score:** Good results for Hindi and Indian languages
- **Speed:** Moderate (slower than Whisper models)
- **Use Case:** Hindi, Tamil, Telugu, Bengali, Marathi, and 100+ languages
- **Trade-off:** Slower processing, requires HF_TOKEN
- **Recommendation:** Best choice for Indian language content

#### 🎯 Whisper-Large
- **Hybrid Score:** Highest accuracy available (95%+)
- **Speed:** Very slow processing
- **Use Case:** When accuracy is absolutely critical
- **Trade-off:** Requires good GPU, long processing time
- **Recommendation:** Use with GPU for maximum quality output

### Model Selection Guide

| Content Type | Recommended Model | Expected Score |
|--------------|-------------------|----------------|
| Clear English (interviews, lectures) | `faster-whisper` | 80-90% |
| Casual English (podcasts, vlogs) | `faster-whisper` | 70-80% |
| Hindi/Indian languages | `indic-seamless` | 75-85% |
| Maximum accuracy needed | `whisper-large` | 90-95%+ |
| Quick draft/preview | `whisper-tiny` | 70%+ |

### Using Indic-Seamless (Multilingual)

The `indic-seamless` model requires Hugging Face authentication:

```bash
# Set your HF token
export HF_TOKEN=your_huggingface_token

# Use the model
youtube-miner run "URL" --model indic-seamless --language hi
```

Get your token at: https://huggingface.co/settings/tokens

---

## 📊 Understanding Comparison Metrics

### Metrics Overview

| Metric | Description | Range | Goal |
|--------|-------------|-------|------|
| **WER** | Word Error Rate | 0-100%+ | Lower = Better |
| **CER** | Character Error Rate | 0-100%+ | Lower = Better |
| **Semantic** | Meaning similarity (embeddings) | 0-100% | Higher = Better |
| **Hybrid** | SeMaScore (WER + Semantic) | 0-100% | Higher = Better |

### Hybrid Score Interpretation

| Score Range | Quality | Action |
|-------------|---------|--------|
| 85-100% | 🟢 Excellent | Production ready |
| 70-85% | 🟢 Good | Minor review recommended |
| 55-70% | 🟡 Acceptable | Review needed |
| 40-55% | 🟠 Poor | Significant editing required |
| <40% | 🔴 Very Poor | Manual transcription recommended |

### Why Hybrid Score?

- ❌ **WER alone:** Penalizes paraphrasing unfairly
- ❌ **Semantic alone:** Ignores word-level accuracy
- ✅ **Hybrid Score:** Balances both for real-world quality

**Example:**
| Reference | Hypothesis | WER | Semantic | Hybrid |
|-----------|------------|-----|----------|--------|
| "I'm going to the store" | "I am heading to the shop" | 60% | 95% | 67.5% |

The meaning is preserved even when words differ!

---

## 📁 Output Structure

```
output/
├── VIDEO_ID_faster-whisper/
│   ├── audio/              # Downloaded audio
│   ├── chunks/             # VAD segments
│   ├── report.json         # Full analysis
│   ├── transcript.srt      # Subtitles
│   └── transcript.txt      # Plain text
└── VIDEO_ID_whisper-large/ # Same video, different model
```

### Download Options

After processing, download:
- **📊 JSON Report** - Full analysis with all metrics
- **🎬 SRT File** - Timed subtitles
- **📄 TXT File** - Plain text transcript

---

## 📋 Real-World Examples

### Example 1: Long-Form English Content

Here's an actual output from processing a 63-minute NVIDIA CEO interview using `faster-whisper`:

#### Video Details

| Field | Value |
|-------|-------|
| **Video** | [NVIDIA CEO Jensen Huang's Vision for the Future](https://www.youtube.com/watch?v=7ARBJQn6QkM) |
| **Duration** | 63 minutes (3,783 seconds) |
| **Model Used** | `faster-whisper` |
| **Total Chunks** | 96 segments |
| **Processing Time** | 308 seconds (~5 minutes) |

#### Summary Results

| Metric | Score | Interpretation |
|--------|-------|----------------|
| **Average WER** | 19.7% | 🟢 Good word accuracy |
| **Average CER** | 17.2% | 🟢 Good character accuracy |
| **Semantic Similarity** | 86.6% | 🟢 Excellent meaning preservation |
| **Hybrid Score (SeMaScore)** | 83.4% | 🟢 Good overall quality |

#### Sample Chunk Comparisons

**Chunk 0 - Excellent Match (95.1% Hybrid Score)**

| Source | Text |
|--------|------|
| **Transcript** | "at some point you have to believe something we have reinvented computing as we know it what is the vision for what you see coming next..." |
| **YouTube Caption** | "at some point you have to believe something we have reinvented computing as we know it what is the vision for what you see coming next..." |

| WER | CER | Semantic | Hybrid |
|-----|-----|----------|--------|
| 3.7% | 1.8% | 93.9% | **95.1%** |

**Chunk 13 - High Quality (96.3% Hybrid Score)**

| Source | Text |
|--------|------|
| **Transcript** | "a couple of researchers at mass general were using it to do ct reconstruction they were using our graphics processors for that reason and inspired us..." |
| **YouTube Caption** | "a couple of researchers at mass general were using it to do ct reconstruction they were using our graphics processors for that reason and it inspired us..." |

| WER | CER | Semantic | Hybrid |
|-----|-----|----------|--------|
| 4.8% | 4.4% | 97.4% | **96.3%** |

---

### Example 2: Short-Form English Content

Here's another example from a 5.5-minute tech career advice video:

#### Video Details

| Field | Value |
|-------|-------|
| **Video** | [Don't Waste 2026 on the Wrong Career (ML vs AI Engineer)](https://www.youtube.com/watch?v=cqDQV5g7zHo) |
| **Duration** | 5.6 minutes (337 seconds) |
| **Model Used** | `faster-whisper` |
| **Total Chunks** | 8 segments |
| **Processing Time** | 32 seconds |

#### Summary Results

| Metric | Score | Interpretation |
|--------|-------|----------------|
| **Average WER** | 11.9% | 🟢 Excellent word accuracy |
| **Average CER** | 9.8% | 🟢 Excellent character accuracy |
| **Semantic Similarity** | 90.7% | 🟢 Excellent meaning preservation |
| **Hybrid Score (SeMaScore)** | 89.4% | 🟢 Excellent overall quality |

#### Sample Chunk Comparisons

**Chunk 0 - Excellent Match (94.7% Hybrid Score)**

| Source | Text |
|--------|------|
| **Transcript** | "what is the best move for the coming year becoming a machine learning engineer or an ai engineer well i help people land ai engineering rules and the first step is always figuring out if that is actually what you want..." |
| **YouTube Caption** | "what is the best move for the coming year becoming a machine learning engineer or an ai engineer well i help people land ai engineering roles and the first step is always figuring out if that is actually what you want..." |

| WER | CER | Semantic | Hybrid |
|-----|-----|----------|--------|
| 8.3% | 7.3% | 97.6% | **94.7%** |

> 💡 **Key Insight:** Shorter videos typically achieve higher accuracy scores because:
> - Less audio variation and background noise
> - More consistent speaking pace
> - Better alignment between transcript and caption chunks

---

### Example 3: Multilingual Content (Hindi)

Here's an example using `indic-seamless` model for Hindi language content:

#### Video Details

| Field | Value |
|-------|-------|
| **Video** | [Ind-Pak War, Indian Army Operations, Weapons & Kargil - Capt Yashika Tyagi](https://www.youtube.com/watch?v=oHry5RRI4KU) |
| **Duration** | 67 minutes (4,012 seconds) |
| **Model Used** | `indic-seamless` |
| **Total Chunks** | 91 segments |
| **Processing Time** | 5,984 seconds (~100 minutes) |

#### Summary Results

| Metric | Score | Interpretation |
|--------|-------|----------------|
| **Average WER** | 53.9% | 🟡 Moderate word accuracy |
| **Average CER** | 40.9% | 🟡 Moderate character accuracy |
| **Semantic Similarity** | 89.4% | 🟢 Excellent meaning preservation |
| **Hybrid Score (SeMaScore)** | 67.8% | 🟡 Acceptable overall quality |

#### Sample Chunk (Hindi Transcription)

**Chunk 8 - Good Match (74.0% Hybrid Score)**

| Source | Text |
|--------|------|
| **Transcript** | "आज जब हम आत्मनिर्भर भारत से कई प्रकार के आर.एंड.डी करके चीजें बना रहे हैं तो आप देखते हैं भारत की जो अर्थव्यवस्था है जो पहले डिफेंस की वजह से हम सिर्फ एक बायर्स इकोनॉमी थे..." |
| **YouTube Caption** | "जब कारगिल हुआ हमने रियलाइज किया कि गैप है एम्यूनिशन हम इक्विपमेंट्स और आज जब हम आत्मनिर्भर भारत से हम कई तरीके के आरएड करके चीजें बना रहे हैं..." |

| WER | CER | Semantic | Hybrid |
|-----|-----|----------|--------|
| 47.3% | 36.4% | 95.3% | **74.0%** |

#### Key Insights for Multilingual Content

> 💡 **Why are WER/CER higher for Hindi?**
> - **Code-switching**: Hindi videos often mix Hindi and English words
> - **Romanization differences**: Different ways to represent Hindi in text
> - **Script variations**: Devanagari script handling between caption and transcript
> - **Speaking style**: Conversational Hindi with regional variations
>
> **However, Semantic Similarity remains high (89.4%)** because the *meaning* is well-preserved even when exact words differ!

---

### Summary: Model Comparison Results

| Content Type | Model | WER | Semantic | Hybrid | Processing |
|--------------|-------|-----|----------|--------|------------|
| English (Long) | `faster-whisper` | 19.7% | 86.6% | **83.4%** | 5 min |
| English (Short) | `faster-whisper` | 11.9% | 90.7% | **89.4%** | 32 sec |
| Hindi (Long) | `indic-seamless` | 53.9% | 89.4% | **67.8%** | 100 min |

> 🎯 **Recommendation**: Use `faster-whisper` for English content, `indic-seamless` for Hindi/Indian languages. Expect higher WER for multilingual content but good semantic preservation.

---

## 🧪 Testing

The project includes 100+ unit tests for robustness and reliability.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Skip slow tests
pytest tests/ -m "not slow"
```

---

## 📂 Project Structure

```
youtube_miner/
├── src/
│   ├── cli.py              # Command-line interface
│   ├── web/                # Flask web frontend
│   ├── downloader/         # YouTube download & captions
│   ├── converter/          # Audio conversion
│   ├── vad/                # Voice Activity Detection
│   ├── transcriber/        # Multi-model ASR
│   ├── deduplicator/       # N-gram removal
│   ├── comparator/         # WER, CER, Semantic metrics
│   ├── pipeline/           # Orchestration
│   └── models/             # Data classes
├── tests/                  # Unit & integration tests
├── docs/                   # Documentation
│   ├── architecture.png    # Pipeline diagram
│   ├── architecture.drawio # Editable diagram
│   └── technical_design.md # Technical documentation
├── requirements.txt
└── pyproject.toml
```

---

## ❓ Troubleshooting

### FFmpeg not found
```bash
ffmpeg -version  # Check installation
brew install ffmpeg  # macOS
```

### Out of memory
```bash
# Use smaller model
youtube-miner run URL --model whisper-tiny
```

### SSL Certificate Error (macOS)
```bash
pip install certifi
```

---

## 📖 Technical Documentation

For detailed technical information, check out:

- **[Technical Design Document](docs/technical_design.md)** - Complete system architecture, component design, API specifications, and testing strategy
- **[Architecture Diagram](docs/architecture.png)** - Visual pipeline flow

---

## 📜 License

MIT License

---

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube download
- [Silero VAD](https://github.com/snakers4/silero-vad) - Voice Activity Detection
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Optimized ASR
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [ai4bharat](https://github.com/ai4bharat) - Indic-Seamless model
- [jiwer](https://github.com/jitsi/jiwer) - WER/CER calculation
- [Sentence-Transformers](https://www.sbert.net/) - Semantic similarity
- [Flask](https://flask.palletsprojects.com/) - Web framework
