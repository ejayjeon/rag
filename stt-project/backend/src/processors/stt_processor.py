# ================================
# 4. STT 처리기 (src/processors/stt_processor.py)
# ================================

import whisper
import torch
from typing import Dict, Tuple
import time

class STTProcessor:
    """Whisper를 사용한 STT 처리"""

    def __init__(self, model_name: str = "base", language: str = "ko"):
        self.model_name = model_name
        self.language = language
        self.model = None
        self._load_model()

    def _load_model(self):
        """Whisper 모델 로드"""
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = whisper.load_model(self.model_name, device=device)
            print(f"✅ Whisper {self.model_name} 모델 로드 완료 ({device})")
        except Exception as e:
            print(f"❌ Whisper 모델 로드 실패: {e}")
            raise
    
    def transcribe(self, audio_path: str, language: str = "ko") -> Tuple[str, float]:
        """음성 파일을 텍스트로 변환"""
        start_time = time.time()
        
        try:
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=False,
                verbose=False
            )
            
            text = result["text"].strip()
            
            # 평균 신뢰도 계산 (segments 기반)
            if "segments" in result:
                confidences = [seg.get("confidence", 0.0) for seg in result["segments"]]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            else:
                avg_confidence = 0.8  # 기본값
            
            processing_time = time.time() - start_time
            
            return text, avg_confidence, processing_time
            
        except Exception as e:
            print(f"❌ STT 처리 실패: {e}")
            raise