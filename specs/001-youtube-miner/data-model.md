# Data Model: YouTube Miner

## Core Entities

### AudioFile

Represents a downloaded or processed audio file.

```python
@dataclass
class AudioFile:
    path: Path                    # File system path to audio
    format: str                   # 'wav', 'm4a', 'webm', etc.
    duration: float               # Duration in seconds
    sample_rate: int              # Sample rate in Hz (target: 16000)
    channels: int                 # Number of channels (target: 1 mono)
    source_url: Optional[str]     # Original YouTube URL if applicable
    created_at: datetime          # When file was created/downloaded
```

**Lifecycle**:
1. Created during download (any format)
2. Converted to WAV (16kHz, mono)
3. Used as input for VAD chunking

---

### Chunk

Represents a speech segment extracted via VAD.

```python
@dataclass
class Chunk:
    index: int                    # Chunk number (0-indexed)
    audio_path: Path              # Path to chunk WAV file
    start_time: float             # Start time in original audio (seconds)
    end_time: float               # End time in original audio (seconds)
    duration: float               # Actual duration (target: ~30s)
    is_speech: bool               # Confirmed as speech by VAD
    confidence: float             # VAD confidence score (0-1)
    parent_audio: AudioFile       # Reference to source audio
```

**Lifecycle**:
1. Created by VAD chunker from AudioFile
2. Saved as individual WAV file
3. Used as input for transcription

---

### Transcript

Represents transcription output from a model.

```python
@dataclass
class Transcript:
    text: str                     # Raw transcribed text
    model_name: str               # 'whisper-tiny', 'faster-whisper', etc.
    chunk: Chunk                  # Associated chunk
    confidence: float             # Model confidence (0-1)
    language: Optional[str]       # Detected language code
    processing_time: float        # Time taken to transcribe (seconds)
    raw_text: str                 # Text before n-gram dedup
    deduplicated: bool            # Whether n-gram dedup was applied
```

**Lifecycle**:
1. Created by transcriber from Chunk
2. Processed by n-gram deduplicator
3. Normalized for comparison

---

### Caption

Represents YouTube auto-generated caption.

```python
@dataclass
class Caption:
    text: str                     # Caption text
    start_time: float             # Start time in video (seconds)
    end_time: float               # End time in video (seconds)
    language: str                 # Caption language code
    source: str                   # 'auto', 'manual', 'translated'
    video_url: str                # Source YouTube URL
```

**Lifecycle**:
1. Extracted from YouTube via yt-dlp
2. Parsed from VTT/SRT format
3. Aligned to chunk timestamps for comparison

---

### ComparisonResult

Represents comparison metrics between transcript and caption.

```python
@dataclass
class ComparisonResult:
    chunk: Chunk                  # Associated chunk
    transcript: Transcript        # Model transcription
    caption: Caption              # YouTube caption
    
    # Normalized texts used for comparison
    normalized_transcript: str
    normalized_caption: str
    
    # Metrics
    wer: float                    # Word Error Rate (0-1, lower is better)
    cer: float                    # Character Error Rate (0-1, lower is better)
    semantic_similarity: float    # Cosine similarity (0-1, higher is better)
    hybrid_score: Optional[float] # SeMaScore or combined metric
    
    # Metadata
    computed_at: datetime
```

**Lifecycle**:
1. Created by comparator from transcript-caption pair
2. Aggregated into pipeline report

---

### PipelineReport

Represents the final output of the complete pipeline.

```python
@dataclass
class PipelineReport:
    video_url: str                # Original YouTube URL
    video_title: str              # Video title
    video_duration: float         # Total video duration
    
    # Processing info
    processed_at: datetime
    processing_time: float        # Total pipeline time
    model_used: str               # Transcription model name
    
    # Results
    total_chunks: int
    chunks: List[ChunkResult]     # Per-chunk results
    
    # Aggregated metrics
    summary: MetricsSummary
```

```python
@dataclass
class ChunkResult:
    chunk_id: int
    start_time: float
    end_time: float
    model_transcript: str
    youtube_caption: str
    metrics: ComparisonResult
```

```python
@dataclass
class MetricsSummary:
    avg_wer: float
    avg_cer: float
    avg_semantic_similarity: float
    min_wer: float
    max_wer: float
    std_wer: float
    # Similar for CER and semantic similarity
```

---

## Entity Relationships

```
┌─────────────────┐
│   YouTube URL   │
└────────┬────────┘
         │ downloads
         ▼
┌─────────────────┐
│   AudioFile     │
└────────┬────────┘
         │ chunks into
         ▼
┌─────────────────┐         ┌─────────────────┐
│     Chunk       │◄────────│    Caption      │
│  (1:N from      │ aligned │  (extracted     │
│   AudioFile)    │   to    │   from URL)     │
└────────┬────────┘         └─────────────────┘
         │ transcribes to              │
         ▼                             │
┌─────────────────┐                    │
│   Transcript    │                    │
│  (1:1 per model │                    │
│   per chunk)    │                    │
└────────┬────────┘                    │
         │                             │
         └──────────────┬──────────────┘
                        │ compares
                        ▼
              ┌─────────────────┐
              │ComparisonResult │
              │ (1 per chunk)   │
              └────────┬────────┘
                       │ aggregates
                       ▼
              ┌─────────────────┐
              │ PipelineReport  │
              │   (1 per URL)   │
              └─────────────────┘
```

---

## File Storage Structure

```
output/
├── {video_id}/
│   ├── audio/
│   │   ├── original.m4a          # Downloaded audio
│   │   └── converted.wav         # 16kHz mono WAV
│   ├── chunks/
│   │   ├── chunk_000.wav
│   │   ├── chunk_001.wav
│   │   └── ...
│   ├── transcripts/
│   │   ├── whisper-tiny/
│   │   │   ├── chunk_000.json
│   │   │   └── ...
│   │   ├── faster-whisper/
│   │   │   └── ...
│   │   └── combined.json         # All chunks, all models
│   ├── captions/
│   │   ├── raw.vtt               # Original caption file
│   │   └── aligned.json          # Aligned to chunks
│   └── report/
│       ├── report.json           # Full JSON report
│       └── summary.md            # Human-readable summary
```

---

## JSON Schemas

### Chunk JSON

```json
{
  "index": 0,
  "audio_path": "chunks/chunk_000.wav",
  "start_time": 0.0,
  "end_time": 30.5,
  "duration": 30.5,
  "is_speech": true,
  "confidence": 0.95
}
```

### Transcript JSON

```json
{
  "text": "Hello and welcome to the podcast...",
  "model_name": "faster-whisper",
  "chunk_index": 0,
  "confidence": 0.87,
  "language": "en",
  "processing_time": 2.3,
  "raw_text": "Hello and and welcome to to the podcast...",
  "deduplicated": true
}
```

### ComparisonResult JSON

```json
{
  "chunk_index": 0,
  "normalized_transcript": "hello and welcome to the podcast",
  "normalized_caption": "hello and welcome to the podcast",
  "wer": 0.15,
  "cer": 0.08,
  "semantic_similarity": 0.92,
  "hybrid_score": 0.88
}
```

