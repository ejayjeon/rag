# 🚀 Streamlit Community Cloud 배포 가이드

## 📋 개요

Streamlit Community Cloud에 STT 프로젝트를 배포하는 완전한 가이드입니다.
**중요**: Streamlit Cloud는 Docker를 직접 지원하지 않지만, `packages.txt`를 통해 시스템 패키지(ffmpeg 등)를 설치할 수 있습니다.

## 🎯 배포 방법

### 1. GitHub 저장소 준비

**필수 파일들 확인:**
- ✅ `streamlit_app.py` - 메인 앱 파일
- ✅ `requirements.txt` - Python 패키지
- ✅ `packages.txt` - 시스템 패키지 (ffmpeg 포함)
- ✅ `.env` - 환경 변수 (배포 시 별도 설정)

**저장소 구조:**
```
stt-project/backend/
├── streamlit_app.py        # 메인 앱 (루트에 있어야 함)
├── requirements.txt        # Python 의존성
├── packages.txt           # 시스템 패키지 (ffmpeg, 한글지원)
├── src/                   # 소스 코드
├── temp/                  # 임시 파일 (자동 생성)
├── models/                # 모델 파일
└── .streamlit/           # Streamlit 설정
```

### 2. Streamlit Community Cloud 배포

#### 2-1. 웹사이트 접속
1. **Streamlit Community Cloud** 방문: https://share.streamlit.io/
2. **GitHub 계정으로 로그인**

#### 2-2. 새 앱 배포
1. **"Deploy an app" 버튼 클릭**
2. **저장소 정보 입력:**
   ```
   Repository: your-github-username/stt-project
   Branch: main (또는 배포할 브랜치)
   Main file path: backend/streamlit_app.py
   ```
3. **"Deploy!" 버튼 클릭**

#### 2-3. 환경 변수 설정 (중요!)
배포 후 **"⚙️ Settings" → "Secrets"**에서 환경 변수 설정:

```toml
# .streamlit/secrets.toml 형식으로 입력
[secrets]
OPENAI_API_KEY = "your-openai-api-key"
ANTHROPIC_API_KEY = "your-anthropic-api-key"
OLLAMA_BASE_URL = "your-ollama-url"  # 필요시

# 한글 지원 환경 변수
LANG = "ko_KR.UTF-8"
LC_ALL = "ko_KR.UTF-8"
PYTHONIOENCODING = "utf-8"
```

### 3. 자동 배포 설정

#### 3-1. GitHub Actions (선택사항)
`.github/workflows/streamlit-deploy.yml`:

```yaml
name: Streamlit App Deploy

on:
  push:
    branches: [ main ]
    paths: [ 'backend/**' ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Streamlit Redeploy
        run: |
          echo "Streamlit will auto-deploy from GitHub"
```

## 🔧 배포 최적화

### 성능 최적화

**1. requirements.txt 최적화:**
```txt
# 필수 패키지만 포함, 버전 고정
streamlit==1.49.1
fastapi==0.116.1
ffmpeg-python
openai-whisper
# ... 나머지 필수 패키지들
```

**2. 캐싱 활용:**
```python
@st.cache_resource
def load_model():
    # 모델 로딩을 캐시
    pass

@st.cache_data
def process_audio(audio_data):
    # 데이터 처리 캐시
    pass
```

### 메모리 최적화

**1. 대용량 파일 처리:**
```python
# streamlit_app.py에 추가
st.set_page_config(
    page_title="STT App",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 파일 크기 제한
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB (Streamlit 제한)
```

**2. 임시 파일 정리:**
```python
import atexit
import tempfile
import shutil

def cleanup_temp_files():
    """앱 종료 시 임시 파일 정리"""
    temp_dir = Path("temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)

atexit.register(cleanup_temp_files)
```

## 🐛 일반적인 문제 해결

### ffmpeg 관련 오류

**문제**: `ffmpeg not found` 오류

**해결방법**:
1. `packages.txt` 파일이 올바른 위치에 있는지 확인
2. 파일 내용 확인:
   ```
   ffmpeg
   libavcodec-extra
   libavformat-dev
   libavutil-dev
   libswscale-dev
   libswresample-dev
   ```
3. 앱 재배포 (때로는 시간이 걸림)

### 한글 파일명 문제

**문제**: 한글 파일명이 깨짐

**해결방법**:
1. `packages.txt`에 로케일 패키지 추가됨: ✅
   ```
   locales
   locales-all
   ```
2. Secrets에 환경 변수 설정: ✅
   ```toml
   LANG = "ko_KR.UTF-8"
   LC_ALL = "ko_KR.UTF-8" 
   PYTHONIOENCODING = "utf-8"
   ```

### 메모리 부족 오류

**문제**: `MemoryError` 또는 앱 크래시

**해결방법**:
1. **파일 크기 제한**:
   ```python
   if uploaded_file.size > MAX_FILE_SIZE:
       st.error(f"파일이 너무 큽니다. 최대 {MAX_FILE_SIZE//1024//1024}MB")
   ```

2. **스트리밍 처리**:
   ```python
   # 대용량 파일을 청크 단위로 처리
   chunk_size = 1024 * 1024  # 1MB 청크
   ```

### API 키 오류

**문제**: OpenAI/Anthropic API 키 관련 오류

**해결방법**:
1. Streamlit Secrets에 API 키가 올바르게 설정되었는지 확인
2. 코드에서 secrets 접근:
   ```python
   import streamlit as st
   api_key = st.secrets["OPENAI_API_KEY"]
   ```

## 🔄 업데이트 및 관리

### 자동 재배포
- GitHub에 코드 푸시 시 Streamlit이 자동으로 재배포
- 보통 2-5분 소요

### 수동 재배포
1. Streamlit 대시보드에서 앱 선택
2. **"⋮" 메뉴 → "Reboot app"**

### 로그 확인
1. Streamlit 대시보드에서 앱 선택  
2. **"⋮" 메뉴 → "View logs"**

## 📊 모니터링

### 사용량 확인
- Streamlit Community Cloud 대시보드에서 확인
- 무료 계정: 월 1GB 대역폭, 3개 앱 제한

### 성능 모니터링
```python
import time
import streamlit as st

# 처리 시간 측정
start_time = time.time()
# ... 처리 로직 ...
processing_time = time.time() - start_time
st.info(f"처리 시간: {processing_time:.2f}초")
```

## 🎉 배포 완료 체크리스트

- [ ] GitHub 저장소에 코드 업로드
- [ ] `streamlit_app.py`가 올바른 경로에 위치
- [ ] `requirements.txt`와 `packages.txt` 확인
- [ ] Streamlit Community Cloud에서 앱 배포
- [ ] 환경 변수(Secrets) 설정
- [ ] 앱이 정상적으로 작동하는지 테스트
- [ ] 한글 파일명 업로드 테스트
- [ ] ffmpeg 기능 작동 확인

## 🔗 유용한 링크

- **Streamlit Community Cloud**: https://share.streamlit.io/
- **배포 문서**: https://docs.streamlit.io/deploy/streamlit-community-cloud
- **패키지 설치 가이드**: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- **환경 변수 설정**: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management