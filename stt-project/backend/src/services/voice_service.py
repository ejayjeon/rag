# ================================  
# 7. 비즈니스 로직 서비스 (src/services/voice_service.py)
# ================================

from src.core.workflow import VoiceProcessingWorkflow
from src.core.config import Config
from src.core.state import ProcessingResult
from pathlib import Path
import shutil

class VoiceProcessingService:
    """음성 처리 비즈니스 로직"""
    
    def __init__(self):
        Config.ensure_directories()
        self.workflow = VoiceProcessingWorkflow()
    
    def process_audio_file(self, audio_file_path: str) -> ProcessingResult:
        """오디오 파일 처리"""
        # 파일 존재 확인
        if not Path(audio_file_path).exists():
            return ProcessingResult(
                success=False,
                session_id="",
                error_message="오디오 파일을 찾을 수 없습니다."
            )
        
        # 파일 크기 확인
        file_size_mb = Path(audio_file_path).stat().st_size / (1024 * 1024)
        if file_size_mb > Config.MAX_AUDIO_SIZE_MB:
            return ProcessingResult(
                success=False,
                session_id="",
                error_message=f"파일 크기가 너무 큽니다. ({file_size_mb:.1f}MB > {Config.MAX_AUDIO_SIZE_MB}MB)"
            )
        
        # 워크플로우 실행
        return self.workflow.process_voice(audio_file_path)
    
    def process_uploaded_audio(self, uploaded_file, original_filename: str) -> ProcessingResult:
        """업로드된 오디오 파일 처리 (Streamlit/FastAPI용)"""
        # 임시 파일로 저장
        temp_path = Config.TEMP_DIR / f"temp_{original_filename}"
        
        try:
            # 파일 저장
            if hasattr(uploaded_file, 'read'):
                # Streamlit UploadedFile
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.read())
            else:
                # 일반 파일 객체
                shutil.copy(uploaded_file, temp_path)
            
            # 처리 실행
            result = self.process_audio_file(str(temp_path))
            
            return result
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                session_id="",
                error_message=f"파일 처리 오류: {str(e)}"
            )
        finally:
            # 임시 파일 정리
            if temp_path.exists():
                temp_path.unlink()