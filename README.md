# ASR API Server V2

A FastAPI-based server for audio/video transcription services, extracted and optimized from the Private-ASR project.

## Features

- **Audio/Video Transcription**: Support for various audio and video formats
- **Multiple Output Formats**: Text and SRT subtitle formats
- **Speaker Diarization**: Identify and separate different speakers
- **Hotwords Support**: Improve recognition accuracy with custom hotwords
- **Speaker Naming**: Replace speaker IDs with custom names
- **Multi-language Support**: Chinese (zh) and English (en)
- **Docker Deployment**: Both CPU and GPU support
- **REST API**: Clean HTTP endpoints for easy integration

## Supported Formats

### Input Formats
- **Audio**: `.wav`, `.mp3`, `.aac`, `.m4a`, `.flac`
- **Video**: `.mp4`, `.avi`, `.mkv`, `.mov`, `.webm`

### Output Formats
- **Text**: Plain text transcription
- **SRT**: Timestamped subtitle format with speaker labels

## Quick Start

### Using Docker (Recommended)

#### CPU Deployment
```bash
# Build and run CPU version
docker-compose --profile cpu up -d

# Or build manually
docker build -t asr-api-v2:cpu .
docker run -p 7869:7869 -e DEVICE=cpu asr-api-v2:cpu
```

#### GPU Deployment
```bash
# Build and run GPU version (requires NVIDIA Docker)
docker-compose --profile gpu up -d

# Or build manually
docker build -f Dockerfile.gpu -t asr-api-v2:gpu .
docker run --gpus all -p 7869:7869 -e DEVICE=cuda:0 asr-api-v2:gpu
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env as needed
```

3. Run the server:
```bash
python main.py
```

## API Endpoints

### Health Check
```http
GET /health
```

### Get Model Information
```http
GET /models
```

### Transcribe File
```http
POST /transcribe
Content-Type: multipart/form-data

file: (audio/video file)
output_format: text|srt|both (default: text)
language: zh|en (default: zh)
enable_speaker_diarization: true|false (default: false)
hotwords: (optional, one per line with format "word weight")
```

### Transcribe URL
```http
POST /transcribe_url
Content-Type: application/json

{
  "url": "https://example.com/audio.wav",
  "output_format": "both",
  "language": "zh",
  "enable_speaker_diarization": false,
  "hotwords": {"测试": 20, "语音识别": 30}
}
```

## API Response Format

### Standard Response (text/srt)
```json
{
  "success": true,
  "transcription": "transcribed text or SRT content",
  "format": "text",
  "language": "zh",
  "speaker_diarization": false,
  "duration": 123.45,
  "speakers": ["spk0", "spk1"]
}
```

### Both Format Response
When `output_format: "both"`, you get both text and SRT:
```json
{
  "success": true,
  "transcription": "plain text transcription",
  "transcription_srt": "1  [spk0]\n00:00:01,300 --> 00:00:03,460\nhello world\n\n",
  "format": "both",
  "language": "zh",
  "speaker_diarization": true,
  "duration": 123.45,
  "speakers": ["spk0", "spk1"]
}
```

## Configuration

### Environment Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 7869)
- `DEVICE`: Processing device (cpu or cuda:0)
- `LANGUAGE`: Default language (zh or en)
- `LOG_LEVEL`: Logging level (default: INFO)

### Hotwords Format

Hotwords can be provided to improve recognition accuracy:

**Form data format:**
```
测试 20
语音识别 30
重要词汇 40
```

**JSON format:**
```json
{
  "测试": 20,
  "语音识别": 30,
  "重要词汇": 40
}
```

### Speaker Names

Replace speaker IDs with custom names:

**Form data format:**
```
spk0:张三,spk1:李四,spk2:王五
```

**JSON format:**
```json
{
  "spk0": "张三",
  "spk1": "李四",
  "spk2": "王五"
}
```

## Testing

### Using the Test Script

1. Place test files in the project directory:
   - `test.wav` - Audio file for testing
   - `test.mp4` - Video file for testing

2. Run the test script:
```bash
python test_api.py
```

### Manual Testing with cURL

#### Health Check
```bash
curl -X GET http://localhost:7869/health
```

#### Transcribe Audio File
```bash
curl -X POST \
  -F "file=@test.wav" \
  -F "output_format=text" \
  -F "language=zh" \
  -F "enable_speaker_diarization=false" \
  -F "hotwords=测试 20" \
  http://localhost:7869/transcribe
```

#### Transcribe with Speaker Diarization
```bash
curl -X POST \
  -F "file=@test.mp4" \
  -F "output_format=srt" \
  -F "language=zh" \
  -F "enable_speaker_diarization=true" \
  http://localhost:7869/transcribe
```

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:7869/docs
- **ReDoc**: http://localhost:7869/redoc

## Docker Deployment

### CPU Version
```bash
docker-compose --profile cpu up -d
```

### GPU Version (requires NVIDIA Docker)
```bash
docker-compose --profile gpu up -d
```

### Build Custom Image
```bash
# CPU version
docker build -t asr-api-v2:cpu .

# GPU version
docker build -f Dockerfile.gpu -t asr-api-v2:gpu .
```

### Volume Configuration

The Docker setup includes a persistent volume for ModelScope cache:

- **`modelscope_cache`**: Stores downloaded FunASR models to avoid re-downloading
- **Location**: `/root/.cache/modelscope` inside container
- **Benefits**: Faster startup times after initial model download

To manually manage the cache volume:
```bash
# View volume info
docker volume inspect asr_api_v2_modelscope_cache

# Remove volume to force model re-download
docker volume rm asr_api_v2_modelscope_cache
```

## Performance Considerations

- **GPU Acceleration**: Use GPU deployment for better performance
- **Memory Usage**: Large models require significant RAM
- **File Size Limits**: Adjust based on your use case
- **Concurrent Requests**: Limited by hardware resources
- **Model Caching**: Models are cached in Docker volumes to avoid re-downloading

## Troubleshooting

### Common Issues

1. **Model Download**: First run may take time to download models (subsequent runs use cached models)
2. **CUDA Errors**: Ensure NVIDIA Docker is properly installed
3. **Memory Issues**: Reduce concurrent requests or use CPU mode
4. **File Format**: Verify input files are in supported formats

### Logs

Check application logs for detailed error information:
```bash
docker logs asr-api-v2-cpu
# or
docker logs asr-api-v2-gpu
```

## Development

### Project Structure
```
ASR_API_V2/
├── main.py              # FastAPI application
├── asr_processor.py     # Core ASR processing logic
├── models.py            # Pydantic models
├── utils/               # Utility functions
├── test_api.py          # Test script
├── requirements.txt     # Python dependencies
├── Dockerfile           # CPU Docker image
├── Dockerfile.gpu       # GPU Docker image
├── docker-compose.yml   # Docker Compose configuration
└── README.md           # This file
```

## License

This project is based on Private-ASR and FunASR, following the MIT License.

## Credits

- Based on [Private-ASR](https://github.com/MotorBottle/Audio-Processor)
- Powered by [FunASR](https://github.com/alibaba-damo-academy/FunASR)
- Uses [FastAPI](https://fastapi.tiangolo.com/) for the web framework