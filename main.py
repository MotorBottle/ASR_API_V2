#!/usr/bin/env python3
"""
ASR API Server V2
A FastAPI-based server for video/audio transcription services
Extracted from Private-ASR project and optimized for API usage
"""

import os
import tempfile
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from asr_processor import ASRProcessor
from models import (
    TranscriptionRequest, 
    TranscriptionResponse, 
    HealthResponse,
    ErrorResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ASR API Server V2",
    description="Audio/Video Transcription API using FunASR",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global ASR processor instance
asr_processor: Optional[ASRProcessor] = None
executor = ThreadPoolExecutor(max_workers=4)

@app.on_event("startup")
async def startup_event():
    """Initialize ASR processor on startup"""
    global asr_processor
    logger.info("Initializing ASR processor...")
    
    device = os.getenv("DEVICE", "cpu")
    language = os.getenv("LANGUAGE", "zh")
    
    try:
        asr_processor = ASRProcessor(device=device, language=language)
        logger.info(f"ASR processor initialized successfully on {device}")
    except Exception as e:
        logger.error(f"Failed to initialize ASR processor: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down ASR API server...")
    executor.shutdown(wait=True)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if asr_processor is None:
        raise HTTPException(status_code=503, detail="ASR processor not initialized")
    
    return HealthResponse(
        status="healthy",
        message="ASR API server is running",
        version="2.0.0"
    )

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_file(
    file: UploadFile = File(..., description="Audio or video file to transcribe"),
    output_format: str = Form("text", description="Output format: text, srt, or both"),
    language: str = Form("zh", description="Language: zh (Chinese) or en (English)"),
    enable_speaker_diarization: bool = Form(False, description="Enable speaker diarization"),
    hotwords: Optional[str] = Form(None, description="Hotwords for improved recognition (one per line)"),
    merge_threshold: int = Form(8000, description="Time threshold in milliseconds for merging consecutive utterances (default: 8000ms)"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Transcribe audio or video file
    
    Args:
        file: Audio or video file to transcribe
        output_format: Output format (text or srt)
        language: Language for transcription (zh or en)
        enable_speaker_diarization: Enable speaker diarization
        hotwords: Hotwords for improved recognition
        merge_threshold: Time threshold in milliseconds for merging consecutive utterances
        
    Returns:
        Transcription result with text/srt output
    """
    if asr_processor is None:
        raise HTTPException(status_code=503, detail="ASR processor not initialized")
    
    # Validate parameters
    if output_format not in ["text", "srt", "both"]:
        raise HTTPException(status_code=400, detail="output_format must be 'text', 'srt', or 'both'")
    
    if language not in ["zh", "en"]:
        raise HTTPException(status_code=400, detail="language must be 'zh' or 'en'")
    
    # Validate file type
    allowed_extensions = {'.wav', '.mp3', '.aac', '.m4a', '.flac', '.mp4', '.avi', '.mkv', '.mov', '.webm'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {file_extension}. Supported formats: {', '.join(allowed_extensions)}"
        )
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        tmp_file_path = tmp_file.name
        
        try:
            # Save uploaded file
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            
            # Process hotwords
            hotwords_dict = None
            if hotwords:
                hotwords_dict = {}
                for line in hotwords.strip().split('\n'):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        word = ' '.join(parts[:-1])
                        try:
                            weight = float(parts[-1])
                            hotwords_dict[word] = weight
                        except ValueError:
                            logger.warning(f"Invalid hotword format: {line}")
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                asr_processor.process_file,
                tmp_file_path,
                output_format,
                language,
                enable_speaker_diarization,
                hotwords_dict,
                merge_threshold
            )
            
            # Schedule file cleanup
            background_tasks.add_task(cleanup_temp_file, tmp_file_path)
            
            # Always include transcription_srt field
            srt_content = result.get("transcription_srt") if output_format == "both" else None
            
            # Clean any null bytes from text fields to prevent JSON corruption
            clean_transcription = str(result["transcription"]).replace('\x00', '') if result.get("transcription") else ""
            clean_srt = str(srt_content).replace('\x00', '') if srt_content else None
            
            response_data = {
                "success": True,
                "transcription": clean_transcription,
                "transcription_srt": clean_srt,
                "format": output_format,
                "language": language,
                "speaker_diarization": enable_speaker_diarization,
                "duration": result.get("duration", 0.0),
                "speakers": result.get("speakers", [])
            }
            
            # Clean any potential null bytes from strings before logging
            safe_format = output_format.replace('\x00', '')
            logger.info(f"Response format: {safe_format}, SRT present: {srt_content is not None}")
            if srt_content:
                clean_len = len(str(srt_content).replace('\x00', ''))
                logger.info(f"SRT content length: {clean_len}")
            
            return TranscriptionResponse(**response_data)
            
        except Exception as e:
            # Cleanup on error
            cleanup_temp_file(tmp_file_path)
            logger.error(f"Transcription failed: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/transcribe_url", response_model=TranscriptionResponse)
async def transcribe_url(
    request: TranscriptionRequest,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Transcribe audio or video from URL
    
    Args:
        request: Transcription request with URL and parameters
        
    Returns:
        Transcription result with text/srt output
    """
    if asr_processor is None:
        raise HTTPException(status_code=503, detail="ASR processor not initialized")
    
    try:
        # Download file from URL
        import requests
        response = requests.get(request.url, stream=True)
        response.raise_for_status()
        
        # Determine file extension from URL or content type
        file_extension = Path(request.url).suffix.lower()
        if not file_extension:
            content_type = response.headers.get('content-type', '')
            if 'video' in content_type:
                file_extension = '.mp4'
            elif 'audio' in content_type:
                file_extension = '.wav'
            else:
                file_extension = '.mp4'  # Default to video
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file_path = tmp_file.name
            
            # Download and save file
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_file.flush()
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                asr_processor.process_file,
                tmp_file_path,
                request.output_format,
                request.language,
                request.enable_speaker_diarization,
                request.hotwords,
                request.merge_threshold
            )
            
            # Schedule file cleanup
            background_tasks.add_task(cleanup_temp_file, tmp_file_path)
            
            # Always include transcription_srt field
            srt_content = result.get("transcription_srt") if request.output_format == "both" else None
            
            response_data = {
                "success": True,
                "transcription": result["transcription"],
                "transcription_srt": srt_content,
                "format": request.output_format,
                "language": request.language,
                "speaker_diarization": request.enable_speaker_diarization,
                "duration": result.get("duration", 0.0),
                "speakers": result.get("speakers", [])
            }
            
            return TranscriptionResponse(**response_data)
            
    except Exception as e:
        logger.error(f"URL transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL transcription failed: {str(e)}")

@app.get("/models", response_model=Dict[str, Any])
async def get_models():
    """Get available ASR models information"""
    if asr_processor is None:
        raise HTTPException(status_code=503, detail="ASR processor not initialized")
    
    return {
        "available_languages": ["zh", "en"],
        "supported_formats": {
            "audio": [".wav", ".mp3", ".aac", ".m4a", ".flac"],
            "video": [".mp4", ".avi", ".mkv", ".mov", ".webm"]
        },
        "output_formats": ["text", "srt", "both"],
        "features": {
            "speaker_diarization": True,
            "hotwords": True
        }
    }

def cleanup_temp_file(file_path: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary file {file_path}: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7869))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )