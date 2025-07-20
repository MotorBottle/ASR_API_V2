#!/usr/bin/env python3
"""
Test script for ASR API Server V2
"""

import requests
import json
import os
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:7869"
TEST_FILES_DIR = Path(".")  # Current directory where test.wav/test.mp4 will be placed

def test_health():
    """Test health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_models():
    """Test models information endpoint"""
    print("\nTesting models endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/models")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Models endpoint failed: {e}")
        return False

def test_transcribe_audio(file_path: str, output_format: str = "text"):
    """Test audio transcription"""
    print(f"\nTesting audio transcription with {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"Test file not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'audio/wav')}
            data = {
                'output_format': output_format,
                'language': 'zh',
                'enable_speaker_diarization': False,
                'hotwords': '测试 20\n语音识别 30',
            }
            
            response = requests.post(f"{API_BASE_URL}/transcribe", files=files, data=data)
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['success']}")
            print(f"Language: {result['language']}")
            print(f"Format: {result['format']}")
            print(f"Duration: {result['duration']:.2f}s")
            print(f"Transcription:\n{result['transcription']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Audio transcription failed: {e}")
        return False

def test_transcribe_video(file_path: str, output_format: str = "srt"):
    """Test video transcription"""
    print(f"\nTesting video transcription with {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"Test file not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
            data = {
                'output_format': output_format,
                'language': 'zh',
                'enable_speaker_diarization': True,
            }
            
            response = requests.post(f"{API_BASE_URL}/transcribe", files=files, data=data)
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['success']}")
            print(f"Language: {result['language']}")
            print(f"Format: {result['format']}")
            print(f"Duration: {result['duration']:.2f}s")
            print(f"Speaker Diarization: {result['speaker_diarization']}")
            print(f"Speakers: {result['speakers']}")
            print(f"Transcription:\n{result['transcription']}")
            if result['format'] == 'both' and 'transcription_srt' in result:
                print(f"SRT Content:\n{result['transcription_srt']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Video transcription failed: {e}")
        return False

def test_transcribe_url():
    """Test URL transcription"""
    print("\nTesting URL transcription...")
    
    # Example URL - replace with actual test URL
    test_url = "https://example.com/test.wav"
    
    try:
        data = {
            "url": test_url,
            "output_format": "text",
            "language": "zh",
            "enable_speaker_diarization": False,
            "hotwords": {"测试": 20, "语音识别": 30}
        }
        
        response = requests.post(f"{API_BASE_URL}/transcribe_url", json=data)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['success']}")
            print(f"Transcription: {result['transcription']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"URL transcription failed: {e}")
        return False

def main():
    """Run all tests"""
    print("ASR API Server V2 - Test Suite")
    print("=" * 40)
    
    # Test files
    test_audio = TEST_FILES_DIR / "test.wav"
    test_video = TEST_FILES_DIR / "test.mp4"
    
    # Run tests
    results = []
    
    # Basic tests
    results.append(("Health Check", test_health()))
    results.append(("Models Info", test_models()))
    
    # File-based tests
    if test_audio.exists():
        results.append(("Audio Transcription (Text)", test_transcribe_audio(str(test_audio), "text")))
        results.append(("Audio Transcription (SRT)", test_transcribe_audio(str(test_audio), "srt")))
        results.append(("Audio Transcription (Both)", test_transcribe_audio(str(test_audio), "both")))
    else:
        print(f"\nSkipping audio tests - {test_audio} not found")
    
    if test_video.exists():
        results.append(("Video Transcription (SRT)", test_transcribe_video(str(test_video), "srt")))
        results.append(("Video Transcription (Text)", test_transcribe_video(str(test_video), "text")))
        results.append(("Video Transcription (Both)", test_transcribe_video(str(test_video), "both")))
    else:
        print(f"\nSkipping video tests - {test_video} not found")
    
    # URL test (optional)
    # results.append(("URL Transcription", test_transcribe_url()))
    
    # Print results
    print("\n" + "=" * 40)
    print("Test Results:")
    print("-" * 40)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name:<30} {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    print(f"\nTotal: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}")

if __name__ == "__main__":
    main()