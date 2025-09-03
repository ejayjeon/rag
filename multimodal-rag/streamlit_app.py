"""Streamlit web interface for Multimodal RAG"""
import streamlit as st
import tempfile
from pathlib import Path
import os
import time

# .env 파일 지원 추가
try:
    from dotenv import load_dotenv
    load_dotenv()  # .env 파일에서 환경변수 로드
except ImportError:
    pass  # python-dotenv가 없어도 계속 진행

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
from src.utils import (
    check_ollama_status, 
    get_ollama_models, 
    get_current_ollama_url, 
    test_ngrok_connection,
    update_ngrok_url,
    get_current_ngrok_url,
    call_ollama_api,
    generate_ollama_response
)
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

# 함수 정의
def _verify_openai_key(api_key: str):
    """OpenAI API 키 검증 함수"""
    # API 키 형식 검증
    if not api_key.startswith('sk-'):
        st.error("❌ API 키는 'sk-'로 시작해야 합니다")
        st.session_state.openai_verified = False
        return
    elif len(api_key) < 50:
        st.error("❌ API 키 길이가 너무 짧습니다")
        st.session_state.openai_verified = False
        return
    
    # 실시간 연결 테스트
    with st.spinner("API 키 검증 중..."):
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            models = client.models.list()
            st.success("✅ OpenAI API 키 검증 성공!")
            st.session_state.openai_verified = True
        except openai.AuthenticationError:
            st.error("❌ 유효하지 않은 API 키입니다")
            st.session_state.openai_verified = False
        except openai.PermissionDeniedError:
            st.error("❌ API 키 권한이 부족합니다")
            st.session_state.openai_verified = False
        except openai.RateLimitError:
            st.warning("⚠️ 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요")
            st.session_state.openai_verified = False
        except Exception as e:
            st.error(f"❌ 연결 오류: {str(e)}")
            st.session_state.openai_verified = False

# 의존성 확인
if not MULTIMODAL_RAG_AVAILABLE:
    st.error("❌ MultimodalRAG 모듈을 import할 수 없습니다.")
    st.error(f"오류: {IMPORT_ERROR}")
    st.info("필요한 패키지를 설치하세요:")
    st.code("pip install langchain langchain-community langchain-ollama chromadb sentence-transformers")
    st.stop()

# 사이드바 - 시스템 상태
with st.sidebar:
    st.markdown("## 🤖 LLM 프로바이더 선택")
    
    # 모델 선택
    llm_provider = st.selectbox(
        "LLM 프로바이더",
        ["ollama", "openai"],
        help="Ollama는 무료이지만 로컬 설치 필요, OpenAI는 유료이지만 고품질"
    )
    
    # OpenAI API Key 입력 (OpenAI 선택시에만 표시)
    if llm_provider == "openai":
        # API 키 확인 (우선순위: Streamlit Secrets > 환경변수)
        auto_api_key = None
        key_source = None
        
        # 1. Streamlit Cloud Secrets 확인 (배포 환경)
        try:
            if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                auto_api_key = st.secrets["OPENAI_API_KEY"]
                key_source = "Streamlit Cloud Secrets"
        except Exception:
            pass
        
        # 2. 환경변수 확인 (로컬 환경)
        if not auto_api_key:
            env_api_key = os.getenv('OPENAI_API_KEY')
            if env_api_key:
                auto_api_key = env_api_key
                key_source = "환경변수"
        
        # API 키 사용 방법 선택
        if auto_api_key:
            # 환경변수/Secrets에 키가 있는 경우
            st.success(f"🔑 {key_source}에서 API 키를 발견했습니다 (sk-...{auto_api_key[-4:]})")
            
            api_key_mode = st.radio(
                "API 키 사용 방법 선택:",
                ["🔐 자동 사용 (권장)", "✏️ 직접 입력"],
                key="api_key_mode",
                help="자동 사용은 환경변수나 Secrets의 키를 사용하고, 직접 입력은 새로운 키를 입력할 수 있습니다."
            )
            
            if api_key_mode == "🔐 자동 사용 (권장)":
                # 자동 키 사용
                st.session_state.openai_api_key = auto_api_key
                
                # 키 검증
                with st.spinner(f"{key_source} API 키 검증 중..."):
                    try:
                        import openai
                        client = openai.OpenAI(api_key=auto_api_key)
                        models = client.models.list()
                        st.success(f"✅ {key_source} API 키 검증 성공!")
                        st.session_state.openai_verified = True
                    except Exception as e:
                        st.error(f"❌ {key_source} API 키 검증 실패: {str(e)}")
                        st.session_state.openai_verified = False
            
            else:  # 직접 입력 모드
                openai_api_key = st.text_input(
                    "OpenAI API Key (직접 입력)",
                    type="password",
                    help="새로운 API 키를 입력하세요",
                    placeholder="sk-...",
                    key="manual_api_key"
                )
                
                if openai_api_key:
                    st.session_state.openai_api_key = openai_api_key
                    _verify_openai_key(openai_api_key)
                else:
                    st.session_state.openai_verified = False
        
        else:
            # 환경변수에 키가 없는 경우 - 직접 입력만 제공
            st.warning("🔑 환경변수나 Streamlit Secrets에 OPENAI_API_KEY가 설정되지 않았습니다")
            st.info("💡 .env 파일이나 시스템 환경변수에 OPENAI_API_KEY를 설정하면 자동으로 사용할 수 있습니다")
            
            openai_api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="OpenAI API 키를 입력하세요 (sk-...)",
                placeholder="sk-...",
                key="fallback_api_key"
            )
            
            if openai_api_key:
                st.session_state.openai_api_key = openai_api_key
                _verify_openai_key(openai_api_key)
            else:
                st.session_state.openai_verified = False
    
    st.markdown("## 🔧 시스템 상태")
    
    # Ollama 상태 확인 (ollama 선택시에만)
    if llm_provider == "ollama":
        try:
            # Streamlit Cloud 환경 감지
            import os
            is_streamlit_cloud = os.getenv('STREAMLIT_SERVER_PORT') is not None
            
            if is_streamlit_cloud:
                st.info("☁️ Streamlit Cloud 환경에서 실행 중")
                st.warning("⚠️ Ollama 사용을 위해서는 ngrok 터널이 필요합니다")
                
                # ngrok 설정 안내
                with st.expander("🌐 ngrok 설정 방법", expanded=False):
                    st.markdown("""
                    **1. 로컬에서 ngrok 실행:**
                    ```bash
                    ngrok http 11434
                    ```
                    
                    **2. 생성된 URL을 환경변수에 설정:**
                    ```bash
                    export OLLAMA_HOST="https://xxxxx.ngrok-free.app"
                    ```
                    
                    **3. Streamlit Cloud에서 환경변수 설정:**
                    - Settings → Secrets에 추가:
                    ```toml
                    OLLAMA_HOST = "https://xxxxx.ngrok-free.app"
                    ```
                    """)
            
            ollama_status, current_url = check_ollama_status()
            if ollama_status:
                st.success("🦙 Ollama 연결됨")
                st.info(f"📍 연결된 서버: {current_url}")
                
                # ngrok 연결 상태 확인
                if "ngrok" in current_url:
                    st.success("🌐 ngrok 터널 연결됨")
                elif "localhost" in current_url:
                    st.info("🏠 로컬 서버 연결됨")
            else:
                if is_streamlit_cloud:
                    st.error("❌ ngrok 터널 연결 실패")
                    st.info("💡 위의 ngrok 설정 방법을 따라주세요")
                else:
                    st.error("❌ Ollama 연결 실패")
                    st.info("Ollama를 설치하고 실행하세요:")
                    st.code("ollama serve")
                st.info("⚠️ OpenAI로 전환하거나 텍스트 문서 처리만 가능합니다")
        except Exception as e:
            st.error(f"❌ Ollama 상태 확인 오류: {str(e)}")
            st.info("⚠️ OpenAI로 전환하거나 텍스트 문서 처리만 가능합니다")
    else:
        # OpenAI 선택시
        if st.session_state.get('openai_verified', False):
            st.success("🤖 OpenAI 연결 성공!")
            
            # 추가 정보 버튼
            if st.button("📋 사용 가능한 모델 보기"):
                with st.spinner("모델 목록 불러오는 중..."):
                    try:
                        import openai
                        client = openai.OpenAI(api_key=st.session_state.openai_api_key)
                        models = client.models.list()
                        
                        # 사용 가능한 모델 표시 (ChatGPT 관련 모델 우선)
                        chat_models = [m for m in models.data if any(x in m.id for x in ['gpt-', 'text-'])]
                        other_models = [m for m in models.data if m not in chat_models]
                        
                        with st.expander("📋 채팅/텍스트 생성 모델", expanded=True):
                            for model in chat_models[:8]:
                                st.text(f"• {model.id}")
                        
                        if other_models:
                            with st.expander("🔧 기타 모델"):
                                for model in other_models[:5]:
                                    st.text(f"• {model.id}")
                                    
                    except Exception as e:
                        st.error(f"❌ 모델 목록 불러오기 실패: {str(e)}")
        
        elif 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
            st.error("❌ OpenAI API 키 검증 실패")
            st.info("💡 올바른 API 키를 입력해주세요")
        else:
            st.warning("🔑 OpenAI API 키를 입력해주세요")
    
    # # ngrok 연결 테스트 및 URL 업데이트
    # st.markdown("### 🌐 ngrok 설정")
    
    # # 현재 ngrok URL 표시
    # current_ngrok_url = get_current_ngrok_url()
    # st.info(f"현재 ngrok URL: `{current_ngrok_url}`")
    
    # # ngrok URL 업데이트
    # new_ngrok_url = st.text_input(
    #     "새로운 ngrok URL 입력",
    #     value=current_ngrok_url,
    #     help="ngrok URL이 변경되었을 때 여기에 입력하세요"
    # )
    
    # if st.button("🔄 ngrok URL 업데이트"):
    #     if new_ngrok_url != current_ngrok_url:
    #         update_ngrok_url(new_ngrok_url)
    #         st.success(f"ngrok URL이 업데이트되었습니다: {new_ngrok_url}")
    #         st.rerun()
    
    # # ngrok 연결 테스트 버튼
    # if st.button("🔍 ngrok 연결 테스트"):
    #     with st.spinner("ngrok 연결 테스트 중..."):
    #         ngrok_success, ngrok_message = test_ngrok_connection()
    #         if ngrok_success:
    #             st.success(ngrok_message)
    #         else:
    #             st.error(ngrok_message)
    #             st.info("💡 ngrok URL이 변경되었을 수 있습니다. 위의 입력창에 새로운 URL을 입력하세요.")
    
    # 프로바이더별 API 테스트
    if llm_provider == "ollama":
        st.markdown("### 🧪 Ollama API 테스트")
        if st.button("🔍 API 연결 테스트"):
            with st.spinner("API 연결 테스트 중..."):
                try:
                    # 모델 목록 가져오기 테스트
                    models_response = call_ollama_api('api/tags')
                    if models_response and 'models' in models_response:
                        st.success(f"✅ API 연결 성공! 모델 {len(models_response['models'])}개 발견")
                        # 모델 목록 표시
                        with st.expander("📋 사용 가능한 모델"):
                            for model in models_response['models']:
                                model_name = model.get('name', 'Unknown')
                                st.text(f"• {model_name}")
                    else:
                        st.error("❌ API 연결 실패")
                        st.info("💡 Ollama 서버가 실행 중인지 확인하세요")
                except Exception as e:
                    st.error(f"❌ API 테스트 오류: {str(e)}")
    elif llm_provider == "openai":
        st.markdown("### 🤖 OpenAI API 상태")
        if st.session_state.get('openai_verified', False):
            st.success("✅ OpenAI API 연결 확인됨")
        else:
            st.warning("⚠️ 위의 API 키를 입력하여 연결을 확인하세요")
    
    # 프로바이더별 모델 상태 확인
    st.markdown("### 🤖 모델 상태")
    
    if llm_provider == "ollama":
        models = get_ollama_models()
        try:
            ollama_status, _ = check_ollama_status()
            if ollama_status:
                # Vision 모델 (이미지 분석용)
                if 'llava' in str(models).lower():
                    st.success("👁️ LLaVA 모델 준비됨 (이미지 분석 가능)")
                else:
                    st.warning("⚠️ LLaVA 모델 없음 (이미지 분석 불가)")
                    st.code("ollama pull llava")
                
                # 언어 모델 감지 (한국어 우선)
                language_models = []
                for model in models:
                    if any(keyword in model.lower() for keyword in ['llama', 'gemma', 'qwen', 'mistral', 'code']):
                        language_models.append(model)
                
                if language_models:
                    st.success("🧠 텍스트 언어모델 준비됨")
                    # 현재 사용 중인 언어 모델 표시
                    if 'current_language_model' in st.session_state:
                        current_model = st.session_state.current_language_model
                        if 'gemma2' in current_model.lower() or 'qwen' in current_model.lower():
                            st.success(f"🇰🇷 한국어 우선: {current_model}")
                        else:
                            st.info(f"현재 사용: {current_model}")
                    
                    # 사용 가능한 언어 모델 목록 표시
                    with st.expander("📋 사용 가능한 Ollama 모델"):
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
            else:
                st.warning("⚠️ Ollama 서버에 연결할 수 없습니다")
                st.info("💡 OpenAI로 전환하시면 모든 기능을 사용할 수 있습니다")
        except Exception as e:
            st.error(f"❌ 모델 상태 확인 오류: {str(e)}")
    
    elif llm_provider == "openai":
        if st.session_state.get('openai_verified', False):
            # OpenAI 모델 상태 및 선택
            try:
                import openai
                client = openai.OpenAI(api_key=st.session_state.openai_api_key)
                available_models = client.models.list()
                
                # 사용 가능한 모델 필터링
                chat_models = [m.id for m in available_models.data if any(x in m.id for x in ['gpt-', 'text-'])]
                vision_models = [m.id for m in available_models.data if 'vision' in m.id.lower()]
                
                if chat_models:
                    st.success(f"🧠 텍스트 모델: {len(chat_models)}개 준비됨")
                    
                    # 현재 선택된 모델 표시
                    if 'current_language_model' in st.session_state:
                        current_model = st.session_state.current_language_model
                        if 'gpt-4' in current_model:
                            st.success(f"🚀 현재 선택: {current_model} (최고 품질)")
                        elif 'gpt-3.5' in current_model:
                            st.info(f"⚡ 현재 선택: {current_model} (빠른 속도)")
                        else:
                            st.info(f"🔧 현재 선택: {current_model}")
                    
                    # 모델 선택 드롭다운
                    selected_model = st.selectbox(
                        "🤖 텍스트 모델 선택",
                        options=chat_models,
                        index=0,
                        help="사용할 텍스트 생성 모델을 선택하세요"
                    )
                    
                    # 모델별 특징 안내
                    with st.expander("📋 모델별 특징", expanded=False):
                        for model in chat_models[:5]:  # 처음 5개만 표시
                            if 'gpt-4' in model:
                                st.success(f"🚀 {model}: 최고 품질, 높은 비용")
                            elif 'gpt-3.5' in model:
                                st.info(f"⚡ {model}: 빠른 속도, 적당한 비용")
                            else:
                                st.info(f"🔧 {model}: 특수 용도")
                
                if vision_models:
                    st.success(f"👁️ Vision 모델: {len(vision_models)}개 준비됨")
                    
                    # Vision 모델 자동 선택 (최신 모델 우선)
                    recommended_vision_models = [
                        'gpt-4o',           # 최신 통합 모델
                        'gpt-4o-mini',      # 경량 버전
                        'gpt-4-vision-preview',  # 구버전 (fallback)
                    ]
                    
                    # 사용 가능한 모델 중에서 권장 모델 찾기
                    selected_vision_model = None
                    for recommended in recommended_vision_models:
                        if recommended in vision_models:
                            selected_vision_model = recommended
                            break
                    
                    if selected_vision_model:
                        st.success(f"🎯 권장 Vision 모델: {selected_vision_model}")
                        # 세션에 Vision 모델 저장
                        st.session_state.selected_vision_model = selected_vision_model
                    else:
                        st.warning("⚠️ 권장 Vision 모델을 찾을 수 없습니다")
                        selected_vision_model = vision_models[0] if vision_models else "gpt-4o"
                        st.info(f"사용할 Vision 모델: {selected_vision_model}")
                    
                    with st.expander("📋 Vision 모델 목록", expanded=False):
                        for model in vision_models:
                            if model == selected_vision_model:
                                st.success(f"👁️ {model} (선택됨)")
                            else:
                                st.info(f"👁️ {model}")
                
                # 사용 가능한 기능 안내
                with st.expander("📋 OpenAI 멀티모달 기능", expanded=False):
                    st.info("• 🤖 텍스트 생성: GPT-3.5/4 시리즈")
                    st.info("• 👁️ 이미지 분석: GPT-4o (최신 Vision 모델)")
                    st.info("• 🔍 이미지 OCR: 텍스트 추출 가능")
                    st.info("• 📊 차트/그래프 이해: 복잡한 시각 데이터 분석")
                    st.info("• 🌍 다국어 지원: 한국어 포함 100+ 언어")
                    st.info("• ⚡ 빠른 응답속도")
                    st.info("• 🎯 높은 품질 & 정확도")
                    
            except Exception as e:
                st.warning(f"⚠️ 모델 정보를 가져올 수 없습니다: {str(e)}")
                st.info("💡 API 키가 올바른지 확인해주세요")
        else:
            st.warning("⚠️ OpenAI API 키 검증이 필요합니다")
            st.info("💡 위에서 유효한 API 키를 입력하세요")
    
    st.markdown("---")
    st.markdown("## 📁 지원 파일 형식")
    st.info("""
    • **텍스트**: .txt, .md
    • **PDF**: 텍스트 + 이미지 추출
    • **이미지**: .jpg, .png, .gif 등
    """)
    
    # 시스템 정보 섹션
    st.markdown("---")
    st.markdown("### 📋 시스템 정보")
    
    if llm_provider == "ollama":
        st.info("""
        **🔧 기술 스택:**
        • LangChain + ChromaDB
        • Sentence Transformers
        • Ollama (로컬 LLM)
        """)
        
        st.info("""
        **💡 팁:**
        • 여러 파일을 동시에 업로드 가능
        • Ollama 서버 실행 필요
        • 이미지 분석은 LLaVA 모델 필요
        """)
    else:
        st.info("""
        **🔧 기술 스택:**
        • LangChain + ChromaDB
        • Sentence Transformers
        • OpenAI API (클라우드 LLM)
        """)
        
        st.info("""
        **💡 팁:**
        • 여러 파일을 동시에 업로드 가능
        • 인터넷 연결 필요
        • API 사용료 발생 (토큰당 과금)
        """)

# RAG 시스템 초기화 (조건부)
should_initialize = False
if llm_provider == "ollama":
    should_initialize = True  # Ollama는 항상 초기화 가능
elif llm_provider == "openai":
    # OpenAI는 키가 있거나 검증된 경우만 초기화
    env_key = os.getenv('OPENAI_API_KEY')
    has_env_key = bool(env_key)
    has_verified_key = st.session_state.get('openai_verified', False)
    should_initialize = has_env_key or has_verified_key

if 'rag_system' not in st.session_state and should_initialize:
    try:
        with st.spinner("RAG 시스템 초기화 중..."):
            language_model = None
            
            if llm_provider == "ollama":
                # Ollama: 사용 가능한 언어 모델 자동 감지
                available_models = get_ollama_models()
                
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
            
            # OpenAI API 키 설정 (우선순위: 검증된 키 > 환경변수)
            openai_api_key = None
            if llm_provider == "openai":
                if st.session_state.get('openai_verified', False) and st.session_state.get('openai_api_key'):
                    openai_api_key = st.session_state.openai_api_key
                else:
                    # 환경변수 확인
                    env_key = os.getenv('OPENAI_API_KEY')
                    if env_key:
                        openai_api_key = env_key
                        st.info("🔑 환경변수 OPENAI_API_KEY를 사용합니다")
                    else:
                        st.warning("⏳ OpenAI API 키 설정을 기다리는 중...")
                        st.info("💡 위의 사이드바에서 API 키를 설정해주세요")
                        st.stop()
            
            elif llm_provider == "openai":
                # OpenAI: 사용 가능한 모델 중에서 선택
                try:
                    import openai
                    client = openai.OpenAI(api_key=openai_api_key)
                    available_models = client.models.list()
                    
                    # 사용 가능한 모델 필터링 (ChatGPT 관련 모델 우선)
                    chat_models = [m.id for m in available_models.data if any(x in m.id for x in ['gpt-', 'text-'])]
                    
                    if chat_models:
                        # 모델 선택 드롭다운
                        selected_model = st.selectbox(
                            "🤖 OpenAI 모델 선택",
                            options=chat_models,
                            index=0,  # 기본값: 첫 번째 모델
                            help="사용할 OpenAI 모델을 선택하세요. GPT-4는 더 정확하지만 비용이 높습니다."
                        )
                        language_model = selected_model
                        st.success(f"🤖 OpenAI 모델 '{language_model}'을 선택했습니다!")
                        
                        # 모델별 특징 안내
                        if 'gpt-4' in language_model:
                            st.info("🚀 GPT-4: 최고 품질, 높은 비용")
                        elif 'gpt-3.5' in language_model:
                            st.info("⚡ GPT-3.5: 빠른 속도, 적당한 비용")
                        else:
                            st.info("🔧 기타 모델: 특수 용도")
                    else:
                        # 모델을 가져올 수 없는 경우 기본값 사용
                        language_model = "gpt-3.5-turbo"
                        st.warning(f"⚠️ 모델 목록을 가져올 수 없어 기본값 '{language_model}'을 사용합니다.")
                        
                except Exception as e:
                    # 오류 발생 시 기본값 사용
                    language_model = "gpt-3.5-turbo"
                    st.warning(f"⚠️ 모델 선택 중 오류 발생: {str(e)}")
                    st.info(f"기본값 '{language_model}'을 사용합니다.")
                
                # 선택된 모델을 세션에 저장
                if 'selected_model' in locals():
                    st.session_state.selected_openai_model = selected_model
            
            # Vision 모델 선택 (OpenAI인 경우)
            if llm_provider == "openai":
                # 세션에서 선택된 Vision 모델 사용, 없으면 기본값
                vision_model = st.session_state.get('selected_vision_model', 'gpt-4o')
                st.info(f"👁️ Vision 모델: {vision_model} 사용")
            else:
                vision_model = "llava"
            
            st.session_state.rag_system = MultimodalRAG(
                llm_model=language_model,
                vision_model=vision_model,
                llm_provider=llm_provider,
                openai_api_key=openai_api_key
            )
            st.session_state.documents_added = False
            st.session_state.current_language_model = language_model
            
        st.success("✅ 시스템 초기화 완료")
    except Exception as e:
        st.error(f"❌ 시스템 초기화 실패: {str(e)}")
        st.stop()

# 시스템이 준비되지 않은 경우 메시지 표시
if 'rag_system' not in st.session_state:
    if llm_provider == "openai":
        st.info("🔑 OpenAI API 키 설정 후 시스템이 자동으로 초기화됩니다")
        st.info("👆 위의 사이드바에서 API 키를 설정해주세요")
    else:
        st.info("⚙️ 시스템 초기화를 위해 잠시만 기다려주세요...")
    st.stop()

# 세션 상태 초기화 (먼저 실행)
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

if 'file_contents' not in st.session_state:
    st.session_state.file_contents = {}

if 'conversation_context' not in st.session_state:
    st.session_state.conversation_context = {
        'uploaded_files': [],
        'file_summaries': {},
        'last_query': None,
        'session_start': time.time()
    }

# 컨텍스트 정보 표시
if st.session_state.uploaded_files:
    st.markdown("### 🧠 세션 컨텍스트")
    with st.expander("📊 현재 상태", expanded=False):
        context = st.session_state.conversation_context
        st.info(f"⏰ 세션 시작: {time.strftime('%H:%M:%S', time.localtime(context['session_start']))}")
        st.info(f"📁 업로드된 파일: {len(st.session_state.uploaded_files)}개")
        st.info(f"💬 대화 수: {len(st.session_state.chat_history)}개")
        
        if context['last_query']:
            st.info(f"🔍 마지막 질문: {context['last_query'][:50]}...")
        
        # 컨텍스트 초기화 버튼
        if st.button("🔄 컨텍스트 초기화", type="secondary"):
            st.session_state.conversation_context = {
                'uploaded_files': [],
                'file_summaries': {},
                'last_query': None,
                'session_start': time.time()
            }
            st.session_state.chat_history = []
            st.success("✅ 컨텍스트가 초기화되었습니다!")
            st.rerun()

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
            
            # 파일 히스토리에 추가
            file_info = {
                'name': uploaded_file.name,
                'type': suffix.lower(),
                'size': len(uploaded_file.getvalue()),
                'upload_time': time.time(),
                'processed': True
            }
            st.session_state.uploaded_files.append(file_info)
            
            # 파일 내용 요약 저장 (텍스트 파일의 경우)
            if suffix.lower() in ['.txt', '.md']:
                try:
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 간단한 요약 생성 (첫 200자)
                        summary = content[:200] + "..." if len(content) > 200 else content
                        st.session_state.file_contents[uploaded_file.name] = {
                            'type': 'text',
                            'summary': summary,
                            'full_content': content
                        }
                except Exception as e:
                    st.warning(f"파일 내용 읽기 실패: {str(e)}")
            
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
    
    # 파일 히스토리 표시
    if st.session_state.uploaded_files:
        st.markdown("### 📚 업로드된 파일 히스토리")
        with st.expander("📋 파일 목록 및 요약", expanded=True):
            for i, file_info in enumerate(st.session_state.uploaded_files):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    file_icon = "📄" if file_info['type'] in ['.txt', '.md'] else "🖼️" if file_info['type'] in ['.jpg', '.jpeg', '.png', '.gif', '.bmp'] else "📕"
                    st.write(f"{file_icon} **{file_info['name']}**")
                
                with col2:
                    st.write(f"**타입**: {file_info['type']}")
                
                with col3:
                    size_kb = file_info['size'] / 1024
                    st.write(f"**크기**: {size_kb:.1f} KB")
                
                # 파일 내용 요약 표시 (텍스트 파일의 경우)
                if file_info['name'] in st.session_state.file_contents:
                    content_info = st.session_state.file_contents[file_info['name']]
                    if content_info['type'] == 'text':
                        st.text_area(
                            f"📝 {file_info['name']} 내용 요약",
                            content_info['summary'],
                            height=80,
                            key=f"summary_{i}",
                            disabled=True
                        )
                
                st.markdown("---")

# 세션 상태는 이미 위에서 초기화됨

# 질문 섹션
if st.session_state.get('documents_added', False):
    st.markdown("---")
    st.markdown("## 💬 채팅형 질문하기")
    
    # 채팅 히스토리 표시
    for message in st.session_state.chat_history:
                    if message['role'] == 'user':
                        with st.chat_message("user"):
                            st.write(message['content'])
                            
                            # 컨텍스트 정보 표시 (사용자 메시지)
                            if 'context' in message:
                                with st.expander("🔍 컨텍스트 정보", expanded=False):
                                    context = message['context']
                                    st.info(f"📁 업로드된 파일: {context['uploaded_files']}개")
                                    st.info(f"📄 파일 타입: {', '.join(context['file_types'])}")
                                    st.info(f"⏱️ 세션 시간: {context['session_duration']:.1f}초")
                    else:
                        with st.chat_message("assistant"):
                            # 오류 메시지인지 확인
                            if message.get('error', False):
                                st.error("❌ 오류 발생")
                                st.write(message['content'])
                                
                                # 오류 상세 정보 표시
                                if 'error_details' in message:
                                    with st.expander("🔍 오류 상세 정보", expanded=False):
                                        st.code(message['error_details'])
                                        
                                        # 오류 해결 방법 제안
                                        st.markdown("**💡 해결 방법:**")
                                        st.markdown("• OpenAI API 키 확인")
                                        st.markdown("• 인터넷 연결 상태 확인")
                                        st.markdown("• API 사용량 한도 확인")
                                        st.markdown("• 잠시 후 다시 시도")
                            else:
                                st.write(message['content'])
                                
                                # 메타 정보가 있으면 표시
                                if 'confidence' in message:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("🎯 신뢰도", f"{message['confidence']:.1%}")
                                    with col2:
                                        st.metric("📚 참조 소스", message.get('source_count', 0))
                                
                                # 컨텍스트 사용 정보 표시
                                if 'context_used' in message:
                                    context_used = message['context_used']
                                    st.success(f"✅ 컨텍스트 인식: {context_used['files_referenced']}개 파일 참조됨")
                                
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
    # st.markdown("**💡 예시 질문:**")
    # col1, col2, col3 = st.columns(3)
    
    # with col1:
    #     if st.button("📊 문서 요약", key="summary_btn"):
    #         st.session_state.example_query = "업로드된 모든 문서의 주요 내용을 요약해주세요."
    
    # with col2:
    #     if st.button("🖼️ 이미지 설명", key="image_btn"):
    #         st.session_state.example_query = "이미지에서 발견되는 중요한 정보를 설명해주세요."
    
    # with col3:
    #     if st.button("🔍 상세 분석", key="analysis_btn"):
    #         st.session_state.example_query = "문서와 이미지를 종합하여 상세히 분석해주세요."
    
    # 새로운 질문 입력 (채팅 형태)
    if prompt := st.chat_input("질문을 입력하세요..."):
        # 컨텍스트 정보 업데이트
        st.session_state.conversation_context['last_query'] = prompt
        
        # 사용자 질문을 채팅 히스토리에 추가
        user_message = {
            'role': 'user',
            'content': prompt,
            'timestamp': len(st.session_state.chat_history),
            'context': {
                'uploaded_files': len(st.session_state.uploaded_files),
                'file_types': [f['type'] for f in st.session_state.uploaded_files],
                'session_duration': time.time() - st.session_state.conversation_context['session_start']
            }
        }
        st.session_state.chat_history.append(user_message)
        
        # 답변 생성
        with st.spinner("답변 생성 중..."):
            try:
                # 컨텍스트가 포함된 질문 생성
                context_prompt = f"""
                컨텍스트 정보:
                - 업로드된 파일 수: {len(st.session_state.uploaded_files)}
                - 파일 타입: {', '.join([f['type'] for f in st.session_state.uploaded_files])}
                - 이전 대화 수: {len(st.session_state.chat_history) - 1}
                
                사용자 질문: {prompt}
                
                위의 컨텍스트를 고려하여 답변해주세요. 업로드된 파일들이 있다면 그 내용을 참고하여 답변하세요.
                """
                
                # OpenAI 사용 시 타임아웃 및 재시도 로직
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        result = st.session_state.rag_system.search(context_prompt)
                        break  # 성공 시 루프 탈출
                    except Exception as retry_error:
                        retry_count += 1
                        if retry_count >= max_retries:
                            # 최대 재시도 횟수 초과
                            error_msg = f"❌ OpenAI API 호출 실패 (재시도 {max_retries}회): {str(retry_error)}"
                            st.error(error_msg)
                            
                            # 오류 정보를 채팅 히스토리에 추가
                            error_message = {
                                'role': 'assistant',
                                'content': error_msg,
                                'timestamp': len(st.session_state.chat_history),
                                'error': True,
                                'error_details': str(retry_error)
                            }
                            st.session_state.chat_history.append(error_message)
                            st.rerun()
                            break  # while 루프 탈출
                        else:
                            # 재시도 안내
                            st.warning(f"⚠️ API 호출 실패, {retry_count}/{max_retries} 재시도 중...")
                            time.sleep(2)  # 2초 대기 후 재시도
                
                # AI 답변을 채팅 히스토리에 추가
                assistant_message = {
                    'role': 'assistant',
                    'content': result.answer,
                    'confidence': result.confidence,
                    'source_count': len(result.sources),
                    'sources': result.sources,
                    'timestamp': len(st.session_state.chat_history),
                    'context_used': {
                        'files_referenced': len(result.sources),
                        'query_understood': True
                    }
                }
                st.session_state.chat_history.append(assistant_message)
                
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
        if llm_provider == "ollama":
            st.markdown("""
            **🤖 기능:**
            • 텍스트 문서 검색
            • 이미지 내용 분석 (LLaVA 모델 필요)
            • 멀티모달 통합 검색
            """)
        else:
            st.markdown("""
            **🤖 기능:**
            • 텍스트 문서 검색
            • 이미지 내용 분석 (GPT-4o Vision)
            • 멀티모달 통합 검색
            """)

# 하단 정보는 사이드바로 이동됨