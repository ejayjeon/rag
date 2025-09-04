# Streamlit Cloud 배포 가이드

## 🚀 배포 전 체크리스트

### 1. 필수 파일 확인
- ✅ `packages.txt` - ffmpeg 시스템 의존성
- ✅ `pyproject.toml` - uv 기반 Python 의존성  
- ✅ `streamlit_app.py` - 루트 디렉토리에 위치
- ✅ `.streamlit/config.toml` - Streamlit 설정
- ✅ `.env.example` - 환경 변수 참고용

### 2. Streamlit Cloud 설정

#### Secrets 관리에서 환경 변수 설정:
```toml
LLM_PROVIDER = "openai"
OPENAI_API_KEY = "sk-your-actual-api-key-here"
OPENAI_MODEL = "gpt-3.5-turbo"
WHISPER_MODEL = "base"
WHISPER_LANGUAGE = "ko"
MAX_AUDIO_SIZE_MB = "50"
SESSION_TIMEOUT_MINUTES = "30"
```

## 🔧 배포 후 문제 해결

### 1. STT 오류: ffmpeg 의존성
**오류**: `[Errno 2] No such file or directory: 'ffmpeg'`

**다중 해결 방안**:
1. **시스템 패키지**: `packages.txt`에 `ffmpeg` 추가 (Streamlit Cloud 표준)
2. **Python 패키지**: `pyproject.toml`에 `ffmpeg-python`, `librosa`, `soundfile` 추가
3. **자동 fallback**: ffmpeg 실패 시 librosa 자동 사용

**현재 구현된 fallback 순서**:
1. Whisper + ffmpeg (가장 빠름)
2. Whisper + librosa (ffmpeg 없어도 동작)
3. 실패 시 상세 오류 메시지

### 2. LLM 연결 오류: 네트워크 문제
**오류**: `[Errno 99] Cannot assign requested address`
**원인**: OpenAI API 키 미설정 또는 잘못된 설정
**해결**: 
1. Streamlit Cloud Secrets에서 `OPENAI_API_KEY` 확인
2. 앱 내 디버그 정보에서 환경 변수 상태 확인

### 3. JSON 파싱 오류: 구조화 체인
**오류**: `cannot access local variable 'json'`
**해결**: import 문 위치 수정 완료

## 🎯 배포 확인 방법

1. **환경 변수 확인**: 앱 내 "배포 디버그 정보" 섹션 확인
2. **LLM 연결 상태**: 환경 변수 상태에서 LLM_Status 확인
3. **파일 업로드 테스트**: 작은 음성 파일로 전체 파이프라인 테스트

## 📋 배포 설정 요약

### 프로젝트 구조
```
backend/
├── streamlit_app.py          # 메인 앱 (루트에 위치)
├── packages.txt              # 시스템 패키지 (ffmpeg)
├── pyproject.toml            # uv 기반 Python 의존성
├── .streamlit/
│   └── config.toml           # Streamlit 설정
├── .env.example              # 환경 변수 예제
└── src/                      # 소스 코드
    ├── core/
    ├── chains/
    ├── processors/
    └── services/
```

### 환경 변수 우선순위
1. **Streamlit Cloud**: OpenAI API 사용 (권장)
2. **로컬 개발**: Ollama 사용
3. **자체 호스팅**: 커스텀 Ollama 서버

## 🚨 주의사항

- OpenAI API 키는 반드시 Streamlit Cloud Secrets에만 저장
- `.env` 파일을 git에 커밋하지 않도록 주의
- 대용량 음성 파일(50MB 초과) 업로드 시 처리 시간 증가 가능