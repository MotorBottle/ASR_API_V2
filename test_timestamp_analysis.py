#!/usr/bin/env python3
"""
Test script to analyze the timestamp issue where start is correct but end is wrong
"""

def analyze_timestamp_issue():
    """Analyze the specific timestamp values from the API response"""
    
    # Data from the actual API response we captured
    problematic_examples = [
        {
            "start_time": "00:00:02,180",
            "end_time": "00:00:02,380", 
            "text": "测试测试测试测试测试再一次测再试次。",
            "start_ms": 2180,
            "end_ms": 2380
        },
        {
            "start_time": "00:00:15,800",
            "end_time": "00:00:15,960",
            "text": "你先说句话，",
            "start_ms": 15800,
            "end_ms": 15960
        },
        {
            "start_time": "00:00:17,900", 
            "end_time": "00:00:18,120",
            "text": "你好多两个字儿，",
            "start_ms": 17900,
            "end_ms": 18120
        }
    ]
    
    print("=== TIMESTAMP ANALYSIS ===")
    print("Analyzing the pattern where start timestamps are correct but end timestamps are wrong")
    print()
    
    for i, example in enumerate(problematic_examples, 1):
        duration_ms = example["end_ms"] - example["start_ms"]
        text_len = len(example["text"])
        
        print(f"Example {i}:")
        print(f"  Text: '{example['text']}'")
        print(f"  Length: {text_len} characters")
        print(f"  Timestamps: {example['start_time']} --> {example['end_time']}")
        print(f"  Duration: {duration_ms}ms")
        print(f"  Speed: {text_len / (duration_ms/1000):.1f} chars/second")
        
        # Analysis
        if duration_ms < 500:
            print(f"  ❌ PROBLEM: Duration too short for text length")
        
        # Check if end timestamp might be in different units
        # If it's in 16kHz samples: end_samples / 16000 * 1000 = end_ms
        if example["start_ms"] > 0:
            # Hypothesis: end timestamp is in 16kHz frame units
            potential_end_ms_from_frames = (example["end_ms"] / 16) * 1000
            reasonable_duration = potential_end_ms_from_frames - example["start_ms"]
            
            if reasonable_duration > 1000 and reasonable_duration < 10000:
                print(f"  💡 HYPOTHESIS: If end timestamp is in 16kHz frames:")
                print(f"     End would be: {potential_end_ms_from_frames:.0f}ms")
                print(f"     Duration would be: {reasonable_duration:.0f}ms")
                print(f"     Speed would be: {text_len / (reasonable_duration/1000):.1f} chars/second")
        
        print()
    
    print("=== PATTERN ANALYSIS ===")
    print("Key observations:")
    print("1. Start timestamps appear correct (match expected timing)")
    print("2. End timestamps are suspiciously close to start timestamps")
    print("3. All durations are under 500ms, which is impossible for the text length")
    print("4. This suggests end timestamps are in wrong units or incorrectly calculated")
    print()
    print("Most likely causes:")
    print("- FunASR returning end timestamps in frame units instead of milliseconds")
    print("- Sample rate conversion issue in audio preprocessing") 
    print("- Timestamp calculation bug in FunASR model configuration")

if __name__ == "__main__":
    analyze_timestamp_issue()