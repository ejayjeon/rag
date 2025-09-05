#!/bin/bash
# deploy.sh - Git 푸시 및 Streamlit Cloud 자동 배포 스크립트

set -e  # 에러 발생시 즉시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 메시지 출력
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 함수: 명령 실행 확인
confirm() {
    read -p "❓ $1 (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "작업이 취소되었습니다."
        exit 1
    fi
}

# 헤더 출력
echo "================================================"
echo "🚀 Streamlit Cloud 자동 배포 스크립트"
echo "================================================"
echo

# 1. Git 상태 확인
log_info "Git 저장소 상태 확인 중..."

if [ ! -d .git ]; then
    log_error "Git 저장소가 아닙니다. 먼저 'git init'을 실행하세요."
    exit 1
fi

# 현재 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)
log_info "현재 브랜치: $CURRENT_BRANCH"

# 변경사항 확인
if [ -z "$(git status --porcelain)" ]; then
    log_warning "커밋할 변경사항이 없습니다."
    exit 0
fi

echo
log_info "변경된 파일:"
git status --short
echo

# 2. 환경 검증
log_info "배포 환경 검증 중..."

# 필수 파일 확인
MISSING_FILES=()

if [ ! -f "pyproject.toml" ]; then
    MISSING_FILES+=("pyproject.toml")
fi

if [ ! -f "streamlit_app.py" ]; then
    MISSING_FILES+=("streamlit_app.py")
fi

if [ ! -f "packages.txt" ]; then
    log_warning "packages.txt가 없습니다. 생성 중..."
    cat > packages.txt << 'EOF'
ffmpeg
libsndfile1
build-essential
python3-dev
git
EOF
    log_success "packages.txt 생성 완료"
fi

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    log_error "필수 파일이 없습니다: ${MISSING_FILES[*]}"
    exit 1
fi

# 3. requirements.txt 생성/업데이트
log_info "requirements.txt 생성 중..."

# uv 설치 확인
if ! command -v uv &> /dev/null; then
    log_error "uv가 설치되지 않았습니다."
    echo "설치: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# requirements.txt 생성
log_info "uv를 사용하여 requirements.txt 생성 중..."

# 임시 파일 생성
uv pip compile pyproject.toml --no-deps > requirements_temp.txt 2>/dev/null || {
    log_error "requirements.txt 생성 실패"
    exit 1
}

# Streamlit Cloud용 최적화
cat > requirements.txt << 'EOF'
# Auto-generated from pyproject.toml for Streamlit Cloud
# Generated at: $(date)

# Torch CPU version for Streamlit Cloud
--find-links https://download.pytorch.org/whl/torch_stable.html
torch==2.1.0+cpu

EOF

# torch를 제외한 나머지 의존성 추가
grep -v "torch" requirements_temp.txt >> requirements.txt
rm requirements_temp.txt

log_success "requirements.txt 생성 완료"

# 4. .streamlit/config.toml 확인
if [ ! -f ".streamlit/config.toml" ]; then
    log_info ".streamlit/config.toml 생성 중..."
    mkdir -p .streamlit
    cat > .streamlit/config.toml << 'EOF'
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 50
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
EOF
    log_success ".streamlit/config.toml 생성 완료"
fi

# 5. .gitignore 확인
if [ ! -f ".gitignore" ]; then
    log_info ".gitignore 생성 중..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Environment
.env
.env.local
.streamlit/secrets.toml

# IDE
.vscode/
.idea/
.DS_Store

# Data
data/
*.mp3
*.wav
*.m4a

# Logs
*.log
logs/

# UV
.uv/

# Temp
temp/
tmp/
EOF
    log_success ".gitignore 생성 완료"
fi

# 6. 커밋 메시지 입력
echo
DEFAULT_MESSAGE="Update for Streamlit Cloud deployment"
read -p "💬 커밋 메시지 (기본값: $DEFAULT_MESSAGE): " COMMIT_MESSAGE
COMMIT_MESSAGE=${COMMIT_MESSAGE:-$DEFAULT_MESSAGE}

# 7. Git 작업 수행
log_info "Git 작업 수행 중..."

# 모든 파일 스테이징
git add .

# 커밋
git commit -m "$COMMIT_MESSAGE" || {
    log_error "커밋 실패"
    exit 1
}

log_success "커밋 완료"

# 8. 원격 저장소 확인
log_info "원격 저장소 확인 중..."

REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

if [ -z "$REMOTE_URL" ]; then
    log_warning "원격 저장소가 설정되지 않았습니다."
    echo
    echo "GitHub 저장소 URL을 입력하세요:"
    echo "예: https://github.com/username/repository.git"
    read -p "URL: " GITHUB_URL
    
    if [ -n "$GITHUB_URL" ]; then
        git remote add origin "$GITHUB_URL"
        log_success "원격 저장소 추가 완료"
    else
        log_error "원격 저장소 URL이 필요합니다."
        exit 1
    fi
else
    log_info "원격 저장소: $REMOTE_URL"
fi

# 9. Push 확인
echo
confirm "GitHub에 푸시하시겠습니까?"

# Push 수행
log_info "GitHub에 푸시 중..."

git push -u origin "$CURRENT_BRANCH" || {
    log_error "푸시 실패. GitHub 인증을 확인하세요."
    exit 1
}

log_success "GitHub 푸시 완료!"

# 10. Streamlit Cloud 배포 정보
echo
echo "================================================"
echo "📌 Streamlit Cloud 배포 단계"
echo "================================================"
echo

# GitHub URL에서 사용자명과 저장소명 추출
if [[ $REMOTE_URL =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    GITHUB_USER="${BASH_REMATCH[1]}"
    GITHUB_REPO="${BASH_REMATCH[2]}"
    
    log_success "GitHub 정보 감지됨"
    echo "  👤 사용자: $GITHUB_USER"
    echo "  📁 저장소: $GITHUB_REPO"
    echo "  🌿 브랜치: $CURRENT_BRANCH"
    echo
fi

# Streamlit Cloud URL 생성
STREAMLIT_URL="https://share.streamlit.io/deploy"

cat << EOF
📋 다음 단계를 따라 배포를 완료하세요:

1. Streamlit Cloud 접속
   🔗 $STREAMLIT_URL

2. GitHub 로그인 (첫 사용시)

3. 새 앱 생성 (New app)
   - Repository: $GITHUB_USER/$GITHUB_REPO
   - Branch: $CURRENT_BRANCH
   - Main file path: streamlit_app.py

4. Secrets 설정 (매우 중요!)
   앱 설정 → Secrets 탭에서 다음 추가:
   
   OPENAI_API_KEY = "sk-..."
   WHISPER_MODEL_SIZE = "tiny"
   MAX_FILE_SIZE_MB = "50"

5. Deploy 클릭!

EOF

# 11. 배포 상태 URL 생성 (예상)
if [ -n "$GITHUB_USER" ] && [ -n "$GITHUB_REPO" ]; then
    EXPECTED_APP_URL="https://${GITHUB_USER}-${GITHUB_REPO//_/-}-streamlit-app-${CURRENT_BRANCH}.streamlit.app"
    echo "🌐 예상 앱 URL (배포 후):"
    echo "   $EXPECTED_APP_URL"
    echo
fi

# 12. 자동 열기 옵션
if command -v open &> /dev/null; then
    # macOS
    confirm "브라우저에서 Streamlit Cloud를 열까요?"
    open "$STREAMLIT_URL"
elif command -v xdg-open &> /dev/null; then
    # Linux
    confirm "브라우저에서 Streamlit Cloud를 열까요?"
    xdg-open "$STREAMLIT_URL"
fi

echo
log_success "🎉 배포 준비 완료!"
echo
echo "💡 팁:"
echo "  - 첫 배포는 5-10분 정도 걸립니다"
echo "  - 로그는 Streamlit Cloud 대시보드에서 확인 가능"
echo "  - 문제 발생시 Logs 탭 확인"
echo
echo "================================================"