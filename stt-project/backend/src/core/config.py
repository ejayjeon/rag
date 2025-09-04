# ================================
# 3. 설정 관리 (src/core/config.py)
# ================================

import os
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class LLMProvider(Enum):
    """LLM 제공자 열거형"""
    OLLAMA = "ollama"
    OPENAI = "openai"

class Config:
    """환경별 설정 관리"""
    
    # 기본 경로
    BASE_DIR = Path(__file__).parent.parent.parent
    MODELS_DIR = BASE_DIR / "models"
    TEMP_DIR = BASE_DIR / "temp"
    
    # Whisper 설정
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ko")
    
    # LLM Provider 설정
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    # Ollama 설정
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")  # 커스텀 엔드포인트용
    
    # 하위 호환성을 위한 레거시 설정
    LLM_MODEL = os.getenv("LLM_MODEL", OLLAMA_MODEL)
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", OLLAMA_BASE_URL)
    
    # 처리 설정
    MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "50"))
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    # API 설정 (Phase 2용)
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    @classmethod
    def get_current_llm_provider(cls) -> LLMProvider:
        """현재 설정된 LLM 제공자 반환"""
        if cls.LLM_PROVIDER == "openai":
            return LLMProvider.OPENAI
        return LLMProvider.OLLAMA
    
    @classmethod
    def get_llm_config(cls):
        """현재 LLM 제공자에 따른 설정 반환"""
        provider = cls.get_current_llm_provider()
        
        if provider == LLMProvider.OPENAI:
            return {
                "provider": "openai",
                "model": cls.OPENAI_MODEL,
                "api_key": cls.OPENAI_API_KEY,
                "base_url": cls.OPENAI_BASE_URL,
            }
        else:  # OLLAMA
            return {
                "provider": "ollama", 
                "model": cls.OLLAMA_MODEL,
                "base_url": cls.OLLAMA_BASE_URL,
            }
    
    @classmethod
    def is_openai_configured(cls) -> bool:
        """OpenAI API 키가 설정되어 있는지 확인"""
        return bool(cls.OPENAI_API_KEY)
    
    @classmethod
    def is_streamlit_cloud(cls) -> bool:
        """Streamlit Cloud 환경인지 확인"""
        import sys
        
        # Streamlit Cloud 감지 조건들
        cloud_indicators = [
            "/app/" in str(Path.cwd()),                    # Streamlit Cloud 기본 경로
            "/mount/src/" in str(Path.cwd()),              # GitHub 연동 경로
            "STREAMLIT_CLOUD" in os.environ,               # 환경 변수
            "STREAMLIT" in os.environ,                     # 대안 환경 변수
            hasattr(sys, 'ps1') is False,                  # 비대화형 환경
            "streamlit" in str(sys.executable).lower(),    # Streamlit 실행 환경
        ]
        
        is_cloud = any(cloud_indicators)
        print(f"🔍 Streamlit Cloud 감지 결과: {is_cloud}")
        print(f"   - 현재 경로: {Path.cwd()}")
        print(f"   - Python 실행파일: {sys.executable}")
        print(f"   - 환경 변수 STREAMLIT: {'STREAMLIT' in os.environ}")
        
        return is_cloud
    
    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리 생성"""
        cls.MODELS_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)