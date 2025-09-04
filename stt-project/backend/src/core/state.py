# ================================
# 2. 핵심 상태 정의 (src/core/state.py)
# ================================

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

class VoiceProcessingState(TypedDict):
    """LangGraph에서 사용할 상태 정의"""
    # 입력 데이터
    audio_file_path: str
    session_id: str
    
    # STT 결과
    original_text: str
    stt_confidence: float
    
    # 전처리 결과
    cleaned_text: str
    removed_fillers: List[str]
    
    # 구조화 결과
    organized_story: Dict[str, Any]
    story_structure: Dict[str, List[str]]
    
    # 태그 추출 결과
    extracted_tags: List[str]
    tag_confidence: Dict[str, float]
    
    # 메타데이터
    processing_steps: List[str]
    error_messages: List[str]
    processing_time: Dict[str, float]
    created_at: str

@dataclass
class ProcessingResult:
    """API 응답용 결과 클래스"""
    success: bool
    session_id: str
    original_text: str = ""
    cleaned_text: str = ""
    organized_story: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    processing_info: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
