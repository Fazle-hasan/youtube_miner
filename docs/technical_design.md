# Technical Design Document: YouTube Miner

> **Version:** 1.0  
> **Last Updated:** December 30, 2025  
> **Status:** Production Ready

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [API Design](#4-api-design)
5. [Performance Considerations](#5-performance-considerations)
6. [Error Handling](#6-error-handling)
7. [Testing Strategy](#7-testing-strategy)
8. [Deployment](#8-deployment)
9. [Future Enhancements](#9-future-enhancements)

---

## 1. Overview

YouTube Miner is a Python-based data pipeline for extracting audio from YouTube videos, applying Voice Activity Detection (VAD) to create clean speech chunks, transcribing using multiple open-source models, and comparing results with YouTube's auto-generated captions.

### 1.1 Objectives

- Download audio from YouTube videos using open-source tools
- Apply VAD to create ~30-second speech-only chunks
- Transcribe using multiple models (Whisper-Tiny, Faster-Whisper, Indic-Seamless, Whisper-Large)
- Compare transcriptions with YouTube captions using WER, CER, and semantic similarity
- Provide Web UI, CLI, and Python API interfaces
- Export results as JSON, SRT subtitles, or plain text

### 1.2 Constraints

- **No paid APIs** - All tools and models must be open-source
- **Memory efficient** - Support videos up to 3 hours
- **Cross-platform** - Works on Linux, macOS, and Windows

### 1.3 Technology Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Download** | yt-dlp | YouTube audio extraction |
| **Audio** | pydub, FFmpeg | Format conversion |
| **VAD** | Silero VAD | Speech detection |
| **ASR** | Whisper, Faster-Whisper | Transcription |
| **Multilingual** | Indic-Seamless | Indian languages |
| **Metrics** | jiwer | WER/CER calculation |
| **Semantic** | sentence-transformers | Embedding similarity |
| **Web** | Flask | Web interface |
| **CLI** | Click | Command-line interface |

---

## 2. System Architecture

### 2.1 Pipeline Architecture Diagram

![YouTube Miner Pipeline Architecture](architecture.png)

### 2.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           YOUTUBE MINER PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   CLI/API   │
                              │   Entry     │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │  Pipeline   │
                              │ Orchestrator│
                              └──────┬──────┘
                                     │
         ┌───────────┬───────────────┼───────────────┬───────────┐
         │           │               │               │           │
    ┌────▼────┐ ┌────▼────┐    ┌────▼────┐    ┌────▼────┐ ┌────▼────┐
    │Download │ │ Convert │    │   VAD   │    │Transcribe│ │ Compare │
    │ Module  │ │ Module  │    │ Module  │    │  Module  │ │ Module  │
    └────┬────┘ └────┬────┘    └────┬────┘    └────┬────┘ └────┬────┘
         │           │               │               │           │
    ┌────▼────┐ ┌────▼────┐    ┌────▼────┐    ┌────▼────┐ ┌────▼────┐
    │ yt-dlp  │ │  pydub  │    │ Silero  │    │ Whisper │ │  jiwer  │
    │         │ │ FFmpeg  │    │   VAD   │    │  Models │ │sentence │
    └─────────┘ └─────────┘    └─────────┘    └─────────┘ │transform│
                                                          └─────────┘
```

### 2.3 Data Flow

```
YouTube URL
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Download                                                            │
│ Input:  YouTube URL                                                          │
│ Output: AudioFile (MP3)                                                      │
│ Tool:   yt-dlp                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: Convert                                                             │
│ Input:  AudioFile (any format)                                               │
│ Output: AudioFile (WAV, 16kHz, mono)                                        │
│ Tool:   pydub + FFmpeg                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: VAD Chunking                                                        │
│ Input:  WAV AudioFile                                                        │
│ Output: List[Chunk] (~30 seconds each, speech only)                         │
│ Tool:   Silero VAD                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ├───────────────────────────────────────────────────────────┐
    ▼                                                           ▼
┌─────────────────────────────────────────┐   ┌─────────────────────────────────┐
│ STAGE 4a: Transcription                 │   │ STAGE 4b: Caption Extraction    │
│ Input:  List[Chunk]                     │   │ Input:  YouTube URL             │
│ Output: List[Transcript]                │   │ Output: List[Caption]           │
│ Tools:  Whisper/Faster-Whisper          │   │ Tool:   youtube-transcript-api  │
└─────────────────────────────────────────┘   └─────────────────────────────────┘
    │                                                           │
    ▼                                                           │
┌─────────────────────────────────────────┐                     │
│ STAGE 5: Deduplication                  │                     │
│ Input:  List[Transcript]                │                     │
│ Output: List[Transcript] (cleaned)      │                     │
│ Tool:   N-gram analysis                 │                     │
└─────────────────────────────────────────┘                     │
    │                                                           │
    └───────────────────────────┬───────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 6: Normalization                                                       │
│ Input:  Transcripts + Captions                                               │
│ Output: Normalized text pairs                                                │
│ Tool:   TextNormalizer                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 7: Comparison                                                          │
│ Input:  Normalized Transcripts + Captions                                    │
│ Output: List[ComparisonResult] (WER, CER, Semantic, Hybrid)                 │
│ Tools:  jiwer, sentence-transformers                                         │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 8: Report Generation                                                   │
│ Input:  List[ComparisonResult] + metadata                                    │
│ Output: PipelineReport (JSON)                                                │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 9: Export Options                                                      │
│ Output: JSON Report, SRT Subtitles, TXT Transcript                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Design

### 3.1 Data Models

```python
@dataclass
class AudioFile:
    path: Path
    format: str
    duration: float
    sample_rate: int
    channels: int
    source_url: Optional[str]

@dataclass
class Chunk:
    index: int
    audio_path: Path
    start_time: float
    end_time: float
    duration: float
    is_speech: bool
    confidence: float

@dataclass
class Transcript:
    text: str
    model_name: str
    chunk_index: int
    confidence: float
    language: str
    processing_time: float
    raw_text: str
    deduplicated: bool

@dataclass
class ComparisonResult:
    chunk_index: int
    normalized_transcript: str
    normalized_caption: str
    wer: float
    cer: float
    semantic_similarity: float
    hybrid_score: float
```

### 3.2 Module Specifications

#### 3.2.1 Downloader Module

```
src/downloader/
├── __init__.py
├── youtube.py      # YouTubeDownloader class
└── captions.py     # CaptionExtractor class
```

**YouTubeDownloader**
- Uses yt-dlp to download best audio quality (MP3)
- Extracts video metadata (title, duration, etc.)
- Handles various URL formats (standard, short, embed)

**CaptionExtractor**
- Uses youtube-transcript-api for reliable caption extraction
- Supports auto-generated and manual captions
- Handles multilingual captions (Hindi, Tamil, etc.)
- Aligns captions to chunk timestamps

#### 3.2.2 Converter Module

```
src/converter/
├── __init__.py
└── audio.py        # AudioConverter class
```

**AudioConverter**
- Converts any audio format to WAV
- Resamples to 16kHz (required by Silero VAD)
- Converts to mono channel
- Uses pydub with FFmpeg backend

#### 3.2.3 VAD Module

```
src/vad/
├── __init__.py
└── chunker.py      # VADChunker class
```

**VADChunker**
- Uses Silero VAD for speech detection
- Creates ~30-second speech-only chunks
- Removes silence and non-speech audio
- Maintains timestamp metadata for SRT generation

#### 3.2.4 Transcriber Module

```
src/transcriber/
├── __init__.py           # Factory and registry
├── base.py               # BaseTranscriber abstract class
├── whisper_tiny.py       # WhisperTinyTranscriber
├── faster_whisper.py     # FasterWhisperTranscriber
├── indic_seamless.py     # IndicSeamlessTranscriber
└── whisper_large.py      # WhisperLargeTranscriber
```

**Model Comparison**

| Model | Speed | Memory | Accuracy | Best For |
|-------|-------|--------|----------|----------|
| Whisper-Tiny | ⭐⭐⭐⭐⭐ | ~1GB | ~70%+ | Quick testing |
| Faster-Whisper | ⭐⭐⭐⭐⭐ | ~2GB | ~80-90% | **Production default** |
| Indic-Seamless | ⭐⭐⭐ | ~4GB | ~75-85% | Indian languages |
| Whisper-Large | ⭐⭐ | ~6GB | ~95%+ | Maximum accuracy |

#### 3.2.5 Deduplicator Module

```
src/deduplicator/
├── __init__.py
└── ngram.py        # NGramDeduplicator class
```

**NGramDeduplicator**
- Removes consecutive duplicate words
- Detects and removes repeated n-grams (bigrams, trigrams)
- Preserves original text as `raw_text`
- Case-insensitive matching

#### 3.2.6 Comparator Module

```
src/comparator/
├── __init__.py
├── normalizer.py    # TextNormalizer
├── wer.py           # WERCalculator
├── cer.py           # CERCalculator
├── semantic.py      # SemanticSimilarity
└── hybrid.py        # HybridScore (SeMaScore)
```

**Metrics**

1. **WER (Word Error Rate)**: `(Substitutions + Deletions + Insertions) / Total Words`
2. **CER (Character Error Rate)**: Same as WER at character level
3. **Semantic Similarity**: Cosine similarity of sentence embeddings
4. **Hybrid SeMaScore**: `0.5 × (1 - WER) + 0.5 × Semantic Similarity`

---

## 4. API Design

### 4.1 Python API

```python
from src.pipeline import YouTubeMinerPipeline

# Full pipeline
pipeline = YouTubeMinerPipeline(
    output_dir="./output",
    model="faster-whisper",
    language="en",
)
report = pipeline.run("https://youtube.com/watch?v=...")

# Access results
print(f"Hybrid Score: {report.summary.avg_hybrid_score:.2%}")
```

### 4.2 Individual Components

```python
from src.downloader import YouTubeDownloader, CaptionExtractor
from src.converter import AudioConverter
from src.vad import VADChunker
from src.transcriber import get_transcriber
from src.comparator import HybridScore

downloader = YouTubeDownloader()
audio = downloader.download("URL")

converter = AudioConverter()
wav = converter.convert(audio)

chunker = VADChunker()
chunks = chunker.chunk(wav)

transcriber = get_transcriber("faster-whisper")
transcripts = transcriber.transcribe_chunks(chunks)

scorer = HybridScore()
result = scorer.compare(caption, transcript)
```

### 4.3 CLI Interface

```bash
# Full pipeline
youtube-miner run "URL" --model faster-whisper --output ./results

# Individual commands
youtube-miner download "URL" -o ./audio
youtube-miner convert audio.m4a -o audio.wav
youtube-miner chunk audio.wav -o ./chunks
youtube-miner transcribe chunk.wav -m faster-whisper
youtube-miner captions "URL"
youtube-miner compare "text1" "text2"
youtube-miner models  # List available models
```

### 4.4 Web Interface

```bash
# Start server
youtube-miner web start

# Start in background
youtube-miner web start --background

# Stop server
youtube-miner web stop
```

---

## 5. Performance Considerations

### 5.1 Memory Management

- **Streaming download**: Don't load entire audio into memory
- **Chunk processing**: Process one chunk at a time
- **Model unloading**: Free memory after transcription via `unload_model()`
- **Temporary files**: Clean up intermediate files automatically

### 5.2 Processing Time Estimates (1-hour audio)

| Stage | Time |
|-------|------|
| Download | 2-5 min |
| Conversion | 1-2 min |
| VAD Chunking | 2-3 min |
| Transcription (Faster-Whisper) | 10-15 min |
| Caption Extraction | <1 min |
| Comparison | 2-3 min |
| **Total** | **~20-30 min** |

### 5.3 GPU Acceleration

- Faster-Whisper supports CUDA for 4x speed improvement
- Indic-Seamless can use GPU but falls back to CPU for stability
- Set `device="cuda"` for GPU acceleration when available

---

## 6. Error Handling

### 6.1 Expected Errors

| Error | Cause | Handling |
|-------|-------|----------|
| Invalid URL | Malformed YouTube URL | Validate before processing |
| Private Video | Video not accessible | Return clear error message |
| No Captions | Video lacks auto-captions | Skip comparison, continue with transcription |
| Memory Error | Model too large | Suggest smaller model, fallback to CPU |
| Network Error | Connection issues | Retry with backoff |

### 6.2 Logging

- Structured logging with levels (DEBUG, INFO, WARNING, ERROR)
- Progress reporting for long operations
- Performance timing for each stage
- Log files stored in `output/logs/`

---

## 7. Testing Strategy

YouTube Miner includes **100+ unit tests** and integration tests to ensure robustness and reliability.

### 7.1 Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests
│   ├── test_captions.py        # 8 tests
│   ├── test_cli.py             # 14 tests
│   ├── test_comparator.py      # 15 tests
│   ├── test_converter.py       # 6 tests
│   ├── test_deduplicator.py    # 9 tests
│   ├── test_downloader.py      # 8 tests
│   ├── test_models.py          # 17 tests
│   ├── test_normalizer.py      # 8 tests
│   ├── test_transcriber.py     # 13 tests
│   └── test_vad.py             # 7 tests
└── integration/
    └── test_pipeline.py        # 4 tests
```

### 7.2 Test Coverage by Component

| Component | Tests | Coverage Areas |
|-----------|-------|----------------|
| Data Models | 17 | AudioFile, Chunk, Transcript, Caption, ComparisonResult |
| Comparator | 15 | WER, CER, Semantic Similarity, Hybrid Score |
| Normalizer | 8 | Lowercase, punctuation, contractions, numbers |
| Deduplicator | 9 | N-gram removal, transcript processing |
| Downloader | 8 | URL parsing, video info extraction |
| Captions | 8 | VTT parsing, timestamp handling |
| Converter | 6 | Format conversion, audio metadata |
| Transcriber | 13 | Model registry, all transcriber classes |
| VAD | 7 | Speech detection, chunk creation |
| CLI | 14 | All commands, error handling |
| Pipeline | 4 | End-to-end integration |

### 7.3 Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_comparator.py

# Skip slow/network tests
pytest -m "not slow and not network"

# Verbose output
pytest -v
```

### 7.4 Test Fixtures

Shared fixtures in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `temp_dir` | Temporary directory for test files |
| `sample_audio_file` | Sample AudioFile object |
| `sample_chunk` | Single Chunk object |
| `sample_chunks` | List of 3 Chunk objects |
| `sample_transcript` | Sample Transcript object |
| `sample_caption` | Sample Caption object |
| `sample_comparison_result` | Sample ComparisonResult object |

### 7.5 Coverage Targets

- **Minimum 80% code coverage** across all modules
- **100% coverage** for data models and metric calculations
- **All public APIs** have corresponding tests
- **Edge cases** explicitly tested (empty inputs, invalid data)
- **Mocked external dependencies** for reliable testing

---

## 8. Deployment

### 8.1 Requirements

- Python 3.10+
- FFmpeg (system installation)
- 8GB+ RAM recommended
- ~5GB disk space for models

### 8.2 Installation

```bash
# Clone repository
git clone <repository-url>
cd youtube_miner

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 8.3 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | For indic-seamless | Hugging Face authentication token |

### 8.4 Output Directory Structure

```
output/
├── VIDEO_ID_faster-whisper/
│   ├── audio/
│   │   └── VIDEO_ID.mp3
│   ├── chunks/
│   │   ├── chunk_000.wav
│   │   ├── chunk_001.wav
│   │   └── ...
│   ├── report.json
│   ├── transcript.srt
│   └── transcript.txt
└── logs/
    └── web_server.log
```

---

## 9. Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| Speaker Diarization | Add pyannote for speaker identification | High |
| Real-time Processing | Stream processing for live content | Medium |
| Batch Processing | Process multiple videos in parallel | Medium |
| Custom Vocabulary | Domain-specific term handling | Low |
| Noise Reduction | Audio preprocessing for better accuracy | Low |
| Docker Support | Containerized deployment | Medium |

---

## 📚 Additional Resources

- **README.md** - Quick start guide and usage instructions
- **architecture.png** - Visual pipeline diagram
- **architecture.drawio** - Editable diagram (open in draw.io)

---

*Document maintained by YouTube Miner Development Team*  
*Last updated: December 30, 2025*
