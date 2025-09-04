# ================================
# 4. STT 처리기 (src/processors/stt_processor.py)
# ================================

import whisper
import torch
from typing import Dict, Tuple
import time
import numpy as np
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

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
            # 방법 1: 직접 Whisper 사용 (ffmpeg 필요)
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=False,
                verbose=False,
                without_timestamps=False,
                decode_options={"beam_size": 5, "best_of": 5}
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
            print(f"❌ 직접 STT 처리 실패: {e}")
            
            # ffmpeg 오류인 경우 librosa fallback 시도
            if "ffmpeg" in str(e).lower() and LIBROSA_AVAILABLE:
                print("🔄 librosa를 사용한 fallback 시도...")
                return self._transcribe_with_librosa(audio_path, language, start_time)
            else:
                print("🔧 ffmpeg 설치 확인 필요:")
                print("   - packages.txt에 ffmpeg 추가")
                print("   - Streamlit Cloud 앱 재배포")
                raise
    
    def _transcribe_with_librosa(self, audio_path: str, language: str, start_time: float) -> Tuple[str, float]:
        """librosa를 사용한 fallback STT 처리"""
        try:
            # librosa로 오디오 로드 (ffmpeg 없이 가능)
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Whisper에 numpy 배열로 직접 전달
            result = self.model.transcribe(
                audio,
                language=language,
                fp16=False,
                verbose=False
            )
            
            text = result["text"].strip()
            
            # 신뢰도 계산
            if "segments" in result:
                confidences = [seg.get("confidence", 0.0) for seg in result["segments"]]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            else:
                avg_confidence = 0.7  # librosa fallback이므로 약간 낮게
            
            processing_time = time.time() - start_time
            print("✅ librosa fallback 성공!")
            return text, avg_confidence, processing_time
            
        except Exception as fallback_error:
            print(f"❌ librosa fallback도 실패: {fallback_error}")
            raise Exception(f"STT 처리 완전 실패 - 직접: ffmpeg 없음, librosa: {str(fallback_error)}")