"""Streamlit web interface for Multimodal RAG"""
import streamlit as st
import tempfile
from pathlib import Path
import os

# 안전한 import with 폴백
try:
    from PIL import Image
except ImportError:
    Image = None

# src 모듈 안전 import
try:
    from src.multimodal_rag import MultimodalRAG
    MULTIMODAL_RAG_AVAILABLE = True
except ImportError as e:
    MultimodalRAG = None
    MULTIMODAL_RAG_AVAILABLE = False
    IMPORT_ERROR = str(e)

# try:
from src.utils import check_ollama_status, get_ollama_models
# except ImportError:
#     def check_ollama_status():
#         return False
#     def get_ollama_models():
#         return []


# Streamlit 페이지 설정
st.set_page_config(
    page_title="🖼️ 멀티모달 RAG",
    page_icon="🤖",
    layout="wide"
)

st.title("🖼️ 멀티모달 RAG - 텍스트 + 이미지 통합 검색")

# 의존성 확인
if not MULTIMODAL_RAG_AVAILABLE:
    st.error("❌ MultimodalRAG 모듈을 import할 수 없습니다.")
    st.error(f"오류: {IMPORT_ERROR}")
    st.info("필요한 패키지를 설치하세요:")
    st.code("pip install langchain langchain-community langchain-ollama chromadb sentence-transformers")
    st.stop()

# 사이드바 - 시스템 상태
with st.sidebar:
    st.markdown("## 🔧 시스템 상태")
    
    # Ollama 상태 확인
    ollama_status = check_ollama_status()
    if ollama_status:
        st.success("🦙 Ollama 연결됨")
    else:
        st.error("❌ Ollama 연결 실패")
        st.info("Ollama를 설치하고 실행하세요:")
        st.code("ollama serve")
        st.info("⚠️ Ollama 없이도 텍스트 문서 처리는 가능합니다")
    
    # 모델 상태 확인
    models = get_ollama_models()
    if ollama_status:
        if 'llava' in str(models).lower():
            st.success("👁️ LLaVA 모델 준비됨")
        else:
            st.warning("⚠️ LLaVA 모델 없음")
            st.code("ollama pull llava")
        
        # 언어 모델 감지 (한국어 우선)
        language_models = []
        for model in models:
            if any(keyword in model.lower() for keyword in ['llama', 'gemma', 'qwen', 'mistral', 'code']):
                language_models.append(model)
        
        if language_models:
            st.success("🧠 언어모델 준비됨")
            # 현재 사용 중인 언어 모델 표시
            if 'current_language_model' in st.session_state:
                current_model = st.session_state.current_language_model
                if 'gemma2' in current_model.lower() or 'qwen' in current_model.lower():
                    st.success(f"🇰🇷 한국어 우선: {current_model}")
                else:
                    st.info(f"현재 사용: {current_model}")
            
            # 사용 가능한 언어 모델 목록 표시
            with st.expander("📋 사용 가능한 언어 모델"):
                for model in language_models:
                    if 'gemma2' in model.lower() or 'qwen' in model.lower():
                        st.success(f"🇰🇷 {model} (한국어 우수)")
                    elif 'llama' in model.lower():
                        st.info(f"🤖 {model} (영어 중심)")
                    else:
                        st.info(f"🌍 {model}")
        else:
            st.warning("⚠️ 언어모델 없음")
            st.code("ollama pull gemma2:9b")
            st.info("💡 한국어 지원을 위해 gemma2:9b 모델을 권장합니다.")
    
    st.markdown("---")
    st.markdown("## 📁 지원 파일 형식")
    st.info("""
    • **텍스트**: .txt, .md
    • **PDF**: 텍스트 + 이미지 추출
    • **이미지**: .jpg, .png, .gif 등
    """)

# RAG 시스템 초기화
if 'rag_system' not in st.session_state:
    try:
        with st.spinner("RAG 시스템 초기화 중..."):
            # 사용 가능한 언어 모델 자동 감지
            available_models = get_ollama_models()
            language_model = None
            
            # 한국어 지원 우수 모델 우선 선택 (우선순위 순)
            korean_priority_models = [
                'gemma2:9b',      # 한국어 지원 우수
                'qwen2.5:7b',     # 한국어 지원 우수
                'codellama:7b',   # 다국어 지원
                'mistral:7b',     # 다국어 지원
            ]
            
            # 우선순위 모델 중에서 찾기
            for priority_model in korean_priority_models:
                if any(priority_model.split(':')[0] in model.lower() for model in available_models):
                    language_model = priority_model
                    break
            
            # 우선순위 모델이 없으면 llama 계열 모델 찾기
            if not language_model:
                for model in available_models:
                    if 'llama' in model.lower():
                        language_model = model
                        break
            
            if not language_model:
                # 기본값 설정
                language_model = "gemma2:9b"
                st.warning(f"⚠️ 사용 가능한 언어 모델을 찾을 수 없습니다. 기본값 '{language_model}'을 사용합니다.")
                st.info("💡 한국어 지원을 위해 gemma2:9b 모델을 설치하는 것을 권장합니다.")
            else:
                if 'gemma2' in language_model.lower() or 'qwen' in language_model.lower():
                    st.success(f"🇰🇷 한국어 우선 모델 '{language_model}'을 사용합니다!")
                else:
                    st.info(f"🤖 언어 모델 '{language_model}'을 사용합니다.")
            
            st.session_state.rag_system = MultimodalRAG(llm_model=language_model)
            st.session_state.documents_added = False
            st.session_state.current_language_model = language_model
            
        st.success("✅ 시스템 초기화 완료")
    except Exception as e:
        st.error(f"❌ 시스템 초기화 실패: {str(e)}")
        st.stop()

# 파일 업로드 섹션
st.markdown("## 📁 파일 업로드")

uploaded_files = st.file_uploader(
    "파일을 선택하세요 (여러 개 선택 가능)",
    type=['txt', 'md', 'pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp'],
    accept_multiple_files=True,
    help="텍스트, PDF, 이미지 파일을 업로드할 수 있습니다"
)

# 파일 처리
if uploaded_files and st.button("📚 문서 처리 시작", type="primary"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    successful_files = []
    failed_files = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            # 진행률 업데이트
            progress = (i + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"처리 중: {uploaded_file.name} ({i+1}/{len(uploaded_files)})")
            
            # 임시 파일로 저장
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name
            
            # 파일 타입에 따른 처리
            if suffix.lower() == '.pdf':
                st.session_state.rag_system.add_pdf_document(temp_path)
            elif suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                st.session_state.rag_system.add_image_document(temp_path)
            elif suffix.lower() in ['.txt', '.md']:
                st.session_state.rag_system.add_text_document(temp_path)
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {suffix}")
            
            successful_files.append(uploaded_file.name)
            
            # 임시 파일 정리
            os.unlink(temp_path)
            
        except Exception as e:
            failed_files.append((uploaded_file.name, str(e)))
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    # 처리 결과
    progress_bar.empty()
    status_text.empty()
    
    if successful_files:
        st.session_state.documents_added = True
        st.success(f"✅ {len(successful_files)}개 파일 처리 완료!")
        
        with st.expander("처리된 파일 목록"):
            for filename in successful_files:
                st.write(f"✅ {filename}")
    
    if failed_files:
        st.error(f"❌ {len(failed_files)}개 파일 처리 실패")
        with st.expander("실패한 파일 목록"):
            for filename, error in failed_files:
                st.write(f"❌ {filename}: {error}")
    
    # 시스템 상태 표시
    if hasattr(st.session_state.rag_system, 'get_status'):
        status = st.session_state.rag_system.get_status()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 텍스트 문서", status.get('text_documents', 0))
        with col2:
            st.metric("🖼️ 이미지", status.get('image_documents', 0))
        with col3:
            st.metric("🧠 총 문서", status.get('total_documents', 0))

# 채팅 히스토리 초기화
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# 질문 섹션
if st.session_state.get('documents_added', False):
    st.markdown("---")
    st.markdown("## 💬 채팅형 질문하기")
    
    # 채팅 히스토리 표시
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant"):
                st.write(message['content'])
                
                # 메타 정보가 있으면 표시
                if 'confidence' in message:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🎯 신뢰도", f"{message['confidence']:.1%}")
                    with col2:
                        st.metric("📚 참조 소스", message.get('source_count', 0))
                
                # 참조 소스가 있으면 표시
                if 'sources' in message and message['sources']:
                    with st.expander("📚 참조된 소스 보기"):
                        for i, doc in enumerate(message['sources']):
                            st.markdown(f"**소스 {i+1}:**")
                            
                            # 메타데이터
                            metadata = doc.metadata
                            source_type = metadata.get('type', '알 수 없음')
                            source_name = metadata.get('filename', metadata.get('source', '알 수 없음'))
                            
                            st.write(f"📄 **유형**: {source_type}")
                            st.write(f"📁 **파일**: {Path(source_name).name}")
                            
                            # 내용 미리보기
                            content = doc.page_content[:300]
                            if len(doc.page_content) > 300:
                                content += "..."
                            
                            st.text_area(
                                f"내용 미리보기 {i+1}",
                                content,
                                height=100,
                                key=f"source_{i}_{message.get('timestamp', 0)}",
                                disabled=True
                            )
                            st.markdown("---")
    
    # 예시 질문 버튼
    st.markdown("**💡 예시 질문:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 문서 요약", key="summary_btn"):
            st.session_state.example_query = "업로드된 모든 문서의 주요 내용을 요약해주세요."
    
    with col2:
        if st.button("🖼️ 이미지 설명", key="image_btn"):
            st.session_state.example_query = "이미지에서 발견되는 중요한 정보를 설명해주세요."
    
    with col3:
        if st.button("🔍 상세 분석", key="analysis_btn"):
            st.session_state.example_query = "문서와 이미지를 종합하여 상세히 분석해주세요."
    
    # 새로운 질문 입력 (채팅 형태)
    if prompt := st.chat_input("질문을 입력하세요..."):
        # 사용자 질문을 채팅 히스토리에 추가
        st.session_state.chat_history.append({
            'role': 'user',
            'content': prompt,
            'timestamp': len(st.session_state.chat_history)
        })
        
        # 답변 생성
        with st.spinner("답변 생성 중..."):
            try:
                result = st.session_state.rag_system.search(prompt)
                
                # AI 답변을 채팅 히스토리에 추가
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': result.answer,
                    'confidence': result.confidence,
                    'source_count': len(result.sources),
                    'sources': result.sources,
                    'timestamp': len(st.session_state.chat_history)
                })
                
                # 페이지 새로고침으로 최신 대화 표시
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 답변 생성 중 오류: {str(e)}")
        
        # 예시 쿼리 초기화
        if 'example_query' in st.session_state:
            del st.session_state.example_query
    
    # 채팅 히스토리 초기화 버튼
    if st.session_state.chat_history:
        if st.button("🗑️ 대화 기록 지우기", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

else:
    st.info("👆 파일을 업로드하고 처리한 후에 질문할 수 있습니다.")
    
    # 사용 가이드
    st.markdown("### 🎯 사용 가이드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📄 지원 파일:**
        • 텍스트 파일 (.txt, .md)
        • PDF 문서 (텍스트 + 이미지)
        • 이미지 파일 (jpg, png 등)
        """)
    
    with col2:
        st.markdown("""
        **🤖 기능:**
        • 텍스트 문서 검색
        • 이미지 내용 분석 (Ollama 필요)
        • 멀티모달 통합 검색
        """)

# 하단 정보
st.markdown("---")
st.markdown("### 📋 시스템 정보")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **🔧 기술 스택:**
    • LangChain + ChromaDB
    • Sentence Transformers
    • Ollama (선택사항)
    """)

with col2:
    st.info("""
    **💡 팁:**
    • 여러 파일을 동시에 업로드 가능
    • Ollama 없이도 기본 기능 사용 가능
    • 이미지 분석은 LLaVA 모델 필요
    """)