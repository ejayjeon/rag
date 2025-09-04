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

    def __init__(self, model_name: str = "base", language: str = "ko", force_librosa: bool = False):
        self.model_name = model_name
        self.language = language
        self.model = None
        self.force_librosa = force_librosa  # Streamlit Cloud용 강제 librosa 사용
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
        
        # Streamlit Cloud에서 강제 librosa 사용
        if self.force_librosa and LIBROSA_AVAILABLE:
            print("🔄 강제 librosa 모드 사용")
            return self._transcribe_with_librosa(audio_path, language, start_time)
        
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
            print(f"🔍 LIBROSA_AVAILABLE: {LIBROSA_AVAILABLE}")
            print(f"🔍 ffmpeg in error: {'ffmpeg' in str(e).lower()}")
            print(f"🔍 Error type: {type(e).__name__}")
            
            # 모든 오디오 관련 오류에 대해 librosa fallback 시도
            if LIBROSA_AVAILABLE and ("ffmpeg" in str(e).lower() or "audio" in str(e).lower() or "No such file" in str(e)):
                print("🔄 librosa를 사용한 fallback 시도...")
                return self._transcribe_with_librosa(audio_path, language, start_time)
            else:
                print("🔧 문제 해결 방법:")
                print("   1. packages.txt에 ffmpeg 추가")
                print("   2. Streamlit Cloud 앱 재배포")
                print(f"   3. librosa 사용 가능: {LIBROSA_AVAILABLE}")
                raise
    
    def _transcribe_with_librosa(self, audio_path: str, language: str, start_time: float) -> Tuple[str, float]:
        """librosa를 사용한 fallback STT 처리"""
        import os
        from pathlib import Path
        
        try:
            print(f"🔍 처리할 파일: {audio_path}")
            print(f"🔍 파일 확장자: {Path(audio_path).suffix}")
            
            # MP4 파일인 경우 특별 처리 필요
            file_extension = Path(audio_path).suffix.lower()
            
            if file_extension in ['.mp4', '.mov', '.avi']:
                print("📹 비디오 파일 감지 - 오디오 추출 시도")
                
                # 1. moviepy를 사용한 오디오 추출 시도
                try:
                    from moviepy.editor import VideoFileClip
                    temp_audio_path = str(Path(audio_path).with_suffix('.wav'))
                    
                    print(f"🎬 moviepy로 오디오 추출: {temp_audio_path}")
                    video = VideoFileClip(audio_path)
                    video.audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
                    video.close()
                    
                    # 추출된 WAV 파일로 처리
                    audio, sr = librosa.load(temp_audio_path, sr=16000)
                    os.remove(temp_audio_path)  # 임시 파일 정리
                    print("✅ moviepy 오디오 추출 성공")
                    
                except ImportError:
                    print("⚠️ moviepy 없음 - librosa 직접 시도")
                    audio, sr = librosa.load(audio_path, sr=16000)
                except Exception as moviepy_error:
                    print(f"⚠️ moviepy 실패: {moviepy_error} - librosa 직접 시도")
                    audio, sr = librosa.load(audio_path, sr=16000)
            else:
                # 일반 오디오 파일
                print("🎵 오디오 파일 - librosa 직접 처리")
                audio, sr = librosa.load(audio_path, sr=16000)
            
            print(f"🔍 로드된 오디오 길이: {len(audio)/sr:.2f}초")
            
            # Whisper에 numpy 배열로 직접 전달
            result = self.model.transcribe(
                audio,
                language=language,
                fp16=False,
                verbose=False
            )
            
            text = result["text"].strip()
            print(f"🎯 인식된 텍스트: {text[:50]}...")
            
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
            print(f"   파일 경로: {audio_path}")
            print(f"   파일 존재: {os.path.exists(audio_path)}")
            if os.path.exists(audio_path):
                print(f"   파일 크기: {os.path.getsize(audio_path)} bytes")
            raise Exception(f"STT 처리 완전 실패 - 직접: ffmpeg 없음, librosa: {str(fallback_error)}")