# Implementation Plan: YouTube Miner

**Branch**: `001-youtube-miner` | **Date**: 2024-12-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-youtube-miner/spec.md`

## Summary

Build a Python-based data pipeline that downloads YouTube audio, applies Voice Activity Detection to create clean 30-second speech chunks, transcribes using open-source models (Whisper-Tiny, Faster-Whisper, ai4bharat/indic-seamless), and compares results with YouTube auto-captions using WER, CER, and semantic similarity metrics.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: 
- yt-dlp (YouTube download)
- silero-vad / torch (Voice Activity Detection)
- faster-whisper / openai-whisper (Transcription)
- transformers (ai4bharat models)
- jiwer (WER/CER calculation)
- sentence-transformers (Semantic similarity)
- pydub / librosa (Audio processing)


**Storage**: Local filesystem (WAV files, JSON outputs)  
**Testing**: pytest with pytest-cov  
**Target Platform**: Linux/macOS/Windows (cross-platform CLI)  
**Project Type**: Single Python package with CLI  
**Performance Goals**: Process 1-hour audio in <30 minutes  
**Constraints**: No paid APIs, open-source only, memory efficient for long videos  
**Scale/Scope**: Single-user CLI tool, videos up to 3 hours

## Comparison Metrics

| Metric | Purpose |
|--------|---------|
| Word Error Rate (WER) | Word-level accuracy |
| Character Error Rate (CER) | Character-level accuracy |
| Semantic Similarity | Meaning preservation (cosine similarity) |
| Hybrid metrics like SeMaScore | Newer metrics combine error rate with semantic similarity to better match human judgments of transcript quality |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Open-Source First | ✅ PASS | All libraries are open-source (yt-dlp, silero, whisper) |
| Modular Pipeline | ✅ PASS | Each stage is independent module |
| Test-First | ✅ PASS | pytest structure planned with >80% coverage |
| Data Quality | ✅ PASS | Normalization, n-gram dedup, 3 metrics defined |
| Simplicity | ✅ PASS | CLI-first, no unnecessary abstractions |

## Project Structure

### Documentation (this feature)

```text
specs/001-youtube-miner/
├── plan.md              # This file
├── spec.md              # User stories and requirements
├── quickstart.md        # Setup and usage guide
├── contracts/           # API contracts (if any)
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
youtube_miner/
├── src/
│   ├── __init__.py
│   ├── cli.py                    # Main CLI entry point
│   ├── downloader/
│   │   ├── __init__.py
│   │   ├── youtube.py            # yt-dlp wrapper
│   │   └── captions.py           # YouTube caption extraction
│   ├── converter/
│   │   ├── __init__.py
│   │   └── audio.py              # WAV conversion (16kHz, mono)
│   ├── vad/
│   │   ├── __init__.py
│   │   └── chunker.py            # Silero VAD + 30s chunking
│   ├── transcriber/
│   │   ├── __init__.py
│   │   ├── base.py               # Base transcriber interface
│   │   ├── whisper_tiny.py       # Whisper-Tiny model
│   │   ├── faster_whisper.py     # Faster-Whisper model
│   │   └── indic_seamless.py     # ai4bharat model
│   ├── deduplicator/
│   │   ├── __init__.py
│   │   └── ngram.py              # N-gram repetition removal
│   ├── comparator/
│   │   ├── __init__.py
│   │   ├── normalizer.py         # Text normalization
│   │   ├── wer.py                # Word Error Rate
│   │   ├── cer.py                # Character Error Rate
│   │   ├── semantic.py           # Embedding cosine similarity
│   │   └── hybrid.py             # SeMaScore hybrid metric
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── orchestrator.py       # End-to-end pipeline
│   └── models/
│       ├── __init__.py
│       ├── audio.py              # AudioFile, Chunk dataclasses
│       ├── transcript.py         # Transcript dataclass
│       └── comparison.py         # ComparisonResult dataclass
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Shared fixtures
│   ├── unit/
│   │   ├── test_downloader.py
│   │   ├── test_converter.py
│   │   ├── test_vad.py
│   │   ├── test_transcriber.py
│   │   ├── test_deduplicator.py
│   │   ├── test_comparator.py
│   │   └── test_normalizer.py
│   └── integration/
│       ├── test_pipeline.py
│       └── test_cli.py
├── docs/
│   └── technical_design.md       # Architecture diagrams
├── requirements.txt
├── pyproject.toml
├── setup.py
└── README.md
```

**Structure Decision**: Single Python package structure with modular sub-packages for each pipeline stage. CLI as primary interface.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           YOUTUBE MINER PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   YouTube    │    │    Audio     │    │     WAV      │    │    Speech    │
│     URL      │───▶│   Download   │───▶│  Conversion  │───▶│   Chunks     │
│              │    │   (yt-dlp)   │    │  (16kHz/mono)│    │  (Silero VAD)│
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                    │
                    ┌───────────────────────────────────────────────┘
                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         TRANSCRIPTION MODULE                                  │
├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
│   Whisper-Tiny   │  Faster-Whisper  │ Indic-Seamless   │  Whisper-Large     │
│                  │   (Optimized)    │  (Multilingual)  │  (High Quality)    │
└──────────────────┴──────────────────┴──────────────────┴────────────────────┘
                    │
                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Raw        │    │   N-gram     │    │   Text       │    │  Comparison  │
│ Transcripts  │───▶│ Dedup        │───▶│ Normalization│───▶│   Metrics    │
│              │    │              │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                    │
                    ┌───────────────────────────────────────────────┘
                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         COMPARISON METRICS                                    │
├────────────────┬────────────────┬─────────────────────┬─────────────────────┤
│   WER          │   CER          │ Semantic Similarity │  SeMaScore          │
│ (Word Error)   │ (Char Error)   │ (Embedding Cosine)  │  (Hybrid Metric)    │
└────────────────┴────────────────┴─────────────────────┴─────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT                                           │
├───────────────────────────────┬──────────────────────────────────────────────┤
│   JSON Report                 │   Human-Readable Summary                     │
│   (Structured Data)           │   (Console/Markdown)                         │
└───────────────────────────────┴──────────────────────────────────────────────┘
```

## Data Flow

```
YouTube URL (str)
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Download                                                            │
│ Input:  YouTube URL                                                          │
│ Output: AudioFile(path, format='webm/m4a', duration, sample_rate)           │
│ Tool:   yt-dlp                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: Convert                                                             │
│ Input:  AudioFile (any format)                                               │
│ Output: AudioFile(path, format='wav', sample_rate=16000, channels=1)        │
│ Tool:   pydub / ffmpeg                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: VAD Chunking                                                        │
│ Input:  WAV AudioFile                                                        │
│ Output: List[Chunk(audio_data, start_time, end_time, duration=~30s, index)] │
│ Tool:   Silero VAD + custom chunking logic                                   │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ├────────────────────────────────────────────────────┐
    ▼                                                    ▼
┌─────────────────────────────────────────┐  ┌─────────────────────────────────┐
│ STAGE 4a: Transcription                 │  │ STAGE 4b: Caption Extraction    │
│ Input:  List[Chunk]                     │  │ Input:  YouTube URL             │
│ Output: List[Transcript(text, model,    │  │ Output: List[Caption(text,      │
│         chunk_id, confidence)]          │  │         start_time, end_time)]  │
│ Tool:   Whisper/Faster-Whisper/Indic    │  │ Tool:   yt-dlp                  │
└─────────────────────────────────────────┘  └─────────────────────────────────┘
    │                                                    │
    ▼                                                    │
┌─────────────────────────────────────────┐              │
│ STAGE 5: N-gram Deduplication           │              │
│ Input:  List[Transcript]                │              │
│ Output: List[Transcript] (cleaned)      │              │
│ Tool:   Custom n-gram logic             │              │
└─────────────────────────────────────────┘              │
    │                                                    │
    └────────────────────────────────────────────────────┤
                                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 6: Normalization                                                       │
│ Input:  Transcripts + Captions                                               │
│ Output: Normalized text pairs                                                │
│ Logic:  lowercase, remove punctuation, collapse whitespace                  │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 7: Comparison                                                          │
│ Input:  Normalized (transcript, caption) pairs                               │
│ Output: List[ComparisonResult(wer, cer, semantic_sim, hybrid_score, chunk_id)]│
│ Tools:  jiwer (WER/CER), sentence-transformers (semantic), SeMaScore (hybrid)│
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 8: Report Generation                                                   │
│ Input:  List[ComparisonResult] + metadata                                    │
│ Output: JSON file + Console summary                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple transcription models | Requirement specifies comparing models | Single model wouldn't meet spec |
| Semantic similarity embeddings | Required metric per specification | WER/CER alone don't capture meaning |

## Dependencies

```
# Core
yt-dlp>=2024.1.1           # YouTube download
pydub>=0.25.1              # Audio manipulation
librosa>=0.10.0            # Audio processing

# VAD
torch>=2.0.0               # Required for Silero VAD
silero-vad>=4.0.0          # Voice Activity Detection

# Transcription
faster-whisper>=0.10.0     # Optimized Whisper
openai-whisper>=20231117   # Original Whisper
transformers>=4.36.0       # For ai4bharat models

# Comparison
jiwer>=3.0.0               # WER/CER calculation
sentence-transformers>=2.2.0  # Semantic similarity

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Optional
ffmpeg-python>=0.2.0       # FFmpeg bindings
```

