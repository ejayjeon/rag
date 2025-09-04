"""
STT 프로젝트 백엔드 모듈

음성 처리 및 스토리 정리를 위한 백엔드 시스템입니다.
"""

__version__ = "0.1.0"
__author__ = "STT Project Team"

# 주요 모듈들을 쉽게 import할 수 있도록 설정
from .core import Config, ProcessingResult, VoiceProcessingWorkflow
from .services import VoiceProcessingService
from .processors import STTProcessor

__all__ = [
    "Config",
    "ProcessingResult", 
    "VoiceProcessingWorkflow",
    "VoiceProcessingService",
    "STTProcessor",
]
