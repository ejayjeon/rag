# ================================
# 6. LangGraph 워크플로우 (src/core/workflow.py)
# ================================

from langgraph.graph import StateGraph, END
from src.processors.stt_processor import STTProcessor
from src.chains.cleaning_chain import TextCleaningChain
from src.chains.organize_chain import StoryOrganizingChain  
from src.chains.tagging_chain import HashtagExtractionChain
from src.core.state import ProcessingResult, VoiceProcessingState
import time
import uuid

class VoiceProcessingWorkflow:
    """음성 처리 워크플로우"""
    
    def __init__(self):
        self.stt_processor = STTProcessor()
        self.cleaning_chain = TextCleaningChain()
        self.organizing_chain = StoryOrganizingChain()
        self.tagging_chain = HashtagExtractionChain()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        
        def stt_node(state: VoiceProcessingState) -> dict:
            """STT 처리 노드"""
            start_time = time.time()
            
            try:
                text, confidence, processing_time = self.stt_processor.transcribe(
                    state["audio_file_path"]
                )
                
                return {
                    "original_text": text,
                    "stt_confidence": confidence,
                    "processing_steps": state["processing_steps"] + ["stt_complete"],
                    "processing_time": {
                        **state.get("processing_time", {}),
                        "stt": processing_time
                    }
                }
            except Exception as e:
                return {
                    "error_messages": state["error_messages"] + [f"STT 오류: {str(e)}"],
                    "processing_steps": state["processing_steps"] + ["stt_failed"]
                }
        
        def cleaning_node(state: VoiceProcessingState) -> dict:
            """텍스트 정리 노드"""
            try:
                result = self.cleaning_chain.clean(state["original_text"])
                
                return {
                    "cleaned_text": result["cleaned_text"],
                    "removed_fillers": result["removed_fillers"],
                    "processing_steps": state["processing_steps"] + ["cleaning_complete"]
                }
            except Exception as e:
                return {
                    "error_messages": state["error_messages"] + [f"정리 오류: {str(e)}"],
                    "processing_steps": state["processing_steps"] + ["cleaning_failed"]
                }
        
        def organizing_node(state: VoiceProcessingState) -> dict:
            """스토리 구조화 노드"""
            try:
                organized = self.organizing_chain.organize(state["cleaned_text"])
                
                return {
                    "organized_story": organized,
                    "processing_steps": state["processing_steps"] + ["organizing_complete"]
                }
            except Exception as e:
                return {
                    "error_messages": state["error_messages"] + [f"구조화 오류: {str(e)}"],
                    "processing_steps": state["processing_steps"] + ["organizing_failed"]
                }
        
        def tagging_node(state: VoiceProcessingState) -> dict:
            """해시태그 추출 노드"""
            try:
                story_text = ""
                if state["organized_story"].get("sections"):
                    story_text = " ".join([
                        section["content"] for section in state["organized_story"]["sections"]
                    ])
                else:
                    story_text = state["cleaned_text"]
                
                tags = self.tagging_chain.extract_tags(story_text)
                
                return {
                    "extracted_tags": tags,
                    "processing_steps": state["processing_steps"] + ["tagging_complete"]
                }
            except Exception as e:
                return {
                    "error_messages": state["error_messages"] + [f"태깅 오류: {str(e)}"],
                    "processing_steps": state["processing_steps"] + ["tagging_failed"]
                }
        
        def quality_check_node(state: VoiceProcessingState) -> str:
            """품질 확인 및 분기 결정"""
            # 오류 메시지가 있으면 실패로 처리
            if state.get("error_messages"):
                return "failed"
            
            # STT 신뢰도 확인
            stt_confidence = state.get("stt_confidence", 0.0)
            if stt_confidence < 0.3:
                return "retry_stt"
            
            # 텍스트 길이 확인
            cleaned_text = state.get("cleaned_text", "")
            if len(cleaned_text.strip()) < 10:
                return "insufficient_content"
            
            return "success"
        
        # 워크플로우 구성
        workflow = StateGraph(VoiceProcessingState)
        
        # 노드 추가
        workflow.add_node("stt", stt_node)
        workflow.add_node("cleaner", cleaning_node)
        workflow.add_node("organizer", organizing_node)
        workflow.add_node("tagger", tagging_node)
        
        # 엣지 정의
        workflow.set_entry_point("stt")
        workflow.add_edge("stt", "cleaner")
        workflow.add_edge("cleaner", "organizer")
        workflow.add_edge("organizer", "tagger")
        
        # 조건부 엣지 (품질 검사)
        workflow.add_conditional_edges(
            "tagger",
            quality_check_node,
            {
                "success": END,
                "retry_stt": "stt",
                "insufficient_content": END,
                "failed": END
            }
        )
        
        return workflow.compile()
    
    def process_voice(self, audio_file_path: str) -> ProcessingResult:
        """음성 파일 처리 메인 함수"""
        session_id = str(uuid.uuid4())
        
        # 초기 상태 설정
        initial_state = VoiceProcessingState(
            audio_file_path=audio_file_path,
            session_id=session_id,
            original_text="",
            stt_confidence=0.0,
            cleaned_text="",
            removed_fillers=[],
            organized_story={},
            story_structure={},
            extracted_tags=[],
            tag_confidence={},
            processing_steps=[],
            error_messages=[],
            processing_time={},
            created_at=time.time()
        )
        
        try:
            # 워크플로우 실행
            result_state = self.workflow.invoke(initial_state)
            
            # 결과 반환
            return ProcessingResult(
                success=len(result_state.get("error_messages", [])) == 0,
                session_id=session_id,
                original_text=result_state.get("original_text", ""),
                cleaned_text=result_state.get("cleaned_text", ""),
                organized_story=result_state.get("organized_story", {}),
                tags=result_state.get("extracted_tags", []),
                processing_info={
                    "steps": result_state.get("processing_steps", []),
                    "stt_confidence": result_state.get("stt_confidence", 0.0),
                    "removed_fillers": result_state.get("removed_fillers", []),
                    "processing_time": result_state.get("processing_time", {})
                },
                error_message="; ".join(result_state.get("error_messages", []))
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                session_id=session_id,
                error_message=f"워크플로우 실행 오류: {str(e)}"
            )