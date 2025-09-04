"""
FastAPI 서버 진입점
Flutter 앱과 연동을 위한 API 서버
"""

import sys
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 프로젝트 모듈 import
from src.services.voice_service import VoiceProcessingService
from src.core.config import Config

# FastAPI 앱 초기화
app = FastAPI(
    title="🎙️ 음성 처리 API",
    description="음성을 텍스트로 변환하고 스토리를 정리하는 API 서버",
    version="0.1.0"
)

# CORS 설정 (Flutter 앱 연동을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 운영 시 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 음성 처리 서비스 초기화
voice_service = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 서비스 초기화"""
    global voice_service
    try:
        voice_service = VoiceProcessingService()
        print("✅ VoiceProcessingService 초기화 완료")
    except Exception as e:
        print(f"❌ 서비스 초기화 실패: {e}")

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "🎙️ 음성 처리 API 서버",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "process_audio": "/api/v1/process-audio",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "voice_service" if voice_service else "not_initialized",
        "config": {
            "whisper_model": Config.WHISPER_MODEL,
            "language": Config.WHISPER_LANGUAGE,
            "max_file_size_mb": Config.MAX_AUDIO_SIZE_MB
        }
    }

@app.post("/api/v1/process-audio")
async def process_audio(file: UploadFile = File(...)):
    """
    음성 파일을 처리하여 텍스트로 변환하고 스토리를 정리
    Flutter 앱에서 호출할 메인 엔드포인트
    """
    if not voice_service:
        raise HTTPException(status_code=500, detail="음성 처리 서비스가 초기화되지 않았습니다")
    
    # 파일 타입 검증
    allowed_types = ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/m4a', 'audio/flac', 'audio/ogg']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {allowed_types}"
        )
    
    try:
        # 음성 파일 처리
        result = voice_service.process_uploaded_audio(file.file, file.filename)
        
        if result.success:
            return {
                "success": True,
                "session_id": result.session_id,
                "data": {
                    "original_text": result.original_text,
                    "cleaned_text": result.cleaned_text,
                    "organized_story": result.organized_story,
                    "tags": result.tags,
                    "created_at": result.created_at
                },
                "processing_info": result.processing_info
            }
        else:
            return {
                "success": False,
                "error": result.error_message,
                "session_id": result.session_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/v1/config")
async def get_config():
    """현재 설정 정보 반환"""
    return {
        "whisper_model": Config.WHISPER_MODEL,
        "language": Config.WHISPER_LANGUAGE,
        "max_audio_size_mb": Config.MAX_AUDIO_SIZE_MB,
        "llm_model": Config.LLM_MODEL
    }

if __name__ == "__main__":
    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )