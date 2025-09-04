# ================================
# 3. 설정 관리 (src/core/config.py)
# ================================

import os
from pathlib import Path

class Config:
    """환경별 설정 관리"""
    
    # 기본 경로
    BASE_DIR = Path(__file__).parent.parent.parent
    MODELS_DIR = BASE_DIR / "models"
    TEMP_DIR = BASE_DIR / "temp"
    
    # Whisper 설정
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ko")
    
    # LLM 설정 
    LLM_MODEL = os.getenv("LLM_MODEL", "llama2")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    
    # 처리 설정
    MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "50"))
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    # API 설정 (Phase 2용)
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리 생성"""
        cls.MODELS_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)