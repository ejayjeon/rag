"""
Streamlit 웹 인터페이스
"""
import streamlit as st
import tempfile
from pathlib import Path
try:
    from src.rag_system import SimpleRAG
except ImportError:
    from rag_system import SimpleRAG


def main():
    st.title("🤖 Simple RAG System")
    st.markdown("문서를 업로드하고 질문해보세요!")
    
    # CSS 스타일 추가 - chat input hover 색상 변경
    st.markdown("""
    <style>
    /* Chat input 기본 스타일 수정 */
    .stChatInput > div > div > textarea {
        border: 2px solid #e6e6e6 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    /* Hover 시 파란색으로 변경 */
    .stChatInput > div > div > textarea:hover {
        border-color: #4CAF50 !important;
        box-shadow: 0 0 5px rgba(76, 175, 80, 0.3) !important;
    }
    
    /* Focus 시 더 진한 파란색 */
    .stChatInput > div > div > textarea:focus {
        border-color: #45a049 !important;
        box-shadow: 0 0 8px rgba(69, 160, 73, 0.5) !important;
        outline: none !important;
    }
    
    /* Chat input 컨테이너 스타일 */
    .stChatInput {
        background-color: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 사이드바에서 모델 선택
    model_type = st.sidebar.selectbox(
        "모델 선택",
        ["openai", "ollama"],
        help="OpenAI는 유료이지만 고품질, Ollama는 무료이지만 로컬 설치 필요"
    )

    # 기존 PDF 사용 옵션
    use_existing = st.checkbox("documents/sample.pdf 파일 사용하기")
    
    uploaded_files = None
    
    if use_existing:
        if Path("documents/sample.pdf").exists():
            pdf_path = "documents/sample.pdf"
            st.success("✅ documents/sample.pdf 파일을 사용합니다!")
            # 기존 PDF를 uploaded_files 형태로 처리
            uploaded_files = [pdf_path]  # 문자열 경로로 설정
        else:
            st.error("❌ documents/sample.pdf 파일을 찾을 수 없습니다.")
            uploaded_files = None
    else:
        # 파일 업로드
        uploaded_files = st.file_uploader(
            "문서 파일을 업로드하세요",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            help="PDF 또는 텍스트 파일만 지원합니다"
        )

    if uploaded_files:
        # RAG 시스템 초기화 (세션 상태로 관리)
        if 'rag_system' not in st.session_state:
            st.session_state.rag_system = None
            st.session_state.documents_loaded = False

        # 문서가 변경되었는지 확인
        if use_existing:
            current_files = uploaded_files  # 경로 리스트
        else:
            current_files = [f.name for f in uploaded_files] if uploaded_files else []
            
        if ('loaded_files' not in st.session_state or 
            st.session_state.loaded_files != current_files):
            
            st.session_state.documents_loaded = False
            st.session_state.loaded_files = current_files

        # 문서 처리
        if not st.session_state.documents_loaded:
            with st.spinner('문서를 분석하고 있습니다...'):
                try:
                    # 파일 경로 처리
                    temp_files = []
                    
                    if use_existing:
                        # 기존 PDF 파일 사용
                        temp_files = uploaded_files  # 이미 경로 리스트
                    else:
                        # 업로드된 파일을 임시 파일로 저장
                        for uploaded_file in uploaded_files:
                            with tempfile.NamedTemporaryFile(
                                delete=False, 
                                suffix=Path(uploaded_file.name).suffix
                            ) as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                temp_files.append(tmp_file.name)

                    # RAG 시스템 초기화
                    rag = SimpleRAG()
                    documents = rag.load_documents(temp_files)
                    rag.create_vectorstore(documents)
                    rag.setup_qa_chain(model_type)
                    
                    st.session_state.rag_system = rag
                    st.session_state.documents_loaded = True
                    
                    st.success(f"✅ {len(documents)}개의 문서 청크를 분석했습니다!")
                    
                except Exception as e:
                    st.error(f"❌ 문서 처리 중 오류가 발생했습니다: {e}")
                    return

        # 채팅 히스토리 초기화
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # 질문 입력
        if st.session_state.documents_loaded:
            st.markdown("---")
            
            # 채팅 히스토리 표시
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.write(message['content'])
                        # 소스 문서가 있으면 표시
                        if 'source_documents' in message:
                            with st.expander("📚 참조 문서 보기"):
                                for i, doc in enumerate(message['source_documents']):
                                    st.markdown(f"**문서 {i+1}:**")
                                    st.text(doc.page_content[:200] + "...")
                                    st.markdown("---")

            # 새로운 질문 입력
            if prompt := st.chat_input("질문을 입력하세요..."):
                # 사용자 질문을 채팅 히스토리에 추가
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': prompt
                })

                # 답변 생성
                with st.spinner('답변을 생성하고 있습니다...'):
                    try:
                        result = st.session_state.rag_system.ask_question(prompt)
                        
                        # AI 답변을 채팅 히스토리에 추가
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': result['answer'],
                            'source_documents': result.get('source_documents', [])
                        })
                        
                        # 페이지 새로고침으로 최신 대화 표시
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ 답변 생성 중 오류가 발생했습니다: {e}")

            # 채팅 히스토리 초기화 버튼
            if st.session_state.chat_history:
                if st.button("🗑️ 대화 기록 지우기"):
                    st.session_state.chat_history = []
                    # 문서 상태도 초기화하여 재선택 시 자동 분석되도록 함
                    st.session_state.documents_loaded = False
                    if 'loaded_files' in st.session_state:
                        del st.session_state.loaded_files
                    st.rerun()

    else:
        st.info("👆 먼저 문서 파일을 업로드해주세요!")


# Ollama 연결 상태 확인
def check_ollama():
    try:
        import requests
        response = requests.get("http://localhost:11434", timeout=5)
        return response.status_code == 200
    except:
        return False


# 사이드바에 상태 정보
with st.sidebar:
    st.markdown("## 🔧 시스템 상태")
    
    if check_ollama():
        st.success("🦙 Ollama 연결됨")
    else:
        st.error("❌ Ollama 연결 안됨")
        st.markdown("터미널에서 `ollama serve` 실행하세요")
    
    # 모델 정보
    st.markdown("## 🧠 사용 모델")
    st.info("Llama2 (7B)")
    
    st.markdown("## 📁 파일 위치")
    st.code("documents/sample.pdf")


if __name__ == "__main__":
    main()