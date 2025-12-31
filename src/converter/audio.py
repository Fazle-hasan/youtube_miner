"""Audio format converter using pydub."""

import logging
from pathlib import Path
from typing import Optional

from pydub import AudioSegment

from src.models.audio import AudioFile

logger = logging.getLogger(__name__)


class AudioConverter:
    """Convert audio files to WAV format (16kHz, mono).
    
    Example:
        >>> converter = AudioConverter()
        >>> wav_file = converter.convert(audio_file)
        >>> print(wav_file.sample_rate)  # 16000
    """
    
    DEFAULT_SAMPLE_RATE = 16000
    DEFAULT_CHANNELS = 1  # Mono
    
    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS,
    ):
        """Initialize the converter.
        
        Args:
            sample_rate: Target sample rate in Hz (default: 16000).
            channels: Number of audio channels (default: 1 for mono).
        """
        self.sample_rate = sample_rate
        self.channels = channels
    
    def convert(
        self,
        audio_file: AudioFile,
        output_path: Optional[Path] = None,
    ) -> AudioFile:
        """Convert audio file to WAV format.
        
        Args:
            audio_file: Input AudioFile to convert.
            output_path: Optional output path. If None, uses same directory with .wav extension.
            
        Returns:
            New AudioFile object representing the converted WAV file.
            
        Raises:
            FileNotFoundError: If input file doesn't exist.
            RuntimeError: If conversion fails.
        """
        if not audio_file.exists:
            raise FileNotFoundError(f"Audio file not found: {audio_file.path}")
        
        # Determine output path
        if output_path is None:
            output_path = audio_file.path.with_suffix('.wav')
        else:
            output_path = Path(output_path)
        
        # Skip if already in correct format
        if (
            audio_file.format == 'wav'
            and audio_file.sample_rate == self.sample_rate
            and audio_file.channels == self.channels
        ):
            logger.info("Audio already in correct format, skipping conversion")
            return audio_file
        
        logger.info(f"Converting {audio_file.path} to WAV ({self.sample_rate}Hz, {self.channels}ch)")
        
        try:
            # Load audio
            audio = AudioSegment.from_file(str(audio_file.path))
            
            # Convert to mono if needed
            if self.channels == 1 and audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Resample if needed
            if audio.frame_rate != self.sample_rate:
                audio = audio.set_frame_rate(self.sample_rate)
            
            # Export as WAV
            audio.export(
                str(output_path),
                format="wav",
                parameters=["-acodec", "pcm_s16le"]
            )
            
            # Get actual duration
            duration = len(audio) / 1000.0  # pydub uses milliseconds
            
            logger.info(f"Converted to: {output_path} ({duration:.1f}s)")
            
            return AudioFile(
                path=output_path,
                format="wav",
                duration=duration,
                sample_rate=self.sample_rate,
                channels=self.channels,
                source_url=audio_file.source_url,
            )
            
        except Exception as e:
            raise RuntimeError(f"Conversion failed: {e}")
    
    def convert_from_path(self, input_path: str, output_path: Optional[str] = None) -> AudioFile:
        """Convert audio file from path string.
        
        Args:
            input_path: Path to input audio file.
            output_path: Optional output path.
            
        Returns:
            AudioFile object representing the converted file.
        """
        input_path = Path(input_path)
        
        # Create a temporary AudioFile
        audio_file = AudioFile(
            path=input_path,
            format=input_path.suffix[1:],
            duration=0,  # Will be determined during conversion
        )
        
        return self.convert(
            audio_file,
            output_path=Path(output_path) if output_path else None
        )
    
    @staticmethod
    def get_audio_info(file_path: str) -> dict:
        """Get audio file information.
        
        Args:
            file_path: Path to audio file.
            
        Returns:
            Dictionary with audio metadata.
        """
        audio = AudioSegment.from_file(file_path)
        
        return {
            "duration": len(audio) / 1000.0,
            "sample_rate": audio.frame_rate,
            "channels": audio.channels,
            "sample_width": audio.sample_width,
            "frame_count": len(audio.get_array_of_samples()),
        }

