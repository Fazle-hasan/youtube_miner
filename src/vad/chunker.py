"""Voice Activity Detection and audio chunking using Silero VAD."""

import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import soundfile as sf
import torch
from silero_vad import load_silero_vad, get_speech_timestamps

from src.models.audio import AudioFile, Chunk

logger = logging.getLogger(__name__)


class VADChunker:
    """Chunk audio into speech segments using Silero VAD.
    
    This class uses Silero VAD to detect speech segments and creates
    clean ~30-second chunks containing only speech (no silence/music).
    
    Example:
        >>> chunker = VADChunker(output_dir="./chunks")
        >>> chunks = chunker.chunk(audio_file)
        >>> print(f"Created {len(chunks)} chunks")
    """
    
    SAMPLE_RATE = 16000  # Silero VAD requires 16kHz
    
    def __init__(
        self,
        output_dir: str = "./output/chunks",
        chunk_duration: float = 30.0,
        min_speech_duration: float = 0.5,
        min_silence_duration: float = 0.3,
        threshold: float = 0.5,
    ):
        """Initialize the VAD chunker.
        
        Args:
            output_dir: Directory to save chunk files.
            chunk_duration: Target chunk duration in seconds (default: 30).
            min_speech_duration: Minimum speech duration to keep (default: 0.5s).
            min_silence_duration: Minimum silence duration to split on (default: 0.3s).
            threshold: VAD confidence threshold (default: 0.5).
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_duration = chunk_duration
        self.min_speech_duration = min_speech_duration
        self.min_silence_duration = min_silence_duration
        self.threshold = threshold
        
        # Load Silero VAD model
        self.model = self._load_vad_model()
    
    def _load_vad_model(self):
        """Load Silero VAD model.
        
        Returns:
            Silero VAD model.
        """
        logger.info("Loading Silero VAD model (ONNX)...")
        
        # Use ONNX version to avoid torchcodec dependency
        model = load_silero_vad(onnx=True)
        
        logger.info("Silero VAD model loaded successfully")
        return model
    
    def _load_audio(self, audio_path: Path) -> Tuple[torch.Tensor, int]:
        """Load audio file using soundfile.
        
        Args:
            audio_path: Path to audio file.
            
        Returns:
            Tuple of (waveform tensor, sample_rate).
        """
        # Load audio with soundfile
        data, sample_rate = sf.read(str(audio_path))
        
        # Convert to float32 numpy array if needed
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        
        # Handle stereo/mono - soundfile returns (samples,) for mono or (samples, channels) for stereo
        if data.ndim == 1:
            # Mono: reshape to (1, samples)
            waveform = torch.from_numpy(data).unsqueeze(0)
        else:
            # Stereo/multi-channel: (samples, channels) -> (channels, samples)
            waveform = torch.from_numpy(data.T)
            # Convert to mono by averaging channels
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
        
        # Resample if needed
        if sample_rate != self.SAMPLE_RATE:
            # Simple linear interpolation for resampling
            current_length = waveform.shape[1]
            new_length = int(current_length * self.SAMPLE_RATE / sample_rate)
            waveform = torch.nn.functional.interpolate(
                waveform.unsqueeze(0), size=new_length, mode='linear', align_corners=False
            ).squeeze(0)
            sample_rate = self.SAMPLE_RATE
        
        return waveform, sample_rate
    
    def detect_speech_segments(self, audio_path: Path) -> List[Tuple[float, float]]:
        """Detect speech segments in audio file.
        
        Args:
            audio_path: Path to audio file.
            
        Returns:
            List of (start_time, end_time) tuples for speech segments.
        """
        # Load audio using soundfile
        waveform, sample_rate = self._load_audio(audio_path)
        
        # Get speech timestamps using silero_vad function
        speech_timestamps = get_speech_timestamps(
            waveform.squeeze(),
            self.model,
            sampling_rate=self.SAMPLE_RATE,
            threshold=self.threshold,
            min_speech_duration_ms=int(self.min_speech_duration * 1000),
            min_silence_duration_ms=int(self.min_silence_duration * 1000),
        )
        
        # Convert sample indices to time
        segments = []
        for ts in speech_timestamps:
            start_time = ts['start'] / self.SAMPLE_RATE
            end_time = ts['end'] / self.SAMPLE_RATE
            segments.append((start_time, end_time))
        
        logger.info(f"Detected {len(segments)} speech segments")
        return segments
    
    def chunk(self, audio_file: AudioFile) -> List[Chunk]:
        """Chunk audio file into speech-only segments.
        
        Args:
            audio_file: AudioFile to chunk.
            
        Returns:
            List of Chunk objects.
        """
        if not audio_file.exists:
            raise FileNotFoundError(f"Audio file not found: {audio_file.path}")
        
        logger.info(f"Chunking audio: {audio_file.path}")
        
        # Detect speech segments
        speech_segments = self.detect_speech_segments(audio_file.path)
        
        if not speech_segments:
            logger.warning("No speech detected in audio")
            return []
        
        # Load full audio for extraction using soundfile
        waveform, sample_rate = self._load_audio(audio_file.path)
        
        # Merge segments into ~30-second chunks
        chunks = self._create_chunks(
            waveform, speech_segments, audio_file.path
        )
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def _create_chunks(
        self,
        waveform: torch.Tensor,
        segments: List[Tuple[float, float]],
        parent_path: Path,
    ) -> List[Chunk]:
        """Create chunks from speech segments.
        
        Args:
            waveform: Audio waveform tensor.
            segments: List of (start, end) speech segments.
            parent_path: Path to parent audio file.
            
        Returns:
            List of Chunk objects.
        """
        chunks = []
        chunk_index = 0
        current_segments = []
        current_duration = 0.0
        chunk_start = None
        
        for start, end in segments:
            segment_duration = end - start
            
            if chunk_start is None:
                chunk_start = start
            
            # Add segment to current chunk
            current_segments.append((start, end))
            current_duration += segment_duration
            
            # If chunk is long enough, save it
            if current_duration >= self.chunk_duration:
                chunk = self._save_chunk(
                    waveform,
                    current_segments,
                    chunk_index,
                    chunk_start,
                    end,
                    parent_path,
                )
                chunks.append(chunk)
                
                # Reset for next chunk
                chunk_index += 1
                current_segments = []
                current_duration = 0.0
                chunk_start = None
        
        # Save any remaining segments
        if current_segments and current_duration >= self.min_speech_duration:
            chunk = self._save_chunk(
                waveform,
                current_segments,
                chunk_index,
                chunk_start,
                current_segments[-1][1],
                parent_path,
            )
            chunks.append(chunk)
        
        return chunks
    
    def _save_chunk(
        self,
        waveform: torch.Tensor,
        segments: List[Tuple[float, float]],
        index: int,
        start_time: float,
        end_time: float,
        parent_path: Path,
    ) -> Chunk:
        """Save a chunk to disk.
        
        Args:
            waveform: Full audio waveform.
            segments: Speech segments in this chunk.
            index: Chunk index.
            start_time: Chunk start time in original audio.
            end_time: Chunk end time in original audio.
            parent_path: Path to parent audio file.
            
        Returns:
            Chunk object.
        """
        # Extract and concatenate speech segments
        chunk_audio = []
        
        for seg_start, seg_end in segments:
            start_sample = int(seg_start * self.SAMPLE_RATE)
            end_sample = int(seg_end * self.SAMPLE_RATE)
            chunk_audio.append(waveform[:, start_sample:end_sample])
        
        # Concatenate all segments
        chunk_waveform = torch.cat(chunk_audio, dim=1)
        duration = chunk_waveform.shape[1] / self.SAMPLE_RATE
        
        # Save chunk using soundfile
        chunk_path = self.output_dir / f"chunk_{index:03d}.wav"
        # Convert to numpy and transpose to (samples, channels) for soundfile
        audio_data = chunk_waveform.squeeze(0).numpy()
        sf.write(str(chunk_path), audio_data, self.SAMPLE_RATE)
        
        logger.debug(f"Saved chunk {index}: {chunk_path} ({duration:.1f}s)")
        
        return Chunk(
            index=index,
            audio_path=chunk_path,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            is_speech=True,
            confidence=1.0,
            parent_audio_path=parent_path,
        )
    
    def chunk_from_path(self, audio_path: str) -> List[Chunk]:
        """Chunk audio from file path.
        
        Args:
            audio_path: Path to audio file.
            
        Returns:
            List of Chunk objects.
        """
        audio_file = AudioFile(
            path=Path(audio_path),
            format=Path(audio_path).suffix[1:],
            duration=0,
        )
        return self.chunk(audio_file)

