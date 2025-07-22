#!/bin/bash

# ASR API Server V2 - cURL Examples

API_BASE="http://localhost:7869"

echo "ASR API Server V2 - cURL Examples"
echo "=================================="

# Health Check
echo -e "\n1. Health Check:"
curl -X GET "${API_BASE}/health" | jq .

# Models Information
echo -e "\n2. Models Information:"
curl -X GET "${API_BASE}/models" | jq .

# Transcribe Audio File (Text Format)
echo -e "\n3. Transcribe Audio File (Text Format):"
if [ -f "test.wav" ]; then
    curl -X POST \
        -F "file=@test.wav" \
        -F "output_format=text" \
        -F "language=zh" \
        -F "enable_speaker_diarization=false" \
        -F "hotwords=测试 20" \
        "${API_BASE}/transcribe" | jq .
else
    echo "test.wav not found - skipping"
fi

# Transcribe Audio File (SRT Format)
echo -e "\n4. Transcribe Audio File (SRT Format):"
if [ -f "test.wav" ]; then
    curl -X POST \
        -F "file=@test.m4a" \
        -F "output_format=srt" \
        -F "language=zh" \
        -F "enable_speaker_diarization=true" \
        "${API_BASE}/transcribe" | jq .
else
    echo "test.wav not found - skipping"
fi

# Transcribe Video File
echo -e "\n5. Transcribe Video File:"
if [ -f "test.mp4" ]; then
    curl -X POST \
        -F "file=@test.mp4" \
        -F "output_format=srt" \
        -F "language=zh" \
        -F "enable_speaker_diarization=true" \
        -F "hotwords=视频 30" \
        "${API_BASE}/transcribe" | jq .
else
    echo "test.mp4 not found - skipping"
fi

# Transcribe URL (JSON)
echo -e "\n6. Transcribe URL (JSON):"
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "url": "https://example.com/test.wav",
        "output_format": "text",
        "language": "zh",
        "enable_speaker_diarization": false,
        "hotwords": {"测试": 20, "语音识别": 30}
    }' \
    "${API_BASE}/transcribe_url" | jq .

# Transcribe with Both Text and SRT
echo -e "\n7. Transcribe with Both Text and SRT:"
if [ -f "test.wav" ]; then
    curl -X POST \
        -F "file=@test.wav" \
        -F "output_format=both" \
        -F "language=zh" \
        -F "enable_speaker_diarization=true" \
        -F "merge_threshold=100" \
        "${API_BASE}/transcribe" | jq .
else
    echo "test.wav not found - skipping"
fi

echo -e "\nDone!"