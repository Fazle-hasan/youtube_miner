#!/usr/bin/env python3
"""
Compare transcription models example.

This script demonstrates how to compare different transcription
models on the same audio file.
"""

from pathlib import Path

from src.transcriber import get_transcriber, list_available_models
from src.models.audio import Chunk


def main():
    """Compare different transcription models."""
    
    # Replace with path to your audio file
    audio_path = Path("./path/to/audio.wav")
    
    if not audio_path.exists():
        print(f"Audio file not found: {audio_path}")
        print("Please update the path to point to a valid WAV file.")
        return 1
    
    # Create a chunk from the audio file
    chunk = Chunk(
        index=0,
        audio_path=audio_path,
        start_time=0.0,
        end_time=30.0,  # Assuming 30 seconds
        duration=30.0,
    )
    
    print(f"Comparing models on: {audio_path}")
    print("=" * 60)
    
    # Models to compare (skip whisper-large if memory is limited)
    models_to_test = ["whisper-tiny", "faster-whisper"]
    
    results = {}
    
    for model_name in models_to_test:
        print(f"\nTranscribing with {model_name}...")
        
        try:
            transcriber = get_transcriber(model_name)
            transcript = transcriber.transcribe_chunk(chunk)
            
            results[model_name] = {
                "text": transcript.text,
                "confidence": transcript.confidence,
                "time": transcript.processing_time,
            }
            
            print(f"  Time: {transcript.processing_time:.2f}s")
            print(f"  Confidence: {transcript.confidence:.2%}")
            print(f"  Text: {transcript.text[:100]}...")
            
            # Unload model to free memory
            transcriber.unload_model()
            
        except Exception as e:
            print(f"  Error: {e}")
            results[model_name] = {"error": str(e)}
    
    # Print comparison summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for model_name, result in results.items():
        if "error" in result:
            print(f"{model_name}: ERROR - {result['error']}")
        else:
            print(f"{model_name}:")
            print(f"  Processing time: {result['time']:.2f}s")
            print(f"  Confidence: {result['confidence']:.2%}")
            print(f"  Word count: {len(result['text'].split())}")
    
    return 0


if __name__ == "__main__":
    exit(main())

