# ================================  
# 7. 비즈니스 로직 서비스 (src/services/voice_service.py)
# ================================

from src.core.workflow import VoiceProcessingWorkflow
from src.core.config import Config
from src.core.state import ProcessingResult
from src.chains import LLMFactory
from pathlib import Path
import shutil

class VoiceProcessingService:
    """음성 처리 비즈니스 로직"""
    
    def __init__(self, llm_provider: str = None):
        Config.ensure_directories()
        
        # LLM provider 설정
        self.llm_provider = llm_provider or Config.get_current_llm_provider().value
        self.llm_config = Config.get_llm_config()
        
        # Workflow 초기화 (provider 정보 전달)
        self.workflow = VoiceProcessingWorkflow(llm_provider=self.llm_provider)
    
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
    
    def get_provider_status(self) -> dict:
        """현재 LLM 제공자 상태 정보 반환"""
        provider_info = LLMFactory.get_provider_info()
        
        return {
            "current_provider": self.llm_provider,
            "provider_info": provider_info,
            "config": self.llm_config,
            "openai_available": Config.is_openai_configured(),
            "ollama_available": True  # Ollama는 기본적으로 사용 가능하다고 가정
        }
    
    def switch_provider(self, new_provider: str) -> bool:
        """LLM 제공자 변경"""
        try:
            # 새로운 제공자로 워크플로우 재초기화
            self.llm_provider = new_provider
            self.llm_config = Config.get_llm_config()
            self.workflow = VoiceProcessingWorkflow(llm_provider=new_provider)
            return True
        except Exception as e:
            print(f"Provider 변경 실패: {e}")
            return False