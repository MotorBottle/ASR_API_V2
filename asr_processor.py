#!/usr/bin/env python3
"""
ASR Processor for API Server V2
Extracted and adapted from Private-ASR project
"""

import os
import logging
import time
import tempfile
import numpy as np
import torch
import torchaudio
import librosa
import soundfile as sf
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from moviepy.editor import VideoFileClip

from funasr import AutoModel
from utils.subtitle_utils import generate_srt
from utils.trans_utils import convert_pcm_to_float

logger = logging.getLogger(__name__)

class ASRProcessor:
    """
    ASR Processor for handling audio/video transcription
    Adapted from Private-ASR VideoClipper class
    """
    
    def __init__(self, device: str = "cpu", language: str = "zh"):
        """
        Initialize ASR processor
        
        Args:
            device: Processing device (cpu or cuda:0)
            language: Language for ASR (zh or en)
        """
        self.device = device
        self.language = language
        self.funasr_model = None
        
        logger.info(f"Initializing ASR processor with device: {device}, language: {language}")
        self._load_models()
    
    def _load_models(self):
        """Load FunASR models based on language"""
        try:
            if self.language == "zh":
                # Chinese models - using exact same configuration as Private-ASR
                self.funasr_model = AutoModel(
                    model="iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                    vad_model="damo/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                    punc_model="damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
                    spk_model="damo/speech_campplus_sv_zh-cn_16k-common",
                    device=self.device
                )
            else:
                # English models - using exact same configuration as Private-ASR
                self.funasr_model = AutoModel(
                    model="iic/speech_paraformer_asr-en-16k-vocab4199-pytorch",
                    vad_model="damo/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                    punc_model="damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
                    spk_model="damo/speech_campplus_sv_zh-cn_16k-common",
                    device=self.device
                )
            
            logger.info(f"Successfully loaded FunASR model for {self.language} with all components")
            
        except Exception as e:
            logger.error(f"Failed to load FunASR models: {e}")
            raise
        
        self._log_funasr_state("load_complete")
    
    def _log_funasr_state(self, phase: str):
        """
        Log internal FunASR state to help diagnose device/batching issues.
        """
        if self.funasr_model is None:
            return
        
        info: Dict[str, Any] = {"phase": phase}
        
        try:
            info["model_device"] = str(next(self.funasr_model.model.parameters()).device)
        except (StopIteration, AttributeError):
            info["model_device"] = "unknown"
        
        keys_of_interest = (
            "device",
            "batch_size",
            "batch_size_s",
            "batch_size_threshold_s",
            "ncpu",
            "ngpu",
            "disable_pbar",
        )
        
        for attr_name in ("kwargs", "vad_kwargs", "punc_kwargs", "spk_kwargs"):
            attr = getattr(self.funasr_model, attr_name, None)
            if isinstance(attr, dict):
                for key in keys_of_interest:
                    info[f"{attr_name}_{key}"] = attr.get(key)
        
        info["torch_threads"] = torch.get_num_threads()
        
        logger.info("FunASR state: %s", info)
    
    def _preprocess_audio(self, audio_path: str) -> Tuple[int, np.ndarray]:
        """
        Preprocess audio file to required format
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (sample_rate, audio_data)
        """
        try:
            # Load audio using librosa
            data, sr = librosa.load(audio_path, sr=None, mono=True)
            logger.info(f"Loaded audio with librosa: sr={sr}, shape={data.shape}")
            
            # Convert to float64
            data = convert_pcm_to_float(data)
            
            # Resample to 16kHz if needed
            if sr != 16000:
                data = torch.tensor(data, dtype=torch.float32)
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
                data = resampler(data).numpy()
                sr = 16000
                logger.info(f"Resampled audio to 16kHz: new_shape={data.shape}")
            
            # Ensure mono
            if len(data.shape) == 2:
                logger.warning("Converting multi-channel audio to mono")
                data = np.mean(data, axis=1)
            
            return sr, data
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise
    
    def _extract_audio_from_video(self, video_path: str) -> str:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file
        """
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio:
                tmp_audio_path = tmp_audio.name
            
            # Extract audio using moviepy
            video = VideoFileClip(video_path)
            audio = video.audio
            
            if audio is None:
                raise ValueError("No audio track found in video")
            
            # Write audio to temporary file
            audio.write_audiofile(tmp_audio_path, verbose=False, logger=None)
            
            # Cleanup
            audio.close()
            video.close()
            
            logger.info(f"Extracted audio from video: {tmp_audio_path}")
            return tmp_audio_path
            
        except Exception as e:
            logger.error(f"Audio extraction from video failed: {e}")
            raise
    
    def _process_hotwords(self, hotwords_dict: Optional[Dict[str, float]]) -> str:
        """
        Process hotwords dictionary to format expected by FunASR
        
        Args:
            hotwords_dict: Dictionary of hotwords with weights
            
        Returns:
            Formatted hotwords string
        """
        if not hotwords_dict:
            return ""
        
        # Format: "word1 weight1\nword2 weight2"
        hotwords_lines = []
        for word, weight in hotwords_dict.items():
            hotwords_lines.append(f"{word} {weight}")
        
        return "\n".join(hotwords_lines)
    
    def process_file(
        self, 
        file_path: str, 
        output_format: str = "text",
        language: str = "zh",
        enable_speaker_diarization: bool = False,
        hotwords_dict: Optional[Dict[str, float]] = None,
        merge_threshold: int = 8000
    ) -> Dict[str, Any]:
        """
        Process audio or video file for transcription
        
        Args:
            file_path: Path to input file
            output_format: Output format (text or srt)
            language: Language for transcription
            enable_speaker_diarization: Enable speaker diarization
            hotwords_dict: Hotwords with weights
            merge_threshold: Time threshold in milliseconds for merging consecutive utterances (default: 8000ms)
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine file type
            file_extension = Path(file_path).suffix.lower()
            is_video = file_extension in ['.mp4', '.avi', '.mkv', '.mov', '.webm', '.ts', '.mpeg']
            
            # Extract audio from video if needed
            audio_path = file_path
            temp_audio_path = None
            
            if is_video:
                temp_audio_path = self._extract_audio_from_video(file_path)
                audio_path = temp_audio_path
            
            try:
                # Preprocess audio
                sr, audio_data = self._preprocess_audio(audio_path)
                
                # Process hotwords
                hotwords_str = self._process_hotwords(hotwords_dict)
                # Log internal state before inference
                self._log_funasr_state("before_generate")
                
                # Run ASR
                start_time = time.perf_counter()
                if enable_speaker_diarization:
                    rec_result = self.funasr_model.generate(
                        audio_data,
                        return_spk_res=True,
                        sentence_timestamp=True,  # Add missing sentence_timestamp parameter
                        return_raw_text=True,
                        is_final=True,
                        hotword=hotwords_str,
                        pred_timestamp=(language == 'en'),
                        en_post_proc=(language == 'en'),
                        cache={}
                    )
                else:
                    rec_result = self.funasr_model.generate(
                        audio_data,
                        return_spk_res=False,
                        sentence_timestamp=True,
                        return_raw_text=True,
                        is_final=True,
                        hotword=hotwords_str,
                        pred_timestamp=(language == 'en'),
                        en_post_proc=(language == 'en'),
                        cache={}
                    )
                
                elapsed = time.perf_counter() - start_time
                audio_duration = len(audio_data) / sr if sr else 0.0
                rtf = (elapsed / audio_duration) if audio_duration > 0 else float("inf")
                
                self._log_funasr_state("after_generate")
                logger.info(
                    "FunASR segment done: elapsed=%.3fs audio=%.3fs rtf=%.3f segments=%s",
                    elapsed,
                    audio_duration,
                    rtf,
                    len(rec_result) if isinstance(rec_result, (list, tuple)) else "NA"
                )
                
                # Extract results
                result = rec_result[0]
                text_result = result['text']
                sentence_info = result['sentence_info']
                
                # Initialize variables
                srt_result = None
                
                # Generate output based on format
                if output_format in ["srt", "both"]:
                    srt_content = generate_srt(sentence_info, merge_threshold=merge_threshold)
                    
                    if output_format == "srt":
                        transcription = srt_content
                    else:  # both
                        transcription = text_result
                        srt_result = srt_content
                else:  # text
                    transcription = text_result
                
                # Calculate duration
                duration = len(audio_data) / sr
                
                # Extract speaker information
                speakers = []
                if enable_speaker_diarization and sentence_info:
                    for sentence in sentence_info:
                        if 'spk' in sentence:
                            spk_id = f"spk{sentence['spk']}"  # Format as spk0, spk1, etc.
                            if spk_id not in speakers:
                                speakers.append(spk_id)
                
                result_dict = {
                    "transcription": transcription,
                    "duration": duration,
                    "speakers": speakers,
                    "language": language,
                    "format": output_format
                }
                
                # Add SRT content for "both" format
                if output_format == "both":
                    result_dict["transcription_srt"] = srt_result
                    logger.info(f"Added SRT content for 'both' format, SRT length: {len(srt_result) if srt_result else 0}")
                
                return result_dict
                
            finally:
                # Cleanup temporary audio file
                if temp_audio_path and os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                    logger.info(f"Cleaned up temporary audio file: {temp_audio_path}")
                    
        except Exception as e:
            logger.error(f"File processing failed: {e}")
            raise
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported file formats"""
        return {
            "audio": [".wav", ".mp3", ".aac", ".m4a", ".flac"],
            "video": [".mp4", ".avi", ".mkv", ".mov", ".webm", ".ts", ".mpeg"]
        }
    
    def get_available_languages(self) -> List[str]:
        """Get available languages"""
        return ["zh", "en"]
