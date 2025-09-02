# 🤖 Simple RAG System

PDF 문서를 업로드하고 AI가 문서 내용을 기반으로 질문에 답변하는 RAG(Retrieval-Augmented Generation) 시스템입니다.

## 📋 프로젝트 개요

이 프로젝트는 다음과 같은 기능을 제공합니다:

- **문서 업로드**: PDF, TXT 파일을 업로드하여 분석
- **벡터 검색**: 문서를 청크 단위로 분할하고 임베딩하여 벡터 데이터베이스 생성
- **AI 질문 답변**: 업로드된 문서를 기반으로 질문에 대한 정확한 답변 제공
- **채팅 인터페이스**: 지속적인 대화형 질문-답변 지원
- **참조 문서 표시**: 답변의 근거가 되는 원본 문서 내용 확인 가능

### 기술 스택

- **Frontend**: Streamlit
- **LLM**: Ollama (Local) / OpenAI (Cloud)
- **Vector Store**: Chroma DB
- **Embeddings**: HuggingFace sentence-transformers
- **Document Processing**: LangChain

## 🚀 로컬 환경 설치 및 실행

### 1. 사전 준비사항

Python 3.8+ 설치 필요

### 2. 프로젝트 클론

```bash
git clone <repository-url>
cd simple-rag
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. Ollama 설치 및 설정 (로컬 LLM 사용 시)

#### macOS/Linux:
```bash
# Ollama 설치
curl -fsSL https://ollama.com/install.sh | sh

# Ollama 서버 시작
ollama serve

# 새 터미널에서 Llama2 모델 다운로드
ollama pull llama2
```

#### Windows:
1. https://ollama.com/download 에서 Windows용 설치 파일 다운로드
2. 설치 후 명령 프롬프트에서 실행:
```cmd
ollama serve
# 새 명령 프롬프트에서
ollama pull llama2
```

### 5. 애플리케이션 실행

```bash
# Streamlit 앱 실행
streamlit run src/streamlit_app.py
```

브라우저에서 `http://localhost:8501`로 접속

### 6. 사용법

1. **모델 선택**: 사이드바에서 `ollama` 또는 `openai` 선택
2. **문서 업로드**: 
   - `documents/sample.pdf` 사용하기 체크박스 선택, 또는
   - PDF/TXT 파일 업로드
3. **질문하기**: 채팅 입력창에 질문 입력
4. **답변 확인**: AI 답변 및 참조 문서 내용 확인

## 📁 프로젝트 구조

```
simple-rag/
├── src/
│   ├── streamlit_app.py    # 향상된 Streamlit 앱 (권장)
│   └── rag_system.py       # RAG 시스템 코어 로직
├── documents/
│   └── sample.pdf          # 샘플 PDF 파일
├── requirements.txt        # Python 의존성
└── README.md              # 프로젝트 문서
```

## 시스템 작동 원리 


## 🧠 시스템 동작 원리 Deep Dive

### 1. 문서 전처리 파이프 라인

```
PDF 파일 -> PyPDFLoader -> 텍스트 추출
-> RecursiveCharacterTextSplitter
-> 1000자 청크
```

핵심 메커니즘
- 청킹 전략: 1000자 + 200자 오버랩으로 문맥 보존
- 계층적 분할: 문단 -> 문장 -> 단어 순으로 자연스럽게 분할
- 메타데이터 보존: 페이지 번호, 소스 파일 경로 등 유지


### 2. 임베딩 및 벡터화 과정

```
텍스트 청크 → SentenceTransformer → 384차원 벡터 → ChromaDB 저장
```

all-MiniLM-L6-v2 모델의 특징:
- 크기: 22MB (가벼움)
- 차원: 384차원 벡터
- 언어: 다국어 지원 (한국어 포함)
- 성능: 빠른 인코딩 속도, 적당한 정확도



### 3. 검색 및 생성 과정

```
질문 → 임베딩 → 유사도 검색 (Top-3) → 컨텍스트 조합 → Llama2 → 답변
```

검색 알고리즘:
- 유사도 측정: 코사인 유사도
- Top-K 선택: 상위 3개 가장 유사한 청크
- 임계값: 자동으로 관련성 필터링



### 배포 시 중요 사항

⚠️ **주의**: Netlify는 정적 사이트 호스팅 서비스로, Streamlit과 같은 Python 웹 애플리케이션을 **직접 배포할 수 없습니다**.

### 대안 배포 방법

#### 1. Streamlit Cloud (권장)

**장점**: Streamlit 전용 호스팅, 무료, 간편한 배포

```bash
# 1. GitHub에 코드 푸시
git add .
git commit -m "Initial commit"
git push origin main

# 2. https://share.streamlit.io/ 접속
# 3. GitHub 레포지토리 연결
# 4. 자동 배포 완료
```

**배포 후 사용법**:
- 배포된 앱에서는 **OpenAI API 사용 권장** (Ollama는 로컬 전용)
- OpenAI API 키를 Streamlit Cloud Secrets에 추가:
  ```toml
  # .streamlit/secrets.toml
  OPENAI_API_KEY = "your-api-key-here"
  ```

#### 2. Heroku

```bash
# Procfile 생성
echo "web: streamlit run src/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile

# Heroku 앱 생성 및 배포
heroku create your-app-name
git push heroku main
```

#### 3. Railway

```bash
# railway 설치
npm install -g @railway/cli

# 배포
railway login
railway init
railway up
```

### 배포 환경에서의 설정

#### OpenAI API 사용 (권장)

1. **API 키 발급**: https://platform.openai.com/api-keys
2. **환경 변수 설정**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
3. **코드 수정**: `src/rag_system.py`에서 OpenAI 설정 추가

#### Ollama 대신 OpenAI 사용하도록 수정

배포 환경에서는 Ollama 서버를 실행할 수 없으므로, OpenAI API를 사용해야 합니다:

```python
# src/rag_system.py 수정 예시
if model_type == "openai":
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
```

## 🔧 환경 변수

로컬 개발 시 `.env` 파일 생성:

```bash
# .env
OPENAI_API_KEY=your-openai-api-key-here
```

## 🐛 문제 해결

### Ollama 연결 오류
```bash
# Ollama 서버 상태 확인
curl http://localhost:11434

# Ollama 재시작
ollama serve
```

### 메모리 부족 오류
- 더 작은 문서로 테스트
- chunk_size를 줄여서 시도 (기본값: 1000 → 500)

### 패키지 설치 오류
```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

## 📝 라이선스

MIT License

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시 (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📞 지원

문제가 있으시면 Issues 탭에서 문의해주세요.