# STT 프로젝트 백엔드

음성 인식 및 텍스트 처리를 위한 백엔드 서비스입니다.

## 주요 기능

- 음성 파일을 텍스트로 변환 (STT)
- 텍스트 정리 및 구조화
- 해시태그 추출
- LangGraph 기반 워크플로우 처리

## 설치 및 설정

### 로컬 개발 환경

```bash
# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 필요한 API 키 설정

# 개발 서버 실행
uv run streamlit run streamlit_app.py
```

### Streamlit Cloud 배포

#### ffmpeg 설치 문제 해결

Streamlit Cloud에서 STT 기능을 사용하려면 ffmpeg가 필요합니다. 다음 방법으로 해결할 수 있습니다:

1. **packages.txt 파일** (이미 설정됨):
   ```
   ffmpeg
   libavcodec-extra
   libavformat-dev
   libavutil-dev
   libswscale-dev
   libswresample-dev
   ```

2. **자동 설치 스크립트**: 앱 시작 시 `install_ffmpeg.py`가 자동으로 실행되어 ffmpeg를 설치합니다.

3. **Fallback 모드**: ffmpeg 설치에 실패하더라도 librosa를 사용한 fallback 모드로 동작합니다.

#### 환경 변수 설정

Streamlit Cloud Secrets에서 다음 환경 변수를 설정하세요:

```toml
[secrets]
LLM_PROVIDER = "openai"  # 또는 "ollama"
OPENAI_API_KEY = "your-openai-api-key"
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama 사용 시
```

## 기술 스택

- **STT**: OpenAI Whisper
- **LLM**: OpenAI GPT / Ollama (gemma2:9b)
- **워크플로우**: LangGraph
- **웹 프레임워크**: Streamlit
- **오디오 처리**: librosa, ffmpeg

## 문제 해결

### ffmpeg 관련 오류

```
[Errno 2] No such file or directory: 'ffmpeg'
```

이 오류가 발생하면:

1. `packages.txt`에 ffmpeg가 포함되어 있는지 확인
2. Streamlit Cloud 앱을 재배포
3. 로그에서 ffmpeg 설치 상태 확인

### STT 처리 실패

STT 처리가 실패하면 자동으로 librosa fallback 모드로 전환됩니다. 이 경우:

- 오디오 파일 형식이 지원되는지 확인
- 파일 크기가 적절한지 확인 (너무 큰 파일은 처리 시간이 오래 걸림)

## 개발

### 프로젝트 구조

```
src/
├── chains/          # LLM 체인들
├── core/            # 핵심 로직 (워크플로우, 설정)
├── interfaces/      # 웹 인터페이스
├── processors/      # 데이터 처리기
└── services/        # 비즈니스 로직
```

### 테스트

```bash
# 테스트 실행
uv run python -m pytest tests/
```

## 라이선스

MIT License
