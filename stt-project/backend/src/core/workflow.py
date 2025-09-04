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
import subprocess
import shutil
from pathlib import Path

class VoiceProcessingWorkflow:
    """음성 처리 워크플로우"""
    
    def __init__(self, llm_provider: str = None):
        # ffmpeg 설치 확인 및 설정
        self._check_and_setup_ffmpeg()
        self.llm_provider = llm_provider
        
        # STT는 항상 Whisper 사용 (배포 환경에서는 강제 librosa)
        from .config import Config
        force_librosa = Config.is_streamlit_cloud()
        
        # 임시: 환경 감지 실패 시 강제 활성화
        if not force_librosa:
            # packages.txt 파일 존재 = 배포 환경으로 간주
            packages_txt = Path(__file__).parent.parent.parent / "packages.txt"
            if packages_txt.exists():
                force_librosa = True
                print("📦 packages.txt 발견 → 배포 환경으로 간주, librosa 강제 활성화")
        
        print(f"🔍 최종 librosa 강제 모드: {force_librosa}")
        self.stt_processor = STTProcessor(force_librosa=force_librosa)
        
        # LLM 체인들은 provider에 따라 다른 LLM 사용
        self.cleaning_chain = TextCleaningChain(provider=llm_provider)
        self.organizing_chain = StoryOrganizingChain(provider=llm_provider)
        self.tagging_chain = HashtagExtractionChain(provider=llm_provider)
        
        self.workflow = self._create_workflow()
    
    def _check_and_setup_ffmpeg(self):
        """ffmpeg 설치 확인 및 환경 설정"""
        try:
            # 1. ffmpeg 명령어 확인
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                print(f"✅ ffmpeg 발견: {ffmpeg_path}")
                return
            
            # 2. 일반적인 경로들 확인
            common_paths = [
                '/usr/bin/ffmpeg',
                '/usr/local/bin/ffmpeg',
                '/opt/conda/bin/ffmpeg',
                '/home/appuser/.local/bin/ffmpeg'
            ]
            
            for path in common_paths:
                if Path(path).exists():
                    print(f"✅ ffmpeg 발견 (직접 경로): {path}")
                    # PATH에 추가
                    import os
                    current_path = os.environ.get('PATH', '')
                    if path not in current_path:
                        os.environ['PATH'] = f"{Path(path).parent}:{current_path}"
                        print(f"🔧 PATH에 추가: {Path(path).parent}")
                    return
            
            # 3. apt로 설치 시도 (Streamlit Cloud에서)
            print("🔍 ffmpeg를 찾을 수 없음. 설치 시도...")
            try:
                result = subprocess.run(
                    ['apt', 'update'], 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                if result.returncode == 0:
                    result = subprocess.run(
                        ['apt', 'install', '-y', 'ffmpeg'], 
                        capture_output=True, 
                        text=True, 
                        timeout=60
                    )
                    if result.returncode == 0:
                        print("✅ ffmpeg 설치 성공")
                        return
                    else:
                        print(f"⚠️ ffmpeg 설치 실패: {result.stderr}")
                else:
                    print(f"⚠️ apt update 실패: {result.stderr}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"⚠️ apt 설치 시도 실패: {e}")
            
            # 4. conda로 설치 시도
            try:
                result = subprocess.run(
                    ['conda', 'install', '-y', 'ffmpeg'], 
                    capture_output=True, 
                    text=True, 
                    timeout=60
                )
                if result.returncode == 0:
                    print("✅ conda로 ffmpeg 설치 성공")
                    return
                else:
                    print(f"⚠️ conda ffmpeg 설치 실패: {result.stderr}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"⚠️ conda 설치 시도 실패: {e}")
            
            print("❌ ffmpeg 설치 실패 - librosa fallback 모드로 진행")
            
        except Exception as e:
            print(f"⚠️ ffmpeg 확인 중 오류: {e}")
            print("❌ ffmpeg 설정 실패 - librosa fallback 모드로 진행")
    
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
                # STT 실패해도 더미 텍스트로 나머지 체인 테스트 가능하도록
                print(f"⚠️ STT 실패, 더미 텍스트 사용: {e}")
                return {
                    "original_text": "STT 처리 실패로 인한 더미 텍스트입니다. 음성 인식이 정상적으로 작동하지 않았습니다.",
                    "stt_confidence": 0.0,
                    "error_messages": state["error_messages"] + [f"STT 오류: {str(e)}"],
                    "processing_steps": state["processing_steps"] + ["stt_failed"],
                    "processing_time": {
                        **state.get("processing_time", {}),
                        "stt": time.time() - start_time
                    }
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
            # 디버깅을 위한 로그
            processing_steps = state.get("processing_steps", [])
            print(f"Quality check - Processing steps: {processing_steps}")
            
            # 오류 메시지가 있으면 실패로 처리
            if state.get("error_messages"):
                print("Quality check result: failed (error messages exist)")
                return "failed"
            
            # 재시도 횟수 확인 (무한 루프 방지)
            stt_attempts = len([step for step in processing_steps if step == "stt_complete"])
            print(f"STT attempts so far: {stt_attempts}")
            
            # STT 재시도는 완전히 비활성화 (무한 루프 방지)
            # stt_confidence = state.get("stt_confidence", 0.0)
            # if stt_confidence < 0.3 and stt_attempts < 1:
            #     print("Quality check result: retry_stt")
            #     return "retry_stt"
            
            # 텍스트 길이 확인
            cleaned_text = state.get("cleaned_text", "")
            if len(cleaned_text.strip()) < 10:
                print("Quality check result: insufficient_content")
                return "insufficient_content"
            
            print("Quality check result: success")
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
        
        # 조건부 엣지 (품질 검사) - retry_stt 제거로 무한 루프 완전 방지
        workflow.add_conditional_edges(
            "tagger",
            quality_check_node,
            {
                "success": END,
                # "retry_stt": "stt",  # 무한 루프 방지를 위해 제거
                "insufficient_content": END,
                "failed": END
            }
        )
        
        # 워크플로우 컴파일
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
            # LangGraph 워크플로우 실행 (올바른 config 설정)
            print("워크플로우 실행 시작 (recursion_limit=100)...")
            result_state = self.workflow.invoke(initial_state, {"recursion_limit": 100})
            print(f"워크플로우 실행 완료. 처리 단계: {result_state.get('processing_steps', [])}")
            
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
            print(f"워크플로우 실행 오류: {e}")
            # Fallback: 직접 단계별 실행
            print("=== Fallback: 직접 단계별 실행 ===")
            try:
                print("STT 단계...")
                stt_text, confidence, processing_time = self.stt_processor.transcribe(audio_file_path)
                
                print("Cleaning 단계...")
                cleaned_result = self.cleaning_chain.clean(stt_text)
                cleaned_text = cleaned_result["cleaned_text"]
                
                print("Organizing 단계...")
                organized_story = self.organizing_chain.organize(cleaned_text)
                
                print("Tagging 단계...")
                story_content = cleaned_text
                if organized_story.get("sections"):
                    story_content = " ".join([s["content"] for s in organized_story["sections"]])
                tags = self.tagging_chain.extract_tags(story_content)
                
                return ProcessingResult(
                    success=True,
                    session_id=session_id,
                    original_text=stt_text,
                    cleaned_text=cleaned_text,
                    organized_story=organized_story,
                    tags=tags,
                    processing_info={
                        "steps": ["stt_complete", "cleaning_complete", "organizing_complete", "tagging_complete"],
                        "stt_confidence": confidence,
                        "removed_fillers": cleaned_result.get("removed_fillers", []),
                        "processing_time": {"stt": processing_time}
                    },
                    error_message=""
                )
                
            except Exception as fallback_error:
                print(f"Fallback도 실패: {fallback_error}")
                return ProcessingResult(
                    success=False,
                    session_id=session_id,
                    error_message=f"워크플로우 실행 오류: {str(e)}, Fallback 오류: {str(fallback_error)}"
                )