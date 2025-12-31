#!/usr/bin/env python3
"""
Basic usage example for YouTube Miner.

This script demonstrates how to use the YouTube Miner pipeline
to process a YouTube video and compare transcriptions with captions.
"""

from src.pipeline import YouTubeMinerPipeline


def main():
    """Run basic YouTube Miner example."""
    
    # Example YouTube URL (replace with actual URL)
    video_url = "https://www.youtube.com/watch?v=7ARBJQn6QkM"
    
    # Create pipeline with default settings
    pipeline = YouTubeMinerPipeline(
        output_dir="./output",
        model="faster-whisper",  # Options: whisper-tiny, faster-whisper, indic-seamless, whisper-large
        language="en",
        chunk_duration=30.0,
        verbose=True,
    )
    
    print(f"Processing video: {video_url}")
    print("-" * 50)
    
    # Run the full pipeline
    try:
        report = pipeline.run(video_url)
        
        # Print results
        print("\n" + "=" * 50)
        print("RESULTS")
        print("=" * 50)
        print(f"Video: {report.video_title}")
        print(f"Duration: {report.video_duration:.1f} seconds")
        print(f"Chunks processed: {report.total_chunks}")
        print(f"Processing time: {report.processing_time:.1f} seconds")
        print()
        print("Comparison Metrics:")
        print(f"  Average WER: {report.summary.avg_wer:.2%}")
        print(f"  Average CER: {report.summary.avg_cer:.2%}")
        print(f"  Average Semantic Similarity: {report.summary.avg_semantic_similarity:.2%}")
        print(f"  Average Hybrid Score: {report.summary.avg_hybrid_score:.2%}")
        print()
        # Output is organized by video ID in separate folders
        print(f"Report saved to: ./output/<video_id>/report.json")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

