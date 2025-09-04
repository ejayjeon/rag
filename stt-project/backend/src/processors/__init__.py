"""
Processors 모듈

데이터 처리를 담당하는 프로세서들을 포함합니다:
- STTProcessor: 음성을 텍스트로 변환하는 프로세서
"""

from .stt_processor import STTProcessor

__all__ = [
    "STTProcessor",
]
