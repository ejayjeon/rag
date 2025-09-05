# # app.py
# import streamlit as st
# import os
# import tempfile
# from pathlib import Path
# import json
# from datetime import datetime
# from dotenv import load_dotenv
# from audio_processor import AudioProcessor
# from text_processor import TextProcessor

# # Load environment variables
# load_dotenv()

# # Page config
# st.set_page_config(
#     page_title="음성 분석 & 요약 도구",
#     page_icon="🎙️",
#     layout="wide"
# )

# # Initialize session state
# if 'transcription_result' not in st.session_state:
#     st.session_state.transcription_result = None
# if 'summary_result' not in st.session_state:
#     st.session_state.summary_result = None
# if 'audio_processor' not in st.session_state:
#     st.session_state.audio_processor = None
# if 'text_processor' not in st.session_state:
#     st.session_state.text_processor = None

# def initialize_processors():
#     """Initialize audio and text processors"""
#     if st.session_state.audio_processor is None:
#         with st.spinner("🎵 음성 처리 모델 로딩 중..."):
#             st.session_state.audio_processor = AudioProcessor(model_size="base")
    
#     if st.session_state.text_processor is None:
#         api_key = os.getenv("OPENAI_API_KEY")
#         if not api_key:
#             st.error("⚠️ OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
#             st.stop()
#         st.session_state.text_processor = TextProcessor(api_key)

# def process_audio_file(uploaded_file):
#     """Process uploaded audio file"""
#     # Save uploaded file temporarily
#     with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
#         tmp_file.write(uploaded_file.read())
#         tmp_file_path = tmp_file.name
    
#     try:
#         # Transcribe audio
#         with st.spinner("🎧 음성을 텍스트로 변환 중..."):
#             result = st.session_state.audio_processor.transcribe(
#                 tmp_file_path,
#                 language=st.session_state.get('language', None)
#             )
#             st.session_state.transcription_result = result
#             return result
#     finally:
#         # Clean up temp file
#         if os.path.exists(tmp_file_path):
#             os.remove(tmp_file_path)

# def main():
#     st.title("🎙️ 음성 분석 & 요약 도구")
#     st.markdown("음성 파일을 업로드하면 습관어를 제거하고 핵심 내용을 요약합니다.")
    
#     # Initialize processors
#     initialize_processors()
    
#     # Sidebar settings
#     with st.sidebar:
#         st.header("⚙️ 설정")
        
#         language = st.selectbox(
#             "언어 선택",
#             ["auto", "ko", "en"],
#             format_func=lambda x: {"auto": "자동 감지", "ko": "한국어", "en": "영어"}[x]
#         )
#         if language != "auto":
#             st.session_state.language = language
#         else:
#             st.session_state.language = None
        
#         st.divider()
        
#         summary_type = st.radio(
#             "요약 방식",
#             ["comprehensive", "bullet_points", "key_points"],
#             format_func=lambda x: {
#                 "comprehensive": "종합 요약",
#                 "bullet_points": "핵심 포인트",
#                 "key_points": "주요 메시지"
#             }[x]
#         )
        
#         st.divider()
        
#         if st.button("🗑️ 결과 초기화"):
#             st.session_state.transcription_result = None
#             st.session_state.summary_result = None
#             st.rerun()
    
#     # Main content area
#     col1, col2 = st.columns([1, 1])
    
#     with col1:
#         st.header("📤 음성 파일 업로드")
        
#         uploaded_file = st.file_uploader(
#             "음성 파일을 선택하세요",
#             type=['mp3', 'wav', 'm4a', 'ogg', 'flac'],
#             help="지원 형식: MP3, WAV, M4A, OGG, FLAC"
#         )
        
#         if uploaded_file is not None:
#             st.audio(uploaded_file)
            
#             if st.button("🚀 처리 시작", type="primary", use_container_width=True):
#                 process_audio_file(uploaded_file)
    
#     with col2:
#         if st.session_state.transcription_result:
#             st.header("📝 전사 결과")
            
#             # Display transcription
#             text = st.session_state.transcription_result['text']
#             st.text_area(
#                 "원본 텍스트",
#                 value=text,
#                 height=200,
#                 disabled=True
#             )
            
#             # Display metadata
#             with st.expander("🔍 상세 정보"):
#                 st.json({
#                     "언어": st.session_state.transcription_result.get('language', 'unknown'),
#                     "처리 시간": f"{len(text.split())} 단어",
#                     "전처리 완료": st.session_state.transcription_result.get('preprocessed', False)
#                 })
    
#     # Summary section
#     if st.session_state.transcription_result:
#         st.divider()
#         st.header("✨ 텍스트 처리 & 요약")
        
#         col3, col4 = st.columns([1, 1])
        
#         with col3:
#             if st.button("📊 텍스트 처리 및 요약", type="primary", use_container_width=True):
#                 with st.spinner("🤖 AI가 내용을 분석하고 있습니다..."):
#                     text = st.session_state.transcription_result['text']
#                     summary_result = st.session_state.text_processor.summarize_text(
#                         text,
#                         summary_type=summary_type
#                     )
#                     st.session_state.summary_result = summary_result
        
#         if st.session_state.summary_result:
#             with col4:
#                 # Statistics
#                 st.metric(
#                     "습관어 제거",
#                     f"{st.session_state.summary_result['fillers_removed']}개",
#                     f"-{st.session_state.summary_result['original_length'] - st.session_state.summary_result['cleaned_length']} 글자"
#                 )
            
#             # Display summary
#             st.subheader("📌 요약 결과")
#             st.info(st.session_state.summary_result['summary'])
            
#             # Extract topics
#             with st.expander("🏷️ 주요 주제"):
#                 text = st.session_state.transcription_result['text']
#                 topics = st.session_state.text_processor.extract_topics(text)
#                 st.write(", ".join(topics))
            
#             # Download results
#             st.divider()
#             col5, col6 = st.columns(2)
            
#             with col5:
#                 # Prepare download data
#                 download_data = {
#                     "timestamp": datetime.now().isoformat(),
#                     "original_text": st.session_state.transcription_result['text'],
#                     "summary": st.session_state.summary_result['summary'],
#                     "statistics": {
#                         "fillers_removed": st.session_state.summary_result['fillers_removed'],
#                         "language": st.session_state.summary_result['language']
#                     }
#                 }
                
#                 st.download_button(
#                     label="💾 결과 다운로드 (JSON)",
#                     data=json.dumps(download_data, ensure_ascii=False, indent=2),
#                     file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
#                     mime="application/json"
#                 )
            
#             with col6:
#                 # Text download
#                 text_content = f"""# 음성 분석 요약 결과
                
# ## 원본 텍스트
# {st.session_state.transcription_result['text']}

# ## 요약
# {st.session_state.summary_result['summary']}

# ## 통계
# - 습관어 제거: {st.session_state.summary_result['fillers_removed']}개
# - 언어: {st.session_state.summary_result['language']}
# """
#                 st.download_button(
#                     label="📄 결과 다운로드 (TXT)",
#                     data=text_content,
#                     file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
#                     mime="text/plain"
#                 )

# if __name__ == "__main__":
#     main()

# streamlit_app.py (Streamlit Cloud용 최적화 버전)
"""Streamlit Cloud optimized application."""

import streamlit as st
import tempfile
import os
from pathlib import Path
from datetime import datetime
import json
import whisper
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import io

# FFmpeg 경로 설정 (Streamlit Cloud용)
import shutil

# FFmpeg 경로 찾기 및 설정
ffmpeg_path = shutil.which("ffmpeg")
ffprobe_path = shutil.which("ffprobe")

st.write(f"- FFmpeg 경로: {ffmpeg_path}")
st.write(f"- FFprobe 경로: {ffprobe_path}")

if ffmpeg_path:
    AudioSegment.converter = ffmpeg_path
    st.write(f"✅ FFmpeg 경로 설정: {ffmpeg_path}")
else:
    st.warning("⚠️ FFmpeg를 찾을 수 없습니다.")

if ffprobe_path:
    AudioSegment.ffprobe = ffprobe_path
    st.write(f"✅ FFprobe 경로 설정: {ffprobe_path}")
else:
    st.warning("⚠️ FFprobe를 찾을 수 없습니다.")

# 환경 감지
IS_STREAMLIT_CLOUD = os.getenv("STREAMLIT_SHARING_MODE") == "true"

# Streamlit Cloud에서는 secrets 사용
if IS_STREAMLIT_CLOUD:
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
    WHISPER_MODEL_SIZE = st.secrets.get("WHISPER_MODEL_SIZE", "tiny")
    MAX_FILE_SIZE_MB = int(st.secrets.get("MAX_FILE_SIZE_MB", "50"))
else:
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))

# Page config
st.set_page_config(
    page_title="🎙️ 음성 분석 & 요약 도구",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 캐시된 모델 로딩
@st.cache_resource(show_spinner=False)
def load_whisper_model():
    """Load and cache Whisper model."""
    import torch
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Streamlit Cloud에서는 작은 모델 사용
    model_size = "tiny" if IS_STREAMLIT_CLOUD else WHISPER_MODEL_SIZE
    
    with st.spinner(f"🎵 Whisper {model_size} 모델 로딩 중... (최초 1회만 실행)"):
        model = whisper.load_model(model_size, device=device)
    
    return model

@st.cache_resource(show_spinner=False)
def load_text_processor():
    """Load and cache text processor."""
    from openai import OpenAI
    
    if not OPENAI_API_KEY:
        return None
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    return client

# 오디오 처리 함수 (캐싱)
@st.cache_data(show_spinner=False)
def process_audio_cached(file_bytes, file_name, language=None):
    """Process audio with caching."""
    
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix=Path(file_name).suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    
    processed_path = None  # 초기화 추가
    
    try:
        # Preprocess audio
        audio = AudioSegment.from_file(tmp_path)
        
        # Normalize volume
        target_dBFS = -20.0
        change_in_dBFS = target_dBFS - audio.dBFS
        audio = audio.apply_gain(change_in_dBFS)
        
        # Remove silence
        nonsilent = detect_nonsilent(audio, min_silence_len=1000, silence_thresh=-40)
        if nonsilent:
            processed = AudioSegment.empty()
            for start, end in nonsilent:
                processed += audio[max(0, start-100):min(len(audio), end+100)]
            audio = processed
        
        # Convert to 16kHz mono
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # Save processed audio
        processed_path = tmp_path.replace(Path(tmp_path).suffix, '_processed.wav')
        audio.export(processed_path, format='wav')
        
        # Transcribe
        model = load_whisper_model()
        result = model.transcribe(
            processed_path,
            language=language,
            task="transcribe",
            verbose=False
        )
        
        st.write(f"✅ 전사 완료!")
        st.write(f"- 전사 결과 타입: {type(result)}")
        st.write(f"- 전사 결과 키들: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        if isinstance(result, dict) and 'text' in result:
            st.write(f"- 전사된 텍스트 길이: {len(result['text'])} 문자")
        
        return result
        
    except Exception as e:
        st.error(f"❌ 오디오 처리 중 오류 발생: {str(e)}")
        st.error(f"오류 타입: {type(e).__name__}")
        import traceback
        st.error(f"상세 오류: {traceback.format_exc()}")
        return None    
        
    finally:
        # Cleanup - processed_path가 None이 아닐 때만 삭제
        for path in [tmp_path, processed_path]:
            if path and os.path.exists(path):
                os.remove(path)

def remove_fillers(text, language='auto'):
    """Remove filler words from text."""
    import re
    from collections import Counter
    
    # Detect language
    if language == 'auto':
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total = korean_chars + english_chars
        
        if total > 0:
            language = 'ko' if korean_chars / total > 0.5 else 'en'
        else:
            language = 'en'
    
    # Filler patterns
    korean_fillers = [
        r'\b(음+|어+|그+|아+)\b',
        r'\b(있잖아|거든|이제|뭐|막|좀)\b',
    ]
    english_fillers = [
        r'\b(um+|uh+|ah+|oh+)\b',
        r'\b(like|you know|I mean)\b',
    ]
    
    patterns = korean_fillers if language == 'ko' else english_fillers
    
    removed = []
    cleaned = text
    
    for pattern in patterns:
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        removed.extend(matches)
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return {
        'cleaned': cleaned,
        'removed_count': len(removed),
        'removed_words': dict(Counter(removed))
    }

def summarize_text(text, summary_type='comprehensive'):
    """Summarize text using OpenAI."""
    client = load_text_processor()
    
    if not client:
        return None
    
    prompts = {
        'comprehensive': "다음 텍스트를 종합적으로 요약해주세요:\n\n",
        'bullet_points': "다음 텍스트를 5개 이내의 핵심 포인트로 요약해주세요:\n\n",
        'key_points': "다음 텍스트에서 가장 중요한 메시지를 추출해주세요:\n\n"
    }
    
    prompt = prompts.get(summary_type, prompts['comprehensive']) + text[:3000]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"요약 중 오류: {e}")
        return None

# Main UI
def main():
    st.title("🎙️ 음성 분석 & 요약 도구")
    
    # 경고 메시지 (Streamlit Cloud)
    if IS_STREAMLIT_CLOUD:
        st.info("☁️ Streamlit Cloud에서 실행 중 (모델: Whisper tiny, 파일 크기 제한: 50MB)")
    
    # API 키 확인
    if not OPENAI_API_KEY:
        st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. 요약 기능이 제한됩니다.")
        st.markdown("[API 키 받기](https://platform.openai.com/api-keys)")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ 설정")
        
        language = st.selectbox(
            "언어",
            ["auto", "ko", "en"],
            format_func=lambda x: {"auto": "자동 감지", "ko": "한국어", "en": "영어"}[x]
        )
        
        summary_type = st.radio(
            "요약 방식",
            ["comprehensive", "bullet_points", "key_points"],
            format_func=lambda x: {
                "comprehensive": "종합 요약",
                "bullet_points": "핵심 포인트",
                "key_points": "주요 메시지"
            }[x]
        )
        
        remove_filler = st.checkbox("습관어 제거", value=True)
        
        st.divider()
        
        # 사용 가이드
        with st.expander("📖 사용 가이드"):
            st.markdown("""
            1. 음성 파일 업로드 (MP3, WAV 등)
            2. 자동으로 텍스트 변환
            3. 습관어 제거 및 요약
            4. 결과 다운로드
            
            **지원 형식**: MP3, WAV, M4A, OGG, FLAC
            **최대 크기**: {MAX_FILE_SIZE_MB}MB
            """)
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 음성 파일 업로드")
        
        uploaded_file = st.file_uploader(
            "파일 선택",
            type=['mp3', 'wav', 'm4a', 'ogg', 'flac'],
            help=f"최대 {MAX_FILE_SIZE_MB}MB"
        )
        
        if uploaded_file:
            # File size check
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                st.error(f"파일 크기 초과: {file_size_mb:.1f}MB (최대: {MAX_FILE_SIZE_MB}MB)")
            else:
                st.audio(uploaded_file)
                
                if st.button("🚀 처리 시작", type="primary", use_container_width=True):
                    with st.spinner("처리 중..."):
                        # Process audio
                        result = process_audio_cached(
                            uploaded_file.getvalue(),
                            uploaded_file.name,
                            language if language != "auto" else None
                        )
                        st.session_state.transcription = result
    
    with col2:
        if 'transcription' in st.session_state and st.session_state.transcription is not None:
            st.header("📝 결과")
            
            # transcription 결과 구조 확인
            if isinstance(st.session_state.transcription, dict) and 'text' in st.session_state.transcription:
                text = st.session_state.transcription['text']
            else:
                st.error("❌ 전사 결과가 올바르지 않습니다.")
                st.write(f"전사 결과 타입: {type(st.session_state.transcription)}")
                st.write(f"전사 결과 내용: {st.session_state.transcription}")
                return
            
            # Remove fillers if requested
            if remove_filler:
                cleaned_result = remove_fillers(text)
                display_text = cleaned_result['cleaned']
                
                st.metric(
                    "습관어 제거",
                    f"{cleaned_result['removed_count']}개",
                    f"-{len(text) - len(display_text)} 글자"
                )
            else:
                display_text = text
            
            # Display text
            st.text_area("변환된 텍스트", display_text, height=200)
            
            # Summarize
            if OPENAI_API_KEY and st.button("📊 요약하기", use_container_width=True):
                with st.spinner("요약 중..."):
                    summary = summarize_text(display_text, summary_type)
                    if summary:
                        st.session_state.summary = summary
            
            # Display summary
            if 'summary' in st.session_state:
                st.divider()
                st.subheader("✨ 요약")
                st.info(st.session_state.summary)
            
            # Download
            st.divider()
            result_data = {
                "timestamp": datetime.now().isoformat(),
                "original": text,
                "cleaned": display_text if remove_filler else text,
                "summary": st.session_state.get('summary', ''),
                "language": st.session_state.transcription.get('language', 'unknown')
            }
            
            st.download_button(
                "💾 결과 다운로드",
                data=json.dumps(result_data, ensure_ascii=False, indent=2),
                file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

if __name__ == "__main__":
    # Initialize and run
    main()