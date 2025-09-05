# app.py
import streamlit as st
import os
import tempfile
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv
from audio_processor import AudioProcessor
from text_processor import TextProcessor

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="음성 분석 & 요약 도구",
    page_icon="🎙️",
    layout="wide"
)

# Initialize session state
if 'transcription_result' not in st.session_state:
    st.session_state.transcription_result = None
if 'summary_result' not in st.session_state:
    st.session_state.summary_result = None
if 'audio_processor' not in st.session_state:
    st.session_state.audio_processor = None
if 'text_processor' not in st.session_state:
    st.session_state.text_processor = None

def initialize_processors():
    """Initialize audio and text processors"""
    if st.session_state.audio_processor is None:
        with st.spinner("🎵 음성 처리 모델 로딩 중..."):
            st.session_state.audio_processor = AudioProcessor(model_size="base")
    
    if st.session_state.text_processor is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("⚠️ OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            st.stop()
        st.session_state.text_processor = TextProcessor(api_key)

def process_audio_file(uploaded_file):
    """Process uploaded audio file"""
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name
    
    try:
        # Transcribe audio
        with st.spinner("🎧 음성을 텍스트로 변환 중..."):
            result = st.session_state.audio_processor.transcribe(
                tmp_file_path,
                language=st.session_state.get('language', None)
            )
            st.session_state.transcription_result = result
            return result
    finally:
        # Clean up temp file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

def main():
    st.title("🎙️ 음성 분석 & 요약 도구")
    st.markdown("음성 파일을 업로드하면 습관어를 제거하고 핵심 내용을 요약합니다.")
    
    # Initialize processors
    initialize_processors()
    
    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ 설정")
        
        language = st.selectbox(
            "언어 선택",
            ["auto", "ko", "en"],
            format_func=lambda x: {"auto": "자동 감지", "ko": "한국어", "en": "영어"}[x]
        )
        if language != "auto":
            st.session_state.language = language
        else:
            st.session_state.language = None
        
        st.divider()
        
        summary_type = st.radio(
            "요약 방식",
            ["comprehensive", "bullet_points", "key_points"],
            format_func=lambda x: {
                "comprehensive": "종합 요약",
                "bullet_points": "핵심 포인트",
                "key_points": "주요 메시지"
            }[x]
        )
        
        st.divider()
        
        if st.button("🗑️ 결과 초기화"):
            st.session_state.transcription_result = None
            st.session_state.summary_result = None
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 음성 파일 업로드")
        
        uploaded_file = st.file_uploader(
            "음성 파일을 선택하세요",
            type=['mp3', 'wav', 'm4a', 'ogg', 'flac'],
            help="지원 형식: MP3, WAV, M4A, OGG, FLAC"
        )
        
        if uploaded_file is not None:
            st.audio(uploaded_file)
            
            if st.button("🚀 처리 시작", type="primary", use_container_width=True):
                process_audio_file(uploaded_file)
    
    with col2:
        if st.session_state.transcription_result:
            st.header("📝 전사 결과")
            
            # Display transcription
            text = st.session_state.transcription_result['text']
            st.text_area(
                "원본 텍스트",
                value=text,
                height=200,
                disabled=True
            )
            
            # Display metadata
            with st.expander("🔍 상세 정보"):
                st.json({
                    "언어": st.session_state.transcription_result.get('language', 'unknown'),
                    "처리 시간": f"{len(text.split())} 단어",
                    "전처리 완료": st.session_state.transcription_result.get('preprocessed', False)
                })
    
    # Summary section
    if st.session_state.transcription_result:
        st.divider()
        st.header("✨ 텍스트 처리 & 요약")
        
        col3, col4 = st.columns([1, 1])
        
        with col3:
            if st.button("📊 텍스트 처리 및 요약", type="primary", use_container_width=True):
                with st.spinner("🤖 AI가 내용을 분석하고 있습니다..."):
                    text = st.session_state.transcription_result['text']
                    summary_result = st.session_state.text_processor.summarize_text(
                        text,
                        summary_type=summary_type
                    )
                    st.session_state.summary_result = summary_result
        
        if st.session_state.summary_result:
            with col4:
                # Statistics
                st.metric(
                    "습관어 제거",
                    f"{st.session_state.summary_result['fillers_removed']}개",
                    f"-{st.session_state.summary_result['original_length'] - st.session_state.summary_result['cleaned_length']} 글자"
                )
            
            # Display summary
            st.subheader("📌 요약 결과")
            st.info(st.session_state.summary_result['summary'])
            
            # Extract topics
            with st.expander("🏷️ 주요 주제"):
                text = st.session_state.transcription_result['text']
                topics = st.session_state.text_processor.extract_topics(text)
                st.write(", ".join(topics))
            
            # Download results
            st.divider()
            col5, col6 = st.columns(2)
            
            with col5:
                # Prepare download data
                download_data = {
                    "timestamp": datetime.now().isoformat(),
                    "original_text": st.session_state.transcription_result['text'],
                    "summary": st.session_state.summary_result['summary'],
                    "statistics": {
                        "fillers_removed": st.session_state.summary_result['fillers_removed'],
                        "language": st.session_state.summary_result['language']
                    }
                }
                
                st.download_button(
                    label="💾 결과 다운로드 (JSON)",
                    data=json.dumps(download_data, ensure_ascii=False, indent=2),
                    file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col6:
                # Text download
                text_content = f"""# 음성 분석 요약 결과
                
## 원본 텍스트
{st.session_state.transcription_result['text']}

## 요약
{st.session_state.summary_result['summary']}

## 통계
- 습관어 제거: {st.session_state.summary_result['fillers_removed']}개
- 언어: {st.session_state.summary_result['language']}
"""
                st.download_button(
                    label="📄 결과 다운로드 (TXT)",
                    data=text_content,
                    file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()