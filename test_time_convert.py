#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
Test script for time_convert function in subtitle_utils.py
Testing for bugs related to SRT time formatting, especially millisecond padding.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.subtitle_utils import time_convert, Text2SRT, generate_srt

def test_time_convert_basic():
    """Test basic time conversion functionality"""
    print("=== Testing Basic Time Conversion ===")
    
    test_cases = [
        # (milliseconds, expected_srt_format)
        (0, "00:00:00,000"),
        (1000, "00:00:01,000"),
        (60000, "00:01:00,000"),
        (3600000, "01:00:00,000"),
        (3661234, "01:01:01,234"),
        (2180, "00:00:02,180"),
        (2380, "00:00:02,380"),
        (200, "00:00:00,200"),
        (50, "00:00:00,050"),
        (5, "00:00:00,005"),
        (1, "00:00:00,001"),
        (999, "00:00:00,999"),
        (1999, "00:00:01,999"),
        (61234, "00:01:01,234"),
    ]
    
    all_passed = True
    for ms, expected in test_cases:
        result = time_convert(ms)
        status = "✓" if result == expected else "✗"
        print(f"{status} {ms}ms -> {result} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_edge_cases():
    """Test edge cases that might cause issues"""
    print("\n=== Testing Edge Cases ===")
    
    edge_cases = [
        # Very small values
        (0, "00:00:00,000"),
        (1, "00:00:00,001"),
        (10, "00:00:00,010"),
        (100, "00:00:00,100"),
        
        # Values that could have zfill issues
        (5, "00:00:00,005"),
        (50, "00:00:00,050"),
        (500, "00:00:00,500"),
        
        # Large values
        (7200000, "02:00:00,000"),  # 2 hours
        (86400000, "24:00:00,000"), # 24 hours
        
        # Fractional seconds that might cause rounding issues
        (1500, "00:00:01,500"),
        (2999, "00:00:02,999"),
    ]
    
    all_passed = True
    for ms, expected in edge_cases:
        result = time_convert(ms)
        status = "✓" if result == expected else "✗"
        print(f"{status} {ms}ms -> {result} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_problematic_scenario():
    """Test the specific scenario mentioned in the bug report"""
    print("\n=== Testing Problematic Scenario (Short Time Ranges) ===")
    
    # Simulate the problematic case: long text with short time range
    start_ms = 2180
    end_ms = 2380
    time_diff = end_ms - start_ms
    
    print(f"Start time: {start_ms}ms -> {time_convert(start_ms)}")
    print(f"End time: {end_ms}ms -> {time_convert(end_ms)}")
    print(f"Time difference: {time_diff}ms ({time_diff/1000:.3f} seconds)")
    
    # Test with Text2SRT class
    long_text = "This is a very long piece of text that should normally take much longer than 200 milliseconds to speak naturally."
    timestamp = [(start_ms, end_ms)]
    
    t2s = Text2SRT(long_text, timestamp)
    srt_output = t2s.srt()
    
    print(f"\nSRT Output:")
    print(srt_output)
    
    # Check if this looks reasonable
    if time_diff < 1000:  # Less than 1 second
        print(f"⚠️  WARNING: Time range is very short ({time_diff}ms) for long text content")
        print("   This might indicate a bug in timestamp calculation upstream")
    
    return True

def test_millisecond_padding():
    """Specifically test the zfill(3) padding for milliseconds"""
    print("\n=== Testing Millisecond Padding (zfill issue) ===")
    
    padding_tests = [
        # Test cases where zfill(3) behavior matters
        (1, "00:00:00,001"),    # Single digit
        (12, "00:00:00,012"),   # Two digits  
        (123, "00:00:00,123"),  # Three digits
        (1234, "00:00:01,234"), # More than 3 digits (should truncate to last 3)
    ]
    
    all_passed = True
    for ms, expected in padding_tests:
        result = time_convert(ms)
        status = "✓" if result == expected else "✗" 
        print(f"{status} {ms}ms -> {result} (expected: {expected})")
        if result != expected:
            all_passed = False
            
        # Also test the millisecond part extraction
        tail = ms % 1000
        padded_tail = str(tail).zfill(3)
        print(f"    Millisecond part: {ms} % 1000 = {tail} -> zfill(3) = '{padded_tail}'")
    
    return all_passed

def test_generate_srt_time_ranges():
    """Test the generate_srt function for time range issues"""
    print("\n=== Testing generate_srt Time Ranges ===")
    
    # Create test data that might produce short time ranges
    sentence_list = [
        {
            'text': 'Hello world',
            'timestamp': [(1000, 2000)],  # 1 second duration
            'spk': 0
        },
        {
            'text': 'This is a much longer sentence that should take more time to speak naturally but has a very short timestamp range',
            'timestamp': [(2100, 2300)],  # Only 200ms duration - this is the bug scenario
            'spk': 0
        },
        {
            'text': 'Another sentence',
            'timestamp': [(3000, 4000)],  # 1 second duration
            'spk': 1
        }
    ]
    
    srt_result = generate_srt(sentence_list, merge_threshold=8000)
    print("Generated SRT:")
    print(srt_result)
    
    # Check for unreasonably short time ranges
    lines = srt_result.split('\n')
    for i, line in enumerate(lines):
        if '-->' in line:
            # Parse the timestamp line
            parts = line.split(' --> ')
            if len(parts) == 2:
                start_str, end_str = parts
                # Convert back to milliseconds for comparison
                start_ms = parse_srt_time_to_ms(start_str)
                end_ms = parse_srt_time_to_ms(end_str)
                duration = end_ms - start_ms
                
                print(f"Entry {(i//4)+1}: {start_str} --> {end_str} (Duration: {duration}ms)")
                if duration < 500:  # Less than 500ms might be problematic
                    print(f"    ⚠️  WARNING: Very short duration ({duration}ms) detected")
    
    return True

def parse_srt_time_to_ms(time_str):
    """Helper function to parse SRT time format back to milliseconds"""
    # Format: "HH:MM:SS,mmm"
    time_part, ms_part = time_str.split(',')
    h, m, s = map(int, time_part.split(':'))
    ms = int(ms_part)
    
    total_ms = (h * 3600 + m * 60 + s) * 1000 + ms
    return total_ms

def main():
    """Run all tests"""
    print("Testing time_convert function for SRT timestamp bugs\n")
    
    results = []
    results.append(test_time_convert_basic())
    results.append(test_edge_cases())
    results.append(test_problematic_scenario())
    results.append(test_millisecond_padding())
    results.append(test_generate_srt_time_ranges())
    
    print(f"\n=== Test Summary ===")
    if all(results):
        print("✓ All tests passed!")
        print("\nAnalysis:")
        print("- The time_convert function appears to work correctly")
        print("- The zfill(3) padding for milliseconds is working as expected")
        print("- Short time ranges (like 200ms) are likely due to upstream timestamp calculation issues")
        print("- The SRT formatting itself is not the source of the bug")
    else:
        print("✗ Some tests failed!")
        print("- There may be issues with the time_convert function")
    
    print(f"\nConclusion:")
    print("If you're seeing very short time ranges like '00:00:02,180 --> 00:00:02,380' for long text,")
    print("the issue is likely in the timestamp data being passed TO the time_convert function,")
    print("not in the time_convert function itself. Check the ASR model output or timestamp processing logic.")

if __name__ == "__main__":
    main()