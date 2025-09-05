#!/bin/bash

# Docker 빌드 및 실행 스크립트
# 한글 파일명 지원을 위한 로케일 설정 포함

# UTF-8 로케일 설정
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8

echo "🐳 STT Streamlit App Docker 빌드 시작..."
echo "🌏 로케일 설정: $LANG"

# Docker 이미지 빌드
echo "📦 Docker 이미지 빌드 중..."
docker build -t stt-streamlit-app .

if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 완료!"
    
    # 기존 컨테이너 정리 (실행 중인 경우)
    echo "🧹 기존 컨테이너 정리 중..."
    docker-compose down 2>/dev/null || true
    
    # Docker Compose로 실행
    echo "🚀 Docker Compose로 애플리케이션 실행 중..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo "✅ 애플리케이션이 성공적으로 시작되었습니다!"
        echo "🌐 Streamlit 앱: http://localhost:8501"
        echo "🔧 FastAPI 문서: http://localhost:8000/docs (활성화된 경우)"
        echo ""
        echo "📋 유용한 명령어:"
        echo "  - 로그 확인: docker-compose logs -f"
        echo "  - 중지: docker-compose down"
        echo "  - 재시작: docker-compose restart"
        echo "  - 컨테이너 상태: docker-compose ps"
    else
        echo "❌ 애플리케이션 시작 실패"
        exit 1
    fi
else
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi