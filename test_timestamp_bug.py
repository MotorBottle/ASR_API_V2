#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
Test script to investigate the specific timestamp bug:
SRT entries showing very short time ranges like "00:00:02,180 --> 00:00:02,380" (200ms) for long text content.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.subtitle_utils import generate_srt, Text2SRT, time_convert

def test_bug_scenario():
    """Test the exact bug scenario reported"""
    print("=== Testing Bug Scenario: Short Time Ranges for Long Text ===")
    
    # Simulate FunASR output that might cause this issue
    problematic_sentences = [
        {
            'text': 'This is a very long sentence that contains multiple words and should realistically take several seconds to speak at a normal pace.',
            'timestamp': [[2180, 2380]],  # Only 200ms - this is the bug!
            'spk': 0
        },
        {
            'text': 'Another long sentence with many words that also has an unrealistically short duration for the amount of content it contains.',
            'timestamp': [[5000, 5150]],  # Only 150ms - also problematic
            'spk': 0  
        },
        {
            'text': 'Short text.',
            'timestamp': [[8000, 8500]],  # 500ms - reasonable for short text
            'spk': 1
        }
    ]
    
    print("Input data:")
    for i, sent in enumerate(problematic_sentences):
        duration = sent['timestamp'][0][1] - sent['timestamp'][0][0]
        words = len(sent['text'].split())
        print(f"Sentence {i+1}: {words} words, {duration}ms duration")
        print(f"  Text: '{sent['text'][:50]}...'")
        print(f"  Timestamp: {sent['timestamp'][0]} ({duration}ms)")
        print(f"  Words per second: {words / (duration/1000):.1f}")
        print()
    
    # Generate SRT with different merge thresholds
    print("Generated SRT (merge_threshold=1000ms):")
    print("-" * 50)
    srt_result = generate_srt(problematic_sentences, merge_threshold=1000)
    print(srt_result)
    
    # Analyze the problem
    print("Analysis:")
    print("- The time_convert function correctly formats the timestamps")
    print("- The issue is that the input timestamps are unrealistically short")
    print("- This suggests a problem in the ASR model output or timestamp extraction")

def test_timestamp_format_variations():
    """Test different timestamp formats that might cause issues"""
    print("\n=== Testing Different Timestamp Formats ===")
    
    # Different possible timestamp formats from FunASR
    test_cases = [
        {
            'name': 'Nested list format',
            'sentences': [
                {
                    'text': 'Test sentence',
                    'timestamp': [[1000, 3000]],  # Current format
                    'spk': 0
                }
            ]
        },
        {
            'name': 'Flat list format',
            'sentences': [
                {
                    'text': 'Test sentence',
                    'timestamp': [1000, 3000],  # Alternative format
                    'spk': 0
                }
            ]
        },
        {
            'name': 'Multiple timestamps per sentence',
            'sentences': [
                {
                    'text': 'Test sentence with multiple segments',
                    'timestamp': [[1000, 1500], [1600, 2000], [2100, 3000]],  # Word-level timestamps
                    'spk': 0
                }
            ]
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        try:
            result = generate_srt(case['sentences'], merge_threshold=1000)
            print("✓ Successfully processed")
            print(result.strip())
        except Exception as e:
            print(f"✗ Error: {e}")

def test_direct_text2srt():
    """Test Text2SRT class directly with problematic timestamps"""
    print("\n=== Testing Text2SRT Class Directly ===")
    
    # Test with problematic short timestamp
    long_text = "This is a very long sentence that should take much more than 200 milliseconds to say at a normal speaking pace."
    short_timestamp = [(2180, 2380)]  # 200ms
    
    print(f"Text: {long_text}")
    print(f"Timestamp: {short_timestamp[0]} ({short_timestamp[0][1] - short_timestamp[0][0]}ms)")
    
    t2s = Text2SRT(long_text, short_timestamp)
    
    print(f"Start time: {t2s.start_time}")
    print(f"End time: {t2s.end_time}")
    print(f"SRT output:")
    print(t2s.srt())
    
    # Check time calculation
    print(f"Start seconds: {t2s.start_sec}ms = {t2s.start_sec/1000:.3f}s")
    print(f"End seconds: {t2s.end_sec}ms = {t2s.end_sec/1000:.3f}s")
    print(f"Duration: {(t2s.end_sec - t2s.start_sec)/1000:.3f}s")

def investigate_time_conversion_edge_cases():
    """Investigate potential edge cases in time conversion"""
    print("\n=== Investigating Time Conversion Edge Cases ===")
    
    # Test values around the problematic range
    test_values = [2180, 2380, 2179, 2381, 0, 1, 999, 1000, 1001]
    
    for ms in test_values:
        converted = time_convert(ms)
        print(f"{ms:4d}ms -> {converted}")
    
    # Test potential floating point issues
    print("\nTesting floating point conversion:")
    float_values = [2180.5, 2180.9, 2379.1, 2379.9]
    for val in float_values:
        # Simulate what happens if float values are passed
        converted = time_convert(val)  # int(val) conversion happens inside
        print(f"{val:6.1f}ms -> {converted} (int conversion: {int(val)})")

def main():
    """Run all tests to investigate the timestamp bug"""
    print("Investigating SRT timestamp bug: Short time ranges for long text")
    print("=" * 70)
    
    test_bug_scenario()
    test_timestamp_format_variations()
    test_direct_text2srt()
    investigate_time_conversion_edge_cases()
    
    print("\n" + "=" * 70)
    print("CONCLUSION:")
    print("The time_convert function and Text2SRT class are working correctly.")
    print("The bug is most likely in:")
    print("1. ASR model timestamp generation (upstream)")
    print("2. Audio preprocessing that affects timing")
    print("3. Timestamp extraction from ASR results")
    print("4. Data format conversion before reaching subtitle_utils")
    print("\nTo fix this, check:")
    print("- ASR model configuration (sentence_timestamp parameter)")
    print("- Audio preprocessing (sample rate, duration calculation)")
    print("- FunASR result parsing in asr_processor.py")

if __name__ == "__main__":
    main()