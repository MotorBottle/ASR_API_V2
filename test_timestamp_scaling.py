#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
Test script to investigate potential timestamp scaling issues found in trans_utils.py
Lines 54 and 65 have "* 16" multiplications that might affect timestamp values.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.subtitle_utils import generate_srt, time_convert
# Skip trans_utils import due to numpy dependency

def test_timestamp_scaling():
    """Test if timestamp scaling in trans_utils affects SRT generation"""
    print("=== Testing Timestamp Scaling Issues ===")
    
    # Original timestamps from FunASR (in sample units?)
    original_timestamps = [
        [136.25, 148.75],  # These might be in some unit that needs scaling
        [156.25, 159.375], # Short duration in original units
        [500.0, 531.25]    # Longer duration
    ]
    
    print("Original timestamps (possibly in samples or frames):")
    for i, ts in enumerate(original_timestamps):
        duration = ts[1] - ts[0]
        print(f"  {i+1}: [{ts[0]}, {ts[1]}] (duration: {duration} units)")
    
    print("\nAfter scaling by 16 (as done in trans_utils.py line 54):")
    scaled_timestamps = []
    for ts in original_timestamps:
        scaled = [ts[0] * 16, ts[1] * 16]
        scaled_timestamps.append(scaled)
        duration = scaled[1] - scaled[0]
        print(f"  [{scaled[0]}, {scaled[1]}] (duration: {duration}ms)")
        print(f"    -> SRT: {time_convert(scaled[0])} --> {time_convert(scaled[1])}")
    
    # Test realistic scenario: if original timestamps are in 10ms units
    print("\nIf original timestamps were in 10ms units (common in ASR):")
    for i, ts in enumerate(original_timestamps):
        ms_start = ts[0] * 10  # Convert to milliseconds
        ms_end = ts[1] * 10
        duration = ms_end - ms_start
        print(f"  {i+1}: {ms_start}ms - {ms_end}ms (duration: {duration}ms)")
        print(f"    -> SRT: {time_convert(ms_start)} --> {time_convert(ms_end)}")

def test_problematic_scaling_scenario():
    """Test the specific scenario that could cause the bug"""
    print("\n=== Testing Problematic Scaling Scenario ===")
    
    # If FunASR returns timestamps in some frame/sample units
    # and they get incorrectly multiplied by 16
    
    # Example: actual audio position is 2.18 seconds = 2180ms
    # If FunASR returns this as 136.25 (some frame unit)
    # And trans_utils multiplies by 16: 136.25 * 16 = 2180
    
    print("Hypothesis: FunASR returns timestamps in frame units, trans_utils scales by 16")
    
    # Simulate FunASR output in frame units (16kHz audio, 1 frame = 1ms)
    funasr_frame_timestamps = [
        [136.25, 148.75],   # Should be 2180ms to 2380ms
        [312.5, 321.875],   # Should be 5000ms to 5150ms  
        [500, 531.25]       # Should be 8000ms to 8500ms
    ]
    
    print("Simulated FunASR frame-based timestamps:")
    for i, ts in enumerate(funasr_frame_timestamps):
        # Apply the scaling from trans_utils.py
        scaled_start = ts[0] * 16
        scaled_end = ts[1] * 16
        duration = scaled_end - scaled_start
        
        print(f"  Frame {i+1}: [{ts[0]}, {ts[1]}] frames")
        print(f"    Scaled: [{scaled_start}, {scaled_end}]ms (duration: {duration}ms)")
        print(f"    SRT: {time_convert(scaled_start)} --> {time_convert(scaled_end)}")
        
        # Check if this matches our problematic case
        if abs(scaled_start - 2180) < 1 and abs(scaled_end - 2380) < 1:
            print("    *** This matches the problematic case! ***")
        print()

def test_alternative_scaling_factors():
    """Test what the timestamps should be with different scaling factors"""
    print("=== Testing Alternative Scaling Factors ===")
    
    # The problematic case: we want 2180ms to 2380ms for reasonable speech
    # But we're getting timestamps that produce this short range
    
    # If the original timestamp represents seconds * some factor
    target_start_ms = 2180
    target_end_ms = 2380
    
    print(f"Target: {target_start_ms}ms to {target_end_ms}ms")
    
    # What would the original values need to be for different scaling factors?
    scaling_factors = [1, 10, 16, 100, 1000]
    
    for factor in scaling_factors:
        orig_start = target_start_ms / factor
        orig_end = target_end_ms / factor
        print(f"  Scale factor {factor:4d}: original would be [{orig_start:8.3f}, {orig_end:8.3f}]")
        
        # Check if this makes sense
        if factor == 16:
            print(f"    ^ Current scaling in trans_utils.py")
        elif factor == 1000:
            print(f"    ^ Would make sense if original is in seconds")
        elif factor == 10:
            print(f"    ^ Would make sense if original is in centiseconds")

def test_correct_vs_incorrect_scaling():
    """Compare correct vs incorrect timestamp scaling"""
    print("\n=== Comparing Correct vs Incorrect Scaling ===")
    
    # Simulate a sentence that should take 3 seconds to speak
    sentence_text = "This is a sentence that should take approximately three seconds to speak at normal pace."
    
    # Case 1: Correct timestamps (3 seconds duration)
    correct_start = 2000  # 2 seconds
    correct_end = 5000    # 5 seconds (3 second duration)
    
    # Case 2: Incorrectly scaled timestamps (might be the bug)
    # If original FunASR gave us values in different units
    incorrect_start = 2180  # What we're seeing
    incorrect_end = 2380    # What we're seeing (200ms duration)
    
    print("Sentence:", sentence_text[:50] + "...")
    print()
    
    print("Case 1 - Correct timestamps (3 second duration):")
    print(f"  Time range: {correct_start}ms to {correct_end}ms")
    print(f"  Duration: {correct_end - correct_start}ms ({(correct_end - correct_start)/1000:.1f} seconds)")
    print(f"  SRT: {time_convert(correct_start)} --> {time_convert(correct_end)}")
    
    words = len(sentence_text.split()) 
    wps_correct = words / ((correct_end - correct_start) / 1000)
    print(f"  Words per second: {wps_correct:.1f} (reasonable)")
    print()
    
    print("Case 2 - Problematic timestamps (200ms duration):")
    print(f"  Time range: {incorrect_start}ms to {incorrect_end}ms")
    print(f"  Duration: {incorrect_end - incorrect_start}ms ({(incorrect_end - incorrect_start)/1000:.3f} seconds)")
    print(f"  SRT: {time_convert(incorrect_start)} --> {time_convert(incorrect_end)}")
    
    wps_incorrect = words / ((incorrect_end - incorrect_start) / 1000)
    print(f"  Words per second: {wps_incorrect:.1f} (unrealistic!)")

def main():
    """Run all timestamp scaling tests"""
    print("Investigating timestamp scaling issues in trans_utils.py")
    print("=" * 60)
    
    test_timestamp_scaling()
    test_problematic_scaling_scenario()
    test_alternative_scaling_factors()
    test_correct_vs_incorrect_scaling()
    
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("The trans_utils.py file contains scaling operations (* 16) that might be")
    print("affecting timestamp values. However, these appear to be used for specific")
    print("text matching functions (proc, proc_spk) and may not be the main cause")
    print("of the SRT timestamp bug.")
    print()
    print("The actual issue is likely in the FunASR model output or the way")
    print("sentence_info timestamps are being generated/processed in asr_processor.py")
    print()
    print("To investigate further:")
    print("1. Check FunASR model configuration parameters")
    print("2. Log actual sentence_info output from the ASR model")
    print("3. Verify timestamp units used by FunASR (ms, samples, frames, etc.)")
    print("4. Check if sentence_timestamp=True is working correctly")

if __name__ == "__main__":
    main()