#!/usr/bin/env python3
"""
Text comparison example.

This script demonstrates how to use the comparison metrics
to evaluate transcription quality.
"""

from src.comparator import HybridScore, TextNormalizer


def main():
    """Demonstrate text comparison metrics."""
    
    # Example texts (model output vs YouTube captions)
    reference = "Hello and welcome to this podcast episode where we discuss machine learning"
    hypothesis = "Hello and welcome to this podcast episode where we discus machine learning"
    
    print("TEXT COMPARISON DEMO")
    print("=" * 60)
    print()
    print("Reference (YouTube caption):")
    print(f"  {reference}")
    print()
    print("Hypothesis (Model output):")
    print(f"  {hypothesis}")
    print()
    
    # Show normalization
    normalizer = TextNormalizer()
    norm_ref, norm_hyp = normalizer.normalize_pair(reference, hypothesis)
    
    print("After normalization:")
    print(f"  Reference:  {norm_ref}")
    print(f"  Hypothesis: {norm_hyp}")
    print()
    
    # Calculate all metrics
    scorer = HybridScore(normalize=True)
    result = scorer.compare(reference, hypothesis)
    
    print("METRICS")
    print("-" * 40)
    print(f"Word Error Rate (WER):     {result.wer:.2%}")
    print(f"Character Error Rate (CER): {result.cer:.2%}")
    print(f"Semantic Similarity:        {result.semantic_similarity:.2%}")
    print(f"Hybrid Score (SeMaScore):   {result.hybrid_score:.2%}")
    print()
    
    # Interpret results
    print("INTERPRETATION")
    print("-" * 40)
    
    if result.wer < 0.1:
        print("✓ Excellent word-level accuracy (WER < 10%)")
    elif result.wer < 0.2:
        print("○ Good word-level accuracy (WER 10-20%)")
    else:
        print("✗ Poor word-level accuracy (WER > 20%)")
    
    if result.semantic_similarity > 0.9:
        print("✓ Excellent meaning preservation (>90% similar)")
    elif result.semantic_similarity > 0.8:
        print("○ Good meaning preservation (80-90% similar)")
    else:
        print("✗ Meaning may be lost (<80% similar)")
    
    print()
    print("Additional examples:")
    print("-" * 40)
    
    # More examples
    examples = [
        ("The quick brown fox jumps over the lazy dog", 
         "The quick brown fox jumped over the lazy dog"),
        ("Machine learning is a subset of artificial intelligence",
         "ML is a subset of AI"),
        ("Hello world",
         "Goodbye world"),
    ]
    
    for ref, hyp in examples:
        result = scorer.compare(ref, hyp)
        print(f"\nRef: {ref}")
        print(f"Hyp: {hyp}")
        print(f"WER: {result.wer:.2%}, Semantic: {result.semantic_similarity:.2%}")
    
    return 0


if __name__ == "__main__":
    exit(main())

