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
            # Streamlit Cloud 환경에서는 CPU만 사용하고 download_root 명시
            if device == "cpu":
                self.model = whisper.load_model(
                    self.model_name, 
                    device=device,
                    download_root=None  # 기본 캐시 디렉토리 사용
                )
            else:
                self.model = whisper.load_model(self.model_name, device=device)
            print(f"✅ Whisper {self.model_name} 모델 로드 완료 ({device})")
        except Exception as e:
            print(f"❌ Whisper 모델 로드 실패: {e}")
            # ffmpeg 오류인 경우 더 자세한 안내
            if "ffmpeg" in str(e).lower():
                print("💡 Streamlit Cloud에서 ffmpeg 오류 발생 시:")
                print("   1. packages.txt 파일에 'ffmpeg' 추가")
                print("   2. 앱 재배포 필요")
                print("   3. 또는 다른 오디오 형식 사용 고려")
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