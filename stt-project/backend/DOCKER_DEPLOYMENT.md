# 🐳 Docker를 이용한 STT 프로젝트 배포 가이드

## 📋 개요

이 프로젝트는 음성을 텍스트로 변환하고 스토리를 정리하는 Streamlit 애플리케이션입니다.
ffmpeg 의존성 문제를 해결하기 위해 Docker를 사용합니다.

## 🚀 빠른 시작

### 1. 필수 조건
- Docker 설치됨
- Docker Compose 설치됨

### 2. 환경 설정
```bash
# .env 파일이 올바르게 설정되어 있는지 확인
cp .env.example .env  # 필요한 경우
```

### 3. 애플리케이션 실행

#### 방법 1: 스크립트 사용 (권장)
```bash
./docker-build.sh
```

#### 방법 2: 직접 명령어 사용
```bash
# 이미지 빌드
docker build -t stt-streamlit-app .

# 실행
docker-compose up -d
```

#### 방법 3: Streamlit 전용 실행
```bash
docker-compose -f streamlit-docker-compose.yml up -d
```

### 4. 접속
- **Streamlit 앱**: http://localhost:8501
- **FastAPI 문서** (활성화된 경우): http://localhost:8000/docs

## 📁 생성된 파일들

### Docker 관련 파일
- `Dockerfile` - 기본 Docker 이미지 정의
- `Dockerfile.optimized` - 최적화된 멀티스테이지 빌드
- `docker-compose.yml` - 전체 서비스 구성
- `streamlit-docker-compose.yml` - Streamlit 전용 구성
- `.dockerignore` - Docker 빌드에서 제외할 파일들
- `requirements.txt` - Python 의존성 목록

### 실행 스크립트
- `docker-build.sh` - 빌드 및 실행 자동화 스크립트

## 🔧 주요 특징

### ffmpeg 포함
- Ubuntu 기반 이미지에 ffmpeg와 관련 라이브러리 사전 설치
- 음성 파일 처리를 위한 모든 의존성 포함

### 한글 파일명 지원 ⭐
- 한국어 로케일 (ko_KR.UTF-8) 설정
- Unicode NFC 정규화를 통한 안전한 파일명 처리
- 한글 파일명이 깨지지 않고 정상적으로 처리됨

### 환경 설정
- `.env` 파일을 통한 환경 변수 관리
- Streamlit 최적화 설정 포함

### 볼륨 마운트
- `./temp`: 임시 파일 저장
- `./models`: 모델 파일 저장
- `./.env`: 환경 변수 파일 (읽기 전용)

## 🛠️ 유용한 명령어

### 로그 확인
```bash
docker-compose logs -f
```

### 컨테이너 상태 확인
```bash
docker-compose ps
```

### 애플리케이션 중지
```bash
docker-compose down
```

### 애플리케이션 재시작
```bash
docker-compose restart
```

### 이미지 재빌드
```bash
docker-compose build --no-cache
```

### 한글 파일명 테스트
```bash
# Docker 컨테이너 내부에서 한글 파일명 처리 테스트
docker-compose exec stt-app python test_korean_filename.py
```

## 🎯 배포 옵션

### 로컬 개발
기본 `docker-compose.yml` 사용

### 프로덕션 배포
1. 최적화된 Dockerfile 사용:
   ```bash
   docker build -f Dockerfile.optimized -t stt-app-optimized .
   ```

2. 리소스 제한 적용:
   `streamlit-docker-compose.yml` 사용

### 클라우드 배포
- AWS ECS, GCP Cloud Run, Azure Container Instances 등에서 사용 가능
- `Dockerfile`을 기반으로 컨테이너 레지스트리에 푸시

## 🔍 트러블슈팅

### ffmpeg 관련 오류
Docker 컨테이너 내부에서 ffmpeg가 자동으로 설치되므로 로컬 설치 불필요

### 한글 파일명 깨짐 해결 ⭐
**문제**: 한글 파일명이 깨져서 보이거나 처리되지 않음

**해결방법**:
1. **로케일 설정 확인**:
   ```bash
   # 컨테이너 내부에서 로케일 확인
   docker-compose exec stt-app locale
   ```

2. **환경 변수 확인**:
   ```bash
   # 환경 변수가 올바르게 설정되었는지 확인
   docker-compose exec stt-app printenv | grep -E "(LANG|LC_)"
   ```

3. **파일명 테스트**:
   ```bash
   # 한글 파일명 처리 테스트 실행
   docker-compose exec stt-app python test_korean_filename.py
   ```

**추가 해결방법**:
- Docker를 완전히 재빌드: `docker-compose build --no-cache`
- 시스템 로케일 확인: 호스트 시스템에서도 UTF-8 지원 확인

### 메모리 부족
`streamlit-docker-compose.yml`의 메모리 제한을 조정:
```yaml
deploy:
  resources:
    limits:
      memory: 4G  # 필요에 따라 증가
```

### 포트 충돌
다른 포트 사용:
```yaml
ports:
  - "8502:8501"  # 다른 포트로 변경
```

## 📊 성능 최적화

### 이미지 크기 최적화
`Dockerfile.optimized` 사용하여 멀티스테이지 빌드 적용

### 캐시 최적화
- requirements.txt를 먼저 복사하여 의존성 캐싱 최적화
- .dockerignore로 불필요한 파일 제외

### 리소스 제한
`streamlit-docker-compose.yml`에서 CPU/메모리 제한 설정

## 🔐 보안 고려사항

- 비root 사용자로 컨테이너 실행 (Dockerfile.optimized)
- .env 파일을 읽기 전용으로 마운트
- 불필요한 포트 노출 방지