# src/interfaces/streamlit_app.py
import streamlit as st
import tempfile
import os
import sys
import time
from pathlib import Path
import json
from datetime import datetime

# 프로젝트 루트를 Python path에 추가 (배포 환경 대응)
# Streamlit Cloud와 로컬 환경 모두 호환되는 방식
current_dir = Path.cwd()
file_dir = Path(__file__).parent

# 가능한 프로젝트 루트 경로들 확인
possible_roots = [
    file_dir,  # streamlit_app.py가 있는 디렉토리 (로컬)
    current_dir,  # 현재 작업 디렉토리 (Streamlit Cloud)
    Path("/mount/src/rag/stt-project/backend"),  # Streamlit Cloud 절대 경로
]

project_root = None
for root in possible_roots:
    if root.exists() and (root / "src").exists():
        project_root = root
        break

if project_root is None:
    # fallback: 현재 디렉토리 사용
    project_root = current_dir

# Python path에 추가
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 프로젝트 모듈 import
from src.services.voice_service import VoiceProcessingService
from src.core.config import Config
from src.chains.llm_factory import LLMFactory

# 환경 변수 및 LLM 연결 상태 확인
def check_environment():
    """환경 변수 및 LLM 연결 상태 확인"""
    env_status = {}
    
    # 환경 변수 확인
    env_status['LLM_PROVIDER'] = os.getenv('LLM_PROVIDER', 'Not Set')
    env_status['OPENAI_API_KEY'] = "✅ Set" if os.getenv('OPENAI_API_KEY') else "❌ Not Set"
    env_status['OLLAMA_BASE_URL'] = os.getenv('OLLAMA_BASE_URL', 'Not Set')
    
    # LLM 연결 테스트
    try:
        provider_info = LLMFactory.get_provider_info()
        env_status['LLM_Status'] = provider_info['status']
        env_status['LLM_Model'] = provider_info['model']
    except Exception as e:
        env_status['LLM_Status'] = f"❌ Error: {str(e)}"
        env_status['LLM_Model'] = "Unknown"
    
    return env_status

# 배포 디버그 정보 (배포 환경에서 확인용)
with st.expander("🔍 **배포 디버그 정보**", expanded=False):
    st.write(f"**현재 작업 디렉토리**: {Path.cwd()}")
    st.write(f"**파일 위치**: {Path(__file__)}")
    st.write(f"**선택된 프로젝트 루트**: {project_root}")
    st.write(f"**src 폴더 존재 여부**: {(project_root / 'src').exists()}")
    
    # 환경 변수 상태 확인
    st.write("### 🔧 환경 변수 상태")
    env_status = check_environment()
    for key, value in env_status.items():
        st.write(f"**{key}**: {value}")

st.write("---")

# Streamlit 페이지 설정
st.set_page_config(
    page_title="🎙️ 음성 처리 시스템",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 - 시스템 정보
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🔧 시스템 정보")
        
        # LLM 제공자 선택
        st.markdown("## 🤖 LLM 제공자 설정")
        
        # 현재 설정 확인
        current_provider = Config.get_current_llm_provider().value
        llm_config = Config.get_llm_config()
        
        # 제공자 선택
        provider_options = ["ollama", "openai"]
        provider_labels = {"ollama": "🦙 Ollama (로컬)", "openai": "🤖 OpenAI API"}
        
        selected_provider = st.selectbox(
            "LLM 제공자 선택",
            options=provider_options,
            index=provider_options.index(current_provider),
            format_func=lambda x: provider_labels[x]
        )
        
        # 환경변수로 제공자 설정 안내
        if selected_provider != current_provider:
            st.info(f"""
            💡 **제공자 변경**
            
            환경변수 설정:
            ```
            LLM_PROVIDER={selected_provider}
            ```
            또는 배포 환경에서 환경변수를 설정하세요.
            """)
        
        # 제공자별 상태 표시
        if selected_provider == "ollama":
            try:
                import requests
                response = requests.get(Config.OLLAMA_BASE_URL, timeout=5)
                if response.status_code == 200:
                    st.success(f"🦙 Ollama 연결됨 ({Config.OLLAMA_MODEL})")
                else:
                    st.error("❌ Ollama 연결 실패")
            except:
                st.error("❌ Ollama 서버 없음")
                st.code("ollama serve")
        
        elif selected_provider == "openai":
            if Config.is_openai_configured():
                st.success(f"🤖 OpenAI API 설정됨 ({Config.OPENAI_MODEL})")
            else:
                st.error("❌ OpenAI API 키 없음")
                st.info("""
                환경변수 설정 필요:
                ```
                OPENAI_API_KEY=your_api_key_here
                ```
                """)
        
        # 설정 정보
        st.markdown("---")
        st.markdown("## ⚙️ 처리 설정")
        try:
            st.info(f"""
            **STT 모델**: {Config.WHISPER_MODEL}
            **언어**: {Config.WHISPER_LANGUAGE}
            **최대 파일 크기**: {Config.MAX_AUDIO_SIZE_MB}MB
            **LLM 제공자**: {llm_config['provider']}
            **LLM 모델**: {llm_config['model']}
            """)
        except NameError:
            st.info("""
            **STT 모델**: base
            **언어**: ko
            **최대 파일 크기**: 50MB
            **LLM 제공자**: ollama
            **LLM 모델**: llama2
            """)
        
        st.markdown("---")
        st.markdown("## 📋 처리 단계")
        st.info("""
        1. **STT**: Whisper로 음성→텍스트
        2. **정리**: 습관어 제거
        3. **구조화**: 문단별 정리
        4. **태그**: 해시태그 추출
        """)

def main():
    # 제목
    st.title("🎙️ 음성 처리 시스템")
    st.markdown("### 음성을 텍스트로 변환하고 스토리를 정리해보세요!")
    
    # 사이드바 렌더링
    render_sidebar()
    
    # 서비스 초기화 (현재 선택된 provider 사용)
    @st.cache_resource
    def get_voice_service(provider: str):
        try:
            return VoiceProcessingService(llm_provider=provider)
        except Exception as e:
            st.error(f"❌ 서비스 초기화 실패: {str(e)}")
            return None
    
    # 현재 설정된 provider로 서비스 초기화
    current_provider = Config.get_current_llm_provider().value
    voice_service = get_voice_service(current_provider)
    if voice_service is None:
        st.stop()
    
    # 메인 인터페이스
    st.markdown("## 📤 음성 파일 업로드")
    
    # 파일 업로더
    uploaded_file = st.file_uploader(
        "음성 파일을 선택하세요",
        type=['wav', 'mp3', 'mp4', 'm4a', 'flac', 'ogg'],
        help=f"최대 파일 크기: {Config.MAX_AUDIO_SIZE_MB}MB"
    )
    
    # 샘플 파일 옵션 (개발용)
    st.markdown("---")
    with st.expander("🎧 샘플 파일 테스트"):
        if st.button("샘플 음성 생성 (개발용)"):
            # 개발용 샘플 텍스트
            sample_text = "안녕하세요. 음... 오늘은 정말 좋은 날씨네요. 그... 아침에 공원을 산책했는데 정말 기분이 좋았어요. 어... 새들이 지저귀고 꽃들이 예쁘게 피어있더라고요."
            
            # 임시로 텍스트 처리만 테스트
            st.session_state['sample_text'] = sample_text
            st.success("샘플 텍스트가 준비되었습니다!")
    
    # 처리 실행
    if uploaded_file is not None or st.session_state.get('sample_text'):
        st.markdown("---")
        
        # 처리 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            process_button = st.button(
                "🚀 처리 시작", 
                type="primary",
                use_container_width=True
            )
        
        if process_button:
            # 처리 시작
            with st.spinner('🔄 음성을 처리하고 있습니다...'):
                
                # 진행률 표시
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    if uploaded_file:
                        # 실제 음성 파일 처리
                        status_text.text("📁 파일을 저장하고 있습니다...")
                        progress_bar.progress(0.1)
                        
                        # 처리 실행
                        result = voice_service.process_uploaded_audio(
                            uploaded_file, 
                            uploaded_file.name
                        )
                        
                    elif st.session_state.get('sample_text'):
                        # 샘플 텍스트 처리 (STT 건너뛰기)
                        status_text.text("📝 샘플 텍스트를 처리하고 있습니다...")
                        progress_bar.progress(0.3)
                        
                        # 임시 결과 생성 (개발용)
                        from src.core.state import ProcessingResult
                        
                        result = ProcessingResult(
                            success=True,
                            session_id="sample_session",
                            original_text=st.session_state['sample_text'],
                            cleaned_text=st.session_state['sample_text'].replace("음...", "").replace("그...", "").replace("어...", ""),
                            organized_story={
                                "title": "공원 산책 이야기",
                                "summary": "아침 공원 산책에서 느낀 좋은 기분",
                                "sections": [
                                    {
                                        "section_title": "아침 산책",
                                        "content": "아침에 공원을 산책했는데 정말 기분이 좋았어요.",
                                        "key_points": ["공원 산책", "좋은 기분"]
                                    },
                                    {
                                        "section_title": "자연 감상",
                                        "content": "새들이 지저귀고 꽃들이 예쁘게 피어있더라고요.",
                                        "key_points": ["새 소리", "꽃"]
                                    }
                                ]
                            },
                            tags=["#공원", "#산책", "#아침", "#자연", "#좋은날씨"]
                        )
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ 처리 완료!")
                    
                    # 결과 저장 (세션 상태)
                    st.session_state['processing_result'] = result
                    
                except Exception as e:
                    st.error(f"❌ 처리 중 오류가 발생했습니다: {str(e)}")
                    st.exception(e)  # 개발 중에는 상세 에러 표시
    
    # 결과 표시
    if 'processing_result' in st.session_state:
        result = st.session_state['processing_result']
        
        st.markdown("---")
        st.markdown("## 📊 처리 결과")
        
        if result.success:
            # 성공 결과 표시
            st.balloons()
            
            # 결과 요약
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📝 원본 텍스트", f"{len(result.original_text)}자")
            with col2:
                st.metric("✨ 정리된 텍스트", f"{len(result.cleaned_text)}자")
            with col3:
                reduction = len(result.original_text) - len(result.cleaned_text)
                st.metric("🎯 정리 효과", f"-{reduction}자")
            with col4:
                st.metric("🏷️ 해시태그", f"{len(result.tags)}개")
            
            # 탭으로 결과 구분 표시
            tab1, tab2, tab3, tab4 = st.tabs(["📝 텍스트 비교", "📖 스토리 구조", "🏷️ 해시태그", "🔍 상세 정보"])
            
            with tab1:
                st.markdown("### 📝 텍스트 변화")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🔴 원본 텍스트**")
                    st.text_area(
                        "원본",
                        result.original_text,
                        height=200,
                        disabled=True,
                        key="original"
                    )
                
                with col2:
                    st.markdown("**🟢 정리된 텍스트**")
                    st.text_area(
                        "정리본",
                        result.cleaned_text,
                        height=200,
                        disabled=True,
                        key="cleaned"
                    )
            
            with tab2:
                st.markdown("### 📖 구조화된 스토리")
                
                if result.organized_story:
                    # 제목과 요약
                    st.markdown(f"**제목**: {result.organized_story.get('title', '제목 없음')}")
                    st.markdown(f"**요약**: {result.organized_story.get('summary', '요약 없음')}")
                    
                    # 섹션들
                    if 'sections' in result.organized_story:
                        st.markdown("**섹션들**:")
                        for i, section in enumerate(result.organized_story['sections']):
                            with st.expander(f"📑 {section.get('section_title', f'섹션 {i+1}')}"):
                                st.write(section.get('content', '내용 없음'))
                                
                                if section.get('key_points'):
                                    st.markdown("**핵심 포인트**:")
                                    for point in section['key_points']:
                                        st.markdown(f"• {point}")
                else:
                    st.info("구조화된 스토리가 없습니다.")
            
            with tab3:
                st.markdown("### 🏷️ 추출된 해시태그")
                
                if result.tags:
                    # 해시태그를 예쁘게 표시
                    tag_html = " ".join([
                        f'<span style="background-color: #e1f5fe; color: #000000; padding: 4px 8px; border-radius: 12px; margin: 2px; display: inline-block; font-weight: 500;">{tag}</span>'
                        for tag in result.tags
                    ])
                    st.markdown(tag_html, unsafe_allow_html=True)
                    
                    # 복사 가능한 텍스트
                    st.markdown("**복사용**:")
                    tag_text = " ".join(result.tags)
                    st.code(tag_text)
                else:
                    st.info("추출된 해시태그가 없습니다.")
            
            with tab4:
                st.markdown("### 🔍 처리 상세 정보")
                
                # 세션 정보
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**세션 ID**")
                    st.code(result.session_id)
                
                with col2:
                    st.markdown("**처리 시간**")
                    st.code(result.created_at)
                
                # 처리 정보
                if result.processing_info:
                    st.markdown("**처리 정보**")
                    st.json(result.processing_info)
        
        else:
            # 실패 결과 표시
            st.error("❌ 처리에 실패했습니다.")
            st.error(f"오류 메시지: {result}")
    
    # 하단 정보
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🔧 기술 스택**")
        st.caption("Whisper, LangChain, LangGraph, Streamlit")
    
    with col2:
        st.markdown("**⚡ 처리 과정**")
        st.caption("STT → 정리 → 구조화 → 태깅")
    
    with col3:
        st.markdown("**🎯 다음 단계**")
        st.caption("FastAPI 서버화 → Flutter 앱 연동")

# # 개발 디버깅 정보 (사이드바 하단)
# def render_debug_info():
#     with st.sidebar:
#         st.markdown("---")
#         with st.expander("🔧 디버그 정보"):
#             st.markdown("**Python 버전**")
#             import sys
#             st.code(f"{sys.version}")
            
#             st.markdown("**설치된 패키지 확인**")
#             try:
#                 import whisper
#                 st.success("✅ Whisper 설치됨")
#             except ImportError:
#                 st.error("❌ Whisper 없음")
            
#             try:
#                 import langchain
#                 st.success("✅ LangChain 설치됨")
#             except ImportError:
#                 st.error("❌ LangChain 없음")
            
#             try:
#                 import langgraph
#                 st.success("✅ LangGraph 설치됨")
#             except ImportError:
#                 st.error("❌ LangGraph 없음")

if __name__ == "__main__":
    # 개발 중에는 디버그 정보도 표시
    # render_debug_info()
    main()
    
    # 개발용 리셋 버튼 (사이드바)
    with st.sidebar:
        st.markdown("---")
        if st.button("🔄 결과 초기화"):
            if 'processing_result' in st.session_state:
                del st.session_state['processing_result']
            if 'sample_text' in st.session_state:
                del st.session_state['sample_text']
            st.rerun()