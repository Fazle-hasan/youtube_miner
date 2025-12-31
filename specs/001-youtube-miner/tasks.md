# Tasks: YouTube Miner

**Input**: Design documents from `/specs/001-youtube-miner/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Unit and integration tests included as per constitution (80% coverage target).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure) ✅

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per plan.md
- [x] T002 Create pyproject.toml with project metadata and dependencies
- [x] T003 [P] Create requirements.txt with all dependencies
- [x] T004 [P] Create src/__init__.py with package info
- [x] T005 [P] Configure .gitignore for Python project
- [x] T006 [P] Setup pytest configuration in pyproject.toml
- [x] T007 [P] Create tests/conftest.py with shared fixtures

---

## Phase 2: Foundational (Core Models & Interfaces) ✅

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T008 Create src/models/__init__.py
- [x] T009 [P] Create AudioFile dataclass in src/models/audio.py
- [x] T010 [P] Create Chunk dataclass in src/models/audio.py
- [x] T011 [P] Create Transcript dataclass in src/models/transcript.py
- [x] T012 [P] Create Caption dataclass in src/models/transcript.py
- [x] T013 [P] Create ComparisonResult dataclass in src/models/comparison.py
- [x] T014 Create base transcriber interface in src/transcriber/base.py
- [x] T015 [P] Create logging configuration in src/utils/logger.py
- [x] T016 [P] Create configuration management in src/utils/config.py

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Download YouTube Audio (Priority: P1) ✅ MVP

**Goal**: Download audio from YouTube URL and convert to WAV

**Independent Test**: Provide YouTube URL, verify WAV file is created

### Tests for User Story 1 ⚠️

- [x] T017 [P] [US1] Unit test for YouTube downloader in tests/unit/test_downloader.py
- [x] T018 [P] [US1] Unit test for audio converter in tests/unit/test_converter.py
- [ ] T019 [P] [US1] Integration test for download+convert in tests/integration/test_download_flow.py

### Implementation for User Story 1 ✅

- [x] T020 [US1] Implement YouTube downloader using yt-dlp in src/downloader/youtube.py
- [x] T021 [US1] Implement audio format converter (to WAV 16kHz mono) in src/converter/audio.py
- [x] T022 [US1] Add error handling for invalid URLs in src/downloader/youtube.py
- [x] T023 [US1] Add error handling for conversion failures in src/converter/audio.py
- [x] T024 [US1] Add progress logging for download operations

**Checkpoint**: ✅ User Story 1 fully functional

---

## Phase 4: User Story 2 - VAD-Based Audio Chunking (Priority: P1) ✅ MVP

**Goal**: Split audio into clean 30-second speech chunks using Silero VAD

**Independent Test**: Provide WAV file, verify ~30-second speech-only chunks are created

### Tests for User Story 2 ⚠️

- [x] T025 [P] [US2] Unit test for VAD detection in tests/unit/test_vad.py
- [x] T026 [P] [US2] Unit test for chunking logic in tests/unit/test_vad.py
- [ ] T027 [P] [US2] Integration test for full chunking pipeline in tests/integration/test_vad_flow.py

### Implementation for User Story 2 ✅

- [x] T028 [US2] Implement Silero VAD wrapper in src/vad/chunker.py
- [x] T029 [US2] Implement speech segment extraction in src/vad/chunker.py
- [x] T030 [US2] Implement 30-second chunk creation logic in src/vad/chunker.py
- [x] T031 [US2] Add silence/music removal logic in src/vad/chunker.py
- [x] T032 [US2] Add chunk metadata (timestamps, duration) in src/vad/chunker.py
- [x] T033 [US2] Save chunks as individual WAV files

**Checkpoint**: ✅ User Story 2 fully functional

---

## Phase 5: User Story 3 - Multi-Model Transcription (Priority: P1) ✅ MVP

**Goal**: Transcribe audio chunks using multiple open-source models

**Independent Test**: Provide audio chunk, verify transcription from each model

### Tests for User Story 3 ⚠️

- [x] T034 [P] [US3] Unit test for Whisper-Tiny transcriber in tests/unit/test_transcriber.py
- [x] T035 [P] [US3] Unit test for Faster-Whisper transcriber in tests/unit/test_transcriber.py
- [x] T036 [P] [US3] Unit test for Indic-Seamless transcriber in tests/unit/test_transcriber.py
- [x] T037 [P] [US3] Unit test for n-gram deduplication in tests/unit/test_deduplicator.py
- [ ] T038 [P] [US3] Integration test for transcription pipeline in tests/integration/test_transcription_flow.py

### Implementation for User Story 3 ✅

- [x] T039 [US3] Implement Whisper-Tiny transcriber in src/transcriber/whisper_tiny.py
- [x] T040 [US3] Implement Faster-Whisper transcriber in src/transcriber/faster_whisper.py
- [x] T041 [US3] Implement Indic-Seamless transcriber in src/transcriber/indic_seamless.py
- [x] T042 [US3] Implement Whisper-Large transcriber in src/transcriber/whisper_large.py
- [x] T043 [US3] Create transcriber factory/selector in src/transcriber/__init__.py
- [x] T044 [US3] Implement n-gram repetition detection in src/deduplicator/ngram.py
- [x] T045 [US3] Implement repetition removal logic in src/deduplicator/ngram.py
- [x] T046 [US3] Add confidence scores to transcription output

**Checkpoint**: ✅ User Story 3 fully functional

---

## Phase 6: User Story 4 - YouTube Caption Extraction (Priority: P2) ✅

**Goal**: Extract YouTube auto-generated captions for comparison

**Independent Test**: Provide YouTube URL, verify captions are extracted with timestamps

### Tests for User Story 4 ⚠️

- [x] T047 [P] [US4] Unit test for caption extractor in tests/unit/test_captions.py
- [x] T048 [P] [US4] Unit test for caption timestamp alignment in tests/unit/test_captions.py
- [ ] T049 [P] [US4] Integration test for caption extraction in tests/integration/test_caption_flow.py

### Implementation for User Story 4 ✅

- [x] T050 [US4] Implement caption extraction using yt-dlp in src/downloader/captions.py
- [x] T051 [US4] Parse caption format (VTT/SRT) in src/downloader/captions.py
- [x] T052 [US4] Align captions to chunk timestamps in src/downloader/captions.py
- [x] T053 [US4] Handle missing captions gracefully in src/downloader/captions.py

**Checkpoint**: ✅ User Story 4 fully functional

---

## Phase 7: User Story 5 - Transcription Comparison (Priority: P2) ✅

**Goal**: Compare model transcription with YouTube captions using WER, CER, semantic similarity

**Independent Test**: Provide two text samples, verify all metrics are calculated

### Tests for User Story 5 ✅

- [x] T054 [P] [US5] Unit test for text normalizer in tests/unit/test_normalizer.py
- [x] T055 [P] [US5] Unit test for WER calculation in tests/unit/test_comparator.py
- [x] T056 [P] [US5] Unit test for CER calculation in tests/unit/test_comparator.py
- [x] T057 [P] [US5] Unit test for semantic similarity in tests/unit/test_comparator.py
- [ ] T058 [P] [US5] Integration test for full comparison in tests/integration/test_comparison_flow.py

### Implementation for User Story 5 ✅

- [x] T059 [US5] Implement text normalizer (lowercase, punctuation) in src/comparator/normalizer.py
- [x] T060 [US5] Implement WER calculation using jiwer in src/comparator/wer.py
- [x] T061 [US5] Implement CER calculation using jiwer in src/comparator/cer.py
- [x] T062 [US5] Implement semantic similarity using sentence-transformers in src/comparator/semantic.py
- [x] T063 [US5] Implement hybrid SeMaScore metric in src/comparator/hybrid.py
- [x] T064 [US5] Create comparison aggregator in src/comparator/__init__.py

**Checkpoint**: ✅ User Story 5 fully functional

---

## Phase 8: User Story 6 - End-to-End Pipeline CLI (Priority: P3) ✅

**Goal**: Single command that runs entire pipeline from URL to comparison report

**Independent Test**: Run CLI with YouTube URL, verify complete report is generated

### Tests for User Story 6 ⚠️

- [x] T065 [P] [US6] Unit test for CLI argument parsing in tests/unit/test_cli.py
- [ ] T066 [P] [US6] Integration test for full pipeline in tests/integration/test_pipeline.py
- [ ] T067 [P] [US6] End-to-end test with real YouTube URL in tests/integration/test_e2e.py

### Implementation for User Story 6 ✅

- [x] T068 [US6] Implement CLI entry point in src/cli.py
- [x] T069 [US6] Implement pipeline orchestrator in src/pipeline/orchestrator.py
- [x] T070 [US6] Implement JSON report generator in src/pipeline/orchestrator.py
- [x] T071 [US6] Implement human-readable console output in src/pipeline/orchestrator.py
- [x] T072 [US6] Add --model flag for model selection
- [x] T073 [US6] Add --output flag for output directory
- [x] T074 [US6] Add --verbose flag for detailed logging
- [x] T075 [US6] Add progress bar for long operations
- [x] T076 [US6] Create __main__.py for module execution

**Checkpoint**: ✅ All user stories independently functional

---

## Phase 9: Polish & Documentation

**Purpose**: Documentation, cleanup, and final deliverables

- [x] T077 [P] Create comprehensive README.md with installation and usage
- [ ] T078 [P] Create docs/technical_design.md with architecture diagrams
- [x] T079 [P] Add docstrings to all public functions and classes
- [ ] T080 [P] Run and fix all linting issues (flake8/black)
- [ ] T081 [P] Ensure test coverage exceeds 80%
- [ ] T082 [P] Create example scripts in examples/ directory
- [ ] T083 Run quickstart.md validation
- [ ] T084 Record demo video showcasing all features
- [ ] T085 Final code review and cleanup

---

## Progress Summary

| Phase | Status | Completed | Total |
|-------|--------|-----------|-------|
| Phase 1: Setup | ✅ | 7/7 | 100% |
| Phase 2: Foundational | ✅ | 9/9 | 100% |
| Phase 3: US1 Download | ✅ | 7/8 | 88% |
| Phase 4: US2 VAD | ✅ | 8/9 | 89% |
| Phase 5: US3 Transcription | ✅ | 12/13 | 92% |
| Phase 6: US4 Captions | ✅ | 6/7 | 86% |
| Phase 7: US5 Comparison | ✅ | 10/11 | 91% |
| Phase 8: US6 CLI | ✅ | 11/12 | 92% |
| Phase 9: Polish | 🔄 | 2/9 | 22% |
| **TOTAL** | 🔄 | **72/85** | **85%** |

---

## Remaining Tasks

1. Integration tests (5 tasks)
2. Technical design document
3. Linting fixes
4. Test coverage verification
5. Example scripts
6. Demo video

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Target: 80% test coverage as per constitution
