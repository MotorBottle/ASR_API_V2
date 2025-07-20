"""
Pydantic models for ASR API Server V2
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl

class TranscriptionRequest(BaseModel):
    """Request model for URL-based transcription"""
    url: HttpUrl = Field(..., description="URL of the audio/video file to transcribe")
    output_format: Literal["text", "srt", "both"] = Field("text", description="Output format: text, srt, or both")
    language: Literal["zh", "en"] = Field("zh", description="Language: zh (Chinese) or en (English)")
    enable_speaker_diarization: bool = Field(False, description="Enable speaker diarization")
    hotwords: Optional[Dict[str, float]] = Field(None, description="Hotwords with weights for improved recognition")

class TranscriptionResponse(BaseModel):
    """Response model for transcription results"""
    success: bool = Field(..., description="Whether transcription was successful")
    transcription: str = Field(..., description="Transcribed text or SRT content")
    transcription_srt: Optional[str] = Field(None, description="SRT content (when format is 'both')")
    format: str = Field(..., description="Output format used")
    language: str = Field(..., description="Language used for transcription")
    speaker_diarization: bool = Field(..., description="Whether speaker diarization was enabled")
    duration: float = Field(0.0, description="Duration of the audio/video in seconds")
    speakers: List[str] = Field(default_factory=list, description="List of identified speakers")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="API version")

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

class ModelInfo(BaseModel):
    """Model information response"""
    available_languages: List[str] = Field(..., description="Available languages")
    supported_formats: Dict[str, List[str]] = Field(..., description="Supported file formats")
    output_formats: List[str] = Field(..., description="Available output formats")
    features: Dict[str, bool] = Field(..., description="Available features")