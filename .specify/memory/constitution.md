# YouTube Miner Constitution

## Core Principles

### I. Open-Source First
All components must use open-source libraries exclusively. No paid APIs allowed.
- **Audio Download**: yt-dlp for YouTube audio extraction
- **Voice Activity Detection**: Silero VAD for silence/music removal
- **Transcription**: Whisper-Tiny, Faster-Whisper, ai4bharat/indic-seamless or equivalent open-source models
- **Comparison**: Open-source NLP libraries for WER, CER, and semantic similarity

### II. Modular Pipeline Architecture
The system follows a strict pipeline pattern with clear separation of concerns:
```
YouTube URL → Audio Download → WAV Conversion → VAD Chunking → Transcription → N-gram Dedup → Caption Comparison
```
Each stage must be:
- Independently testable
- Loosely coupled with clear interfaces
- Capable of running in isolation for debugging

### III. Test-First Development (NON-NEGOTIABLE)
TDD is mandatory for all components:
- Unit tests written BEFORE implementation
- Red-Green-Refactor cycle strictly enforced
- Integration tests for pipeline stages
- Minimum 80% code coverage target
- All edge cases documented and tested

### IV. Data Quality Standards
Audio and text processing must maintain quality:
- Audio chunks: Clean 30-second segments with silence/music removed
- Transcription: Remove repetitive words using n-gram analysis
- Normalization: Both transcripts (model output and YouTube captions) normalized identically before comparison
- Comparison metrics: WER, CER, and semantic similarity (embedding cosine) at chunk level

### V. Simplicity & YAGNI
- Start with minimal viable implementation
- No premature optimization
- Add complexity only when justified by requirements
- Prefer standard library solutions over external dependencies when equivalent

## Technical Specifications

### Audio Processing
| Specification | Value |
|--------------|-------|
| Output Format | WAV (16kHz, mono) |
| Chunk Duration | 30 seconds (clean speech) |
| VAD Model | Silero VAD |
| Silence Threshold | Configurable, default removes non-speech |

### Transcription Models (Priority Order)
1. **Faster-Whisper (Whisper-Tiny)** - Optimized for speed
2. **Whisper-Tiny** - Baseline model
3. **ai4bharat/indic-seamless** - For multilingual support
4. **openai/whisper-large** - for big text
5. Additional models may be added if they outperform baseline

### Comparison Metrics
| Metric | Purpose |
|--------|---------|
| Word Error Rate (WER) | Word-level accuracy |
| Character Error Rate (CER) | Character-level accuracy |
| Semantic Similarity | Meaning preservation (cosine similarity) |
| Hybrid metrics like SeMaScore | Newer metrics combine error rate with semantic similarity to better match human judgments of transcript quality | Useful if you care about user‑perceived quality rather than raw edit distance |

## Development Workflow

### Project Structure
```
youtube_miner/
├── src/
│   ├── downloader/      # YouTube audio download
│   ├── converter/       # Audio format conversion
│   ├── vad/             # Voice activity detection & chunking
│   ├── transcriber/     # Speech-to-text models
│   ├── deduplicator/    # N-gram repetition removal
│   ├── comparator/      # WER, CER, semantic similarity
│   └── pipeline/        # End-to-end orchestration
├── tests/
│   ├── unit/            # Unit tests per module
│   └── integration/     # Pipeline integration tests
├── docs/
│   └── technical_design.md
├── requirements.txt
└── README.md
```

### Code Quality Gates
- All code must pass linting (flake8/black)
- Type hints required for all public functions
- Docstrings required for all modules, classes, and functions
- No merge without passing tests

### Documentation Requirements
1. **README.md**: Setup instructions, quick start, usage examples
2. **Technical Design Document**: Architecture diagrams, flow diagrams, assumptions
3. **Inline Documentation**: Clear comments for complex logic
4. **Demo Video**: YouTube link showcasing key features

## Deliverables Checklist

- [ ] Functional Python script accepting YouTube URL
- [ ] Audio download and WAV conversion
- [ ] VAD-based 30-second chunking
- [ ] Multi-model transcription support
- [ ] N-gram deduplication
- [ ] Comparison with YouTube auto-captions (WER, CER, Semantic)
- [ ] Comprehensive unit tests
- [ ] Technical design document with diagrams
- [ ] Demo video (YouTube link)
- [ ] GitHub repository with version control
- [ ] Setup and deployment instructions

## Governance

- This constitution guides all development decisions
- Any deviation requires documented justification
- Code reviews must verify compliance with these principles
- Architecture changes require constitution amendment

**Version**: 1.0.0 | **Ratified**: 2024-12-24 | **Last Amended**: 2024-12-24

