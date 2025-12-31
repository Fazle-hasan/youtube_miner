"""Auto-detect language from audio using Whisper Turbo."""

import logging
import os
import ssl
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import certifi
import torch

logger = logging.getLogger(__name__)

# Singleton model to avoid reloading
_detector_model = None
_detector_processor = None


def _setup_ssl_context():
    """Setup SSL context with certifi certificates for model downloads."""
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    https_handler = urllib.request.HTTPSHandler(context=ssl_context)
    opener = urllib.request.build_opener(https_handler)
    urllib.request.install_opener(opener)
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['CURL_CA_BUNDLE'] = certifi.where()


def _load_turbo_model():
    """Load Whisper Large v3 Turbo model for language detection."""
    global _detector_model, _detector_processor
    
    if _detector_model is not None:
        return _detector_model, _detector_processor
    
    logger.info("Loading Whisper Large v3 Turbo for language detection...")
    _setup_ssl_context()
    
    try:
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
        
        model_id = "openai/whisper-large-v3-turbo"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        # Load model without low_cpu_mem_usage to avoid meta tensor issues
        _detector_model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=False,  # Changed to False to avoid meta tensor error
            use_safetensors=True,
        )
        _detector_model.to(device)
        
        _detector_processor = AutoProcessor.from_pretrained(model_id)
        
        logger.info(f"Whisper Turbo loaded on {device}")
        return _detector_model, _detector_processor
        
    except Exception as e:
        logger.error(f"Failed to load Whisper Turbo: {e}")
        raise


def detect_language(audio_path: str, sample_duration: float = 30.0) -> Tuple[str, float]:
    """Detect language from audio file using Whisper Large v3 Turbo.
    
    Args:
        audio_path: Path to the audio file (WAV format preferred).
        sample_duration: Duration in seconds to sample for detection (default 30s).
        
    Returns:
        Tuple of (language_code, confidence).
        Language code is a 2-letter ISO 639-1 code (e.g., 'en', 'hi', 'es').
    """
    import soundfile as sf
    import numpy as np
    
    logger.info(f"Detecting language from: {audio_path}")
    
    # Load audio
    audio_data, sample_rate = sf.read(str(audio_path))
    audio_data = audio_data.astype(np.float32)
    
    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    
    # Take a sample from the audio (first 30 seconds by default)
    sample_frames = int(sample_duration * sample_rate)
    if len(audio_data) > sample_frames:
        # Take sample from middle of audio for better representation
        start = max(0, (len(audio_data) - sample_frames) // 2)
        audio_data = audio_data[start:start + sample_frames]
    
    # Resample to 16kHz if needed
    if sample_rate != 16000:
        import librosa
        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
    
    try:
        # Load model
        model, processor = _load_turbo_model()
        device = next(model.parameters()).device
        torch_dtype = next(model.parameters()).dtype
        
        # Process audio for language detection
        input_features = processor(
            audio_data,
            sampling_rate=16000,
            return_tensors="pt",
        ).input_features.to(device, dtype=torch_dtype)
        
        # Use Whisper's built-in language detection
        # The decoder_input_ids for language detection start with <|startoftranscript|>
        with torch.no_grad():
            # Get the language token logits
            encoder_outputs = model.get_encoder()(input_features)
            
            # Create decoder input with just the start token
            decoder_input_ids = torch.tensor([[model.config.decoder_start_token_id]]).to(device)
            
            # Get logits for the next token (which should be the language token)
            outputs = model(
                encoder_outputs=encoder_outputs,
                decoder_input_ids=decoder_input_ids,
            )
            
            # Get the logits for the language token position
            logits = outputs.logits[0, -1]
            
            # Get language token IDs from the tokenizer
            # Whisper uses special tokens like <|en|>, <|hi|>, <|es|>, etc.
            lang_tokens = {}
            for token, token_id in processor.tokenizer.get_vocab().items():
                if token.startswith("<|") and token.endswith("|>") and len(token) == 6:
                    # This is a language token like <|en|>, <|hi|>
                    lang_code = token[2:4]
                    lang_tokens[lang_code] = token_id
            
            # Find the language with highest probability
            best_lang = "en"
            best_score = float("-inf")
            
            for lang_code, token_id in lang_tokens.items():
                score = logits[token_id].item()
                if score > best_score:
                    best_score = score
                    best_lang = lang_code
            
            # Calculate confidence using softmax
            import torch.nn.functional as F
            lang_token_ids = list(lang_tokens.values())
            lang_logits = logits[lang_token_ids]
            probs = F.softmax(lang_logits, dim=0)
            
            # Find confidence for best language
            best_idx = list(lang_tokens.keys()).index(best_lang)
            confidence = probs[best_idx].item()
            
            logger.info(f"Detected language: {best_lang} (confidence: {confidence:.2f})")
            return best_lang, confidence
            
    except Exception as e:
        logger.error(f"Whisper language detection failed: {e}")
        
        # Fallback: Analyze the audio with a simple transcription and check script
        try:
            model, processor = _load_turbo_model()
            device = next(model.parameters()).device
            torch_dtype = next(model.parameters()).dtype
            
            input_features = processor(
                audio_data,
                sampling_rate=16000,
                return_tensors="pt",
            ).input_features.to(device, dtype=torch_dtype)
            
            with torch.no_grad():
                predicted_ids = model.generate(input_features, max_new_tokens=50)
                text = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            
            detected_lang = _guess_language_from_text(text)
            logger.info(f"Detected language (text analysis fallback): {detected_lang}")
            return detected_lang, 0.7
            
        except Exception as e2:
            logger.error(f"Fallback detection also failed: {e2}")
            return "en", 0.5


def detect_language_simple(audio_path: str) -> str:
    """Simple language detection that returns just the language code.
    
    Uses first chunk's audio for detection.
    
    Args:
        audio_path: Path to audio file.
        
    Returns:
        2-letter language code (e.g., 'en', 'hi', 'es').
    """
    try:
        lang, confidence = detect_language(audio_path)
        logger.info(f"Language detected: {lang} (confidence: {confidence:.2f})")
        # Ensure we never return None
        if lang is None or lang == "":
            logger.warning("Language detection returned None, defaulting to English")
            return "en"
        return lang
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        logger.info("Falling back to English")
        return "en"


def _guess_language_from_text(text: str) -> str:
    """Guess language from transcribed text based on character analysis.
    
    Args:
        text: Transcribed text.
        
    Returns:
        Guessed language code.
    """
    if not text:
        return "en"
    
    # Check for specific character ranges
    devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    japanese_count = sum(1 for c in text if '\u3040' <= c <= '\u30FF' or '\u4e00' <= c <= '\u9fff')
    korean_count = sum(1 for c in text if '\uAC00' <= c <= '\uD7AF')
    cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    
    total = len(text)
    if total == 0:
        return "en"
    
    # Determine language based on script
    if devanagari_count / total > 0.2:
        return "hi"
    elif chinese_count / total > 0.2:
        return "zh"
    elif arabic_count / total > 0.2:
        return "ar"
    elif korean_count / total > 0.2:
        return "ko"
    elif cyrillic_count / total > 0.2:
        return "ru"
    elif japanese_count / total > 0.2:
        return "ja"
    
    # Default to English
    return "en"


# Language code mapping to full names
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "zh": "Chinese",
    "ar": "Arabic",
    "ru": "Russian",
    "ko": "Korean",
    "pt": "Portuguese",
    "it": "Italian",
    "nl": "Dutch",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
}


def get_language_name(code: str) -> str:
    """Get full language name from code."""
    if code is None:
        return "Unknown"
    return LANGUAGE_NAMES.get(code, code.upper() if isinstance(code, str) else "Unknown")

