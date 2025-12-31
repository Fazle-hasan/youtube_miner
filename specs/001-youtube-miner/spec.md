# Feature Specification: YouTube Miner

**Feature Branch**: `001-youtube-miner`  
**Created**: 2024-12-24  
**Status**: Draft  
**Input**: User description: "Python script for YouTube audio extraction, VAD chunking, transcription, and caption comparison"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download YouTube Audio (Priority: P1)

As a user, I want to provide a YouTube URL and have the system download the audio track automatically, so I can process it for transcription.

**Why this priority**: This is the entry point of the entire pipeline. Without audio download, nothing else works.

**Independent Test**: Can be fully tested by providing a valid YouTube URL and verifying a WAV file is created with correct audio content.

**Acceptance Scenarios**:

1. **Given** a valid YouTube URL, **When** the download command is executed, **Then** audio is extracted and saved as a WAV file (16kHz, mono)
2. **Given** an invalid/private YouTube URL, **When** the download command is executed, **Then** an appropriate error message is displayed
3. **Given** a YouTube URL with age restriction, **When** the download command is executed, **Then** the system handles it gracefully with an error message

---

### User Story 2 - VAD-Based Audio Chunking (Priority: P1)

As a user, I want the audio to be automatically split into clean 30-second chunks with silence and music removed, so I get speech-only segments for transcription.

**Why this priority**: Core requirement - VAD chunking is central to the pipeline's purpose.

**Independent Test**: Can be tested by providing a WAV file and verifying output chunks are approximately 30 seconds of clean speech.

**Acceptance Scenarios**:

1. **Given** a WAV audio file, **When** VAD chunking is applied, **Then** the output consists of 30-second chunks containing only speech
2. **Given** audio with long silence gaps, **When** VAD chunking is applied, **Then** silence is removed and chunks contain continuous speech
3. **Given** audio with background music, **When** VAD chunking is applied, **Then** music sections are identified and excluded from speech chunks
4. **Given** audio shorter than 30 seconds of speech, **When** VAD chunking is applied, **Then** the system produces fewer chunks as appropriate

---

### User Story 3 - Multi-Model Transcription (Priority: P1)

As a user, I want to transcribe audio chunks using multiple open-source models, so I can compare their performance and choose the best output.

**Why this priority**: Transcription is the core output of the pipeline and must support multiple models as per requirements.

**Independent Test**: Can be tested by providing an audio chunk and verifying transcription output from each model.

**Acceptance Scenarios**:

1. **Given** a 30-second audio chunk, **When** Whisper-Tiny model is selected, **Then** a text transcription is produced
2. **Given** a 30-second audio chunk, **When** Faster-Whisper model is selected, **Then** a text transcription is produced with faster processing
3. **Given** a 30-second audio chunk, **When** ai4bharat/indic-seamless model is selected, **Then** multilingual transcription is produced
4. **Given** all chunks from a video, **When** transcription is complete, **Then** repetitive words are removed using n-gram analysis

---

### User Story 4 - YouTube Caption Extraction (Priority: P2)

As a user, I want to automatically extract YouTube's auto-generated captions, so I can compare them with my transcription.

**Why this priority**: Required for comparison, but depends on successful audio processing first.

**Independent Test**: Can be tested by providing a YouTube URL and verifying caption text is extracted.

**Acceptance Scenarios**:

1. **Given** a YouTube URL with auto-captions, **When** caption extraction is executed, **Then** the caption text is retrieved with timestamps
2. **Given** a YouTube URL without captions, **When** caption extraction is attempted, **Then** an appropriate message indicates no captions available
3. **Given** extracted captions, **When** processing completes, **Then** captions are aligned to match chunk timestamps

---

### User Story 5 - Transcription Comparison (Priority: P2)

As a user, I want to compare my transcription with YouTube's auto-captions using multiple metrics, so I can evaluate transcription quality.

**Why this priority**: Final stage of pipeline - requires all prior stages to be complete.

**Independent Test**: Can be tested by providing two text samples and verifying metric calculations are correct.

**Acceptance Scenarios**:

1. **Given** model transcription and YouTube captions, **When** comparison is executed, **Then** Word Error Rate (WER) is calculated and reported
2. **Given** model transcription and YouTube captions, **When** comparison is executed, **Then** Character Error Rate (CER) is calculated and reported
3. **Given** model transcription and YouTube captions, **When** comparison is executed, **Then** semantic similarity (cosine embedding) is calculated at chunk level
4. **Given** both transcripts before comparison, **When** normalization is applied, **Then** both are normalized identically (lowercase, punctuation removal, etc.)

---

### User Story 6 - End-to-End Pipeline CLI (Priority: P3)

As a user, I want a single command that runs the entire pipeline from YouTube URL to comparison report, so I can process videos with minimal effort.

**Why this priority**: Convenience feature that integrates all components.

**Independent Test**: Can be tested by running the CLI with a YouTube URL and verifying complete output report.

**Acceptance Scenarios**:

1. **Given** a YouTube URL via CLI, **When** the pipeline command is executed, **Then** all stages run sequentially and produce a final report
2. **Given** CLI execution, **When** any stage fails, **Then** appropriate error handling and logging occurs
3. **Given** completed pipeline, **When** results are output, **Then** a structured report (JSON + human-readable) is generated

---

### Edge Cases

- What happens when YouTube video is longer than 3 hours? (Memory management)
- How does system handle audio with multiple languages?
- What happens when audio quality is very poor?
- How to handle network interruption during download?
- What if Whisper model fails to load due to memory constraints?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download audio from YouTube URLs using yt-dlp
- **FR-002**: System MUST convert downloaded audio to WAV format (16kHz, mono)
- **FR-003**: System MUST apply Silero VAD to detect speech segments
- **FR-004**: System MUST chunk audio into ~30-second speech-only segments
- **FR-005**: System MUST support multiple transcription models (Whisper-Tiny, Faster-Whisper, ai4bharat/indic-seamless)
- **FR-006**: System MUST remove repetitive words using n-gram analysis
- **FR-007**: System MUST extract YouTube auto-generated captions
- **FR-008**: System MUST normalize both transcripts before comparison
- **FR-009**: System MUST calculate WER (Word Error Rate)
- **FR-010**: System MUST calculate CER (Character Error Rate)
- **FR-011**: System MUST calculate semantic similarity using embedding cosine
- **FR-012**: System MUST NOT use any paid APIs
- **FR-013**: System MUST provide CLI interface for all operations

### Key Entities

- **AudioFile**: Downloaded/converted audio (path, format, duration, sample_rate)
- **Chunk**: Speech segment (audio_data, start_time, end_time, duration, index)
- **Transcript**: Text output from model (text, model_name, chunk_id, confidence)
- **Caption**: YouTube caption (text, start_time, end_time, source)
- **ComparisonResult**: Metrics (wer, cer, semantic_similarity, chunk_id, normalized_texts)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pipeline processes a 1-hour podcast in under 30 minutes on standard hardware
- **SC-002**: VAD correctly identifies speech vs non-speech with >90% accuracy
- **SC-003**: All three comparison metrics (WER, CER, semantic similarity) are computed for every chunk
- **SC-004**: System handles videos up to 3 hours without memory errors
- **SC-005**: Unit test coverage exceeds 80%
- **SC-006**: Documentation includes setup instructions that work on first try
- **SC-007**: Demo video clearly shows all pipeline stages working

