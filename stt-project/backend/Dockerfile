# Python 3.11 기반 이미지 사용
FROM python:3.11-slim

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    # 한글 지원을 위한 로케일 패키지
    locales \
    locales-all \
    # ffmpeg 및 관련 라이브러리 설치
    ffmpeg \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    # 빌드 도구들
    build-essential \
    git \
    wget \
    curl \
    # 오디오 처리를 위한 추가 패키지
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    # 정리
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 한글 로케일 설정
RUN locale-gen ko_KR.UTF-8
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LC_ALL=ko_KR.UTF-8

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치 (캐시 최적화를 위해 먼저 실행)
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p temp models

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 포트 노출
EXPOSE 8501
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health

# Streamlit 앱 실행 (기본값)
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]