"""ai4bharat/indic-seamless transcriber for multilingual support."""

import gc
import logging
import os
import ssl
import time
import urllib.request
from pathlib import Path
from typing import Optional

import certifi
import torch
from transformers import (
    SeamlessM4Tv2ForSpeechToText,
    SeamlessM4TFeatureExtractor,
    SeamlessM4TTokenizer,
)
from huggingface_hub import login

from src.models.audio import Chunk
from src.models.transcript import Transcript
from src.transcriber.base import BaseTranscriber

# Load environment variables from .env file (optional - graceful fallback)
try:
    from dotenv import load_dotenv
    _project_root = Path(__file__).parent.parent.parent
    load_dotenv(_project_root / ".env")
except ImportError:
    # python-dotenv not installed - user must set env vars manually
    pass

# Set MPS memory allocation to allow using all GPU memory
os.environ.setdefault('PYTORCH_MPS_HIGH_WATERMARK_RATIO', '0.0')

logger = logging.getLogger(__name__)


def _clear_gpu_memory():
    """Clear GPU memory cache to free up space."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    elif torch.backends.mps.is_available():
        torch.mps.empty_cache()
        if hasattr(torch.mps, 'synchronize'):
            torch.mps.synchronize()
    logger.info("GPU memory cleared")


def _setup_ssl_context():
    """Setup SSL context with certifi certificates for model downloads."""
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    https_handler = urllib.request.HTTPSHandler(context=ssl_context)
    opener = urllib.request.build_opener(https_handler)
    urllib.request.install_opener(opener)
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['CURL_CA_BUNDLE'] = certifi.where()


def _setup_hf_auth():
    """Setup Hugging Face authentication for gated models."""
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        try:
            login(token=hf_token, add_to_git_credential=False)
            logger.info("Hugging Face authentication successful")
        except Exception as e:
            logger.warning(f"Hugging Face login failed: {e}")
    else:
        logger.warning("HF_TOKEN not set in .env file. Some models may require authentication.")


class IndicSeamlessTranscriber(BaseTranscriber):
    """Transcriber using ai4bharat/indic-seamless model (SeamlessM4Tv2).
    
    Indic-Seamless is a multilingual speech-to-text model
    supporting 100+ languages including Indian languages.
    
    Uses SeamlessM4Tv2ForSpeechToText for proper model architecture.
    
    Note: This is a gated model. Set HF_TOKEN environment variable for authentication.
    
    Memory: ~4GB
    Speed: Medium (faster on GPU/CUDA)
    Languages: 100+ including Hindi, Tamil, Telugu, etc.
    
    Example:
        >>> transcriber = IndicSeamlessTranscriber()
        >>> transcript = transcriber.transcribe_chunk(chunk)
        >>> print(transcript.text)
    """
    
    MODEL_NAME = "ai4bharat/indic-seamless"
    
    def __init__(
        self,
        language: str = "en",
        device: Optional[str] = None,
    ):
        """Initialize Indic-Seamless transcriber.
        
        Args:
            language: Target language for transcription (e.g., 'en', 'hi', 'ta').
            device: Device to use ('cuda', 'cpu', or None for auto).
        """
        super().__init__(model_name="indic-seamless", language=language)
        
        # Device selection: CUDA > CPU (skip MPS - causes memory issues)
        if device:
            self.device = device
        elif torch.cuda.is_available():
            self.device = "cuda:0"
        else:
            self.device = "cpu"
        
        self._processor = None
        self._tokenizer = None
        self._torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        logger.info(f"Indic-Seamless will use device: {self.device}, dtype: {self._torch_dtype}")
    
    def load_model(self) -> None:
        """Load Indic-Seamless model with correct v2 architecture."""
        logger.info(f"Loading {self.MODEL_NAME} model (SeamlessM4Tv2)...")
        
        # Clear GPU memory before loading
        _clear_gpu_memory()
        
        # Setup SSL context for model download
        _setup_ssl_context()
        
        # Setup Hugging Face authentication
        _setup_hf_auth()
        
        # Get token for model loading
        hf_token = os.environ.get("HF_TOKEN")
        
        try:
            # Use correct v2 classes for indic-seamless
            # SeamlessM4Tv2ForSpeechToText - for speech-to-text only (more efficient)
            self._model = SeamlessM4Tv2ForSpeechToText.from_pretrained(
                self.MODEL_NAME,
                token=hf_token,
            )
            
            # SeamlessM4TFeatureExtractor - for audio processing
            self._processor = SeamlessM4TFeatureExtractor.from_pretrained(
                self.MODEL_NAME,
                token=hf_token,
            )
            
            # SeamlessM4TTokenizer - for decoding output
            self._tokenizer = SeamlessM4TTokenizer.from_pretrained(
                self.MODEL_NAME,
                token=hf_token,
            )
            
            # Move model to device
            self._model = self._model.to(self.device)
            
            logger.info(f"Indic-Seamless model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load Indic-Seamless: {e}")
            logger.error("Make sure HF_TOKEN is set and you have access to the model at:")
            logger.error("https://huggingface.co/ai4bharat/indic-seamless")
            raise
    
    def transcribe_chunk(self, chunk: Chunk) -> Transcript:
        """Transcribe audio chunk using Indic-Seamless v2.
        
        Args:
            chunk: Audio chunk to transcribe.
            
        Returns:
            Transcript object with transcription results.
        """
        if self._model is None or self._processor is None or self._tokenizer is None:
            self.load_model()
        
        if not chunk.exists:
            raise FileNotFoundError(f"Chunk file not found: {chunk.audio_path}")
        
        start_time = time.time()
        
        try:
            import soundfile as sf
            import numpy as np
            
            # Load audio using soundfile (avoids torchaudio/torchcodec issues)
            audio_array, sample_rate = sf.read(str(chunk.audio_path))
            
            # Convert to float32
            audio_array = audio_array.astype(np.float32)
            
            # Handle stereo -> mono conversion
            if len(audio_array.shape) > 1:
                audio_array = audio_array.mean(axis=1)
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                import librosa
                audio_array = librosa.resample(
                    audio_array,
                    orig_sr=sample_rate,
                    target_sr=16000
                )
            
            # Process audio with feature extractor
            audio_inputs = self._processor(
                audio_array,
                sampling_rate=16000,
                return_tensors="pt"
            )
            
            # Move inputs to device
            audio_inputs = {k: v.to(self.device) for k, v in audio_inputs.items()}
            
            # Generate transcription
            with torch.no_grad():
                output_tokens = self._model.generate(
                    **audio_inputs,
                    tgt_lang=self._get_language_code(),
                )
            
            # Decode output with tokenizer
            text_tokens = output_tokens[0].cpu().numpy().squeeze()
            text = self._tokenizer.decode(
                text_tokens,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            text = ""
        
        processing_time = time.time() - start_time
        
        logger.debug(
            f"Transcribed chunk {chunk.index}: {len(text)} chars in {processing_time:.2f}s"
        )
        
        return Transcript(
            text=text.strip(),
            model_name=self.model_name,
            chunk_index=chunk.index,
            confidence=0.8,  # Seamless doesn't provide confidence scores
            language=self.language,
            processing_time=processing_time,
        )
    
    def _get_language_code(self) -> str:
        """Convert language code to Seamless format.
        
        Returns:
            Language code in Seamless format (3-letter codes).
        """
        # Handle "auto" language - default to Hindi for Indic model
        if self.language == "auto":
            return "hin"
        
        # Map common 2-letter codes to Seamless 3-letter codes
        lang_map = {
            "en": "eng",
            "hi": "hin",
            "ta": "tam",
            "te": "tel",
            "bn": "ben",
            "mr": "mar",
            "gu": "guj",
            "kn": "kan",
            "ml": "mal",
            "pa": "pan",
            "or": "ory",  # Odia
            "as": "asm",  # Assamese
            "ur": "urd",  # Urdu
            "ne": "npi",  # Nepali
            "si": "sin",  # Sinhala
        }
        
        return lang_map.get(self.language, self.language)
    
    def unload_model(self) -> None:
        """Unload model from memory."""
        if self._model is not None:
            del self._model
        if self._processor is not None:
            del self._processor
        if self._tokenizer is not None:
            del self._tokenizer
        
        self._model = None
        self._processor = None
        self._tokenizer = None
        
        # Clear GPU cache
        _clear_gpu_memory()
        logger.info("Indic-Seamless model unloaded")
