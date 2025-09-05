# audio_processor.py
import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional
import whisper
import torch
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import numpy as np

class AudioProcessor:
    def __init__(self, model_size: str = "base"):
        """
        Initialize audio processor with Whisper model
        
        Args:
            model_size: Size of Whisper model (tiny, base, small, medium, large)
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model ({model_size}) on {self.device}...")
        self.whisper_model = whisper.load_model(model_size, device=self.device)
        
    def preprocess_audio(self, audio_file_path: str) -> str:
        """
        Preprocess audio: normalize, remove silence, convert format
        
        Args:
            audio_file_path: Path to input audio file
            
        Returns:
            Path to preprocessed audio file
        """
        # Load audio file
        audio = AudioSegment.from_file(audio_file_path)
        
        # Normalize audio volume
        audio = self.normalize_audio(audio)
        
        # Remove long silence periods
        audio = self.remove_silence(audio)
        
        # Convert to 16kHz mono for Whisper
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        
        # Save preprocessed audio
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        audio.export(temp_path, format="wav")
        
        return temp_path
    
    def normalize_audio(self, audio: AudioSegment, target_dBFS: float = -20.0) -> AudioSegment:
        """
        Normalize audio volume to target dBFS
        
        Args:
            audio: Input audio segment
            target_dBFS: Target volume level in dBFS
            
        Returns:
            Normalized audio segment
        """
        change_in_dBFS = target_dBFS - audio.dBFS
        return audio.apply_gain(change_in_dBFS)
    
    def remove_silence(self, audio: AudioSegment, 
                      min_silence_len: int = 1000,
                      silence_thresh: int = -40) -> AudioSegment:
        """
        Remove silence from audio
        
        Args:
            audio: Input audio segment
            min_silence_len: Minimum length of silence to detect (ms)
            silence_thresh: Silence threshold in dBFS
            
        Returns:
            Audio with silence removed
        """
        # Detect non-silent chunks
        nonsilent_chunks = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh
        )
        
        # Concatenate non-silent chunks
        if nonsilent_chunks:
            processed = AudioSegment.empty()
            for start, end in nonsilent_chunks:
                processed += audio[start:end]
            return processed
        return audio
    
    def transcribe(self, audio_file_path: str, 
                  language: Optional[str] = None) -> dict:
        """
        Transcribe audio using Whisper
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (e.g., 'ko', 'en') or None for auto-detect
            
        Returns:
            Transcription result dictionary
        """
        # Preprocess audio
        preprocessed_path = self.preprocess_audio(audio_file_path)
        
        try:
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                preprocessed_path,
                language=language,
                task="transcribe",
                verbose=False
            )
            
            # Add preprocessing info
            result['preprocessed'] = True
            result['original_file'] = audio_file_path
            
            return result
            
        finally:
            # Clean up temp file
            if os.path.exists(preprocessed_path):
                os.remove(preprocessed_path)
    
    def extract_segments_with_timestamps(self, result: dict) -> list:
        """
        Extract text segments with timestamps
        
        Args:
            result: Whisper transcription result
            
        Returns:
            List of segments with timestamps
        """
        segments = []
        for segment in result.get('segments', []):
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'confidence': segment.get('avg_logprob', 0)
            })
        return segments