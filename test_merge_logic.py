#!/usr/bin/env python3
"""
Test the SRT merge logic directly with mock data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.subtitle_utils import generate_srt

def test_merge_logic():
    """Test SRT merge logic with controlled data"""
    
    # Test case: 3 consecutive sentences from same speaker within threshold
    test_sentences = [
        {
            'text': 'First sentence from speaker 0',
            'timestamp': [[0, 2000]],  # 0ms to 2000ms
            'spk': 0
        },
        {
            'text': 'Second sentence from speaker 0',
            'timestamp': [[2100, 4000]],  # 2100ms to 4000ms (gap: 100ms)
            'spk': 0
        },
        {
            'text': 'Third sentence from speaker 0',
            'timestamp': [[4050, 6000]],  # 4050ms to 6000ms (gap: 50ms)
            'spk': 0
        },
        {
            'text': 'Different speaker interrupts',
            'timestamp': [[6500, 8000]],  # 6500ms to 8000ms
            'spk': 1
        },
        {
            'text': 'Back to speaker 0',
            'timestamp': [[8200, 10000]],  # 8200ms to 10000ms (gap: 200ms)
            'spk': 0
        }
    ]
    
    print("Test Case 1: Merge threshold = 1000ms")
    print("Expected: First 3 sentences should merge into one block")
    print("Start time should be 0ms, end time should be 6000ms")
    print("-" * 50)
    
    result = generate_srt(test_sentences, merge_threshold=1000)
    print(result)
    
    print("\n" + "=" * 60)
    print("Test Case 2: Merge threshold = 100ms")
    print("Expected: Only first 2 sentences should merge")
    print("Block 1: 0ms to 4000ms, Block 2: 4050ms to 6000ms")
    print("-" * 50)
    
    result = generate_srt(test_sentences, merge_threshold=100)
    print(result)
    
    print("\n" + "=" * 60)
    print("Test Case 3: Merge threshold = 50ms")
    print("Expected: No merging should occur")
    print("-" * 50)
    
    result = generate_srt(test_sentences, merge_threshold=50)
    print(result)

if __name__ == "__main__":
    test_merge_logic()