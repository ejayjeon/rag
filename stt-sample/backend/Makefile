# Makefile - 프로젝트 자동화

.PHONY: help install deploy quick-deploy update-deps test run clean setup-streamlit check-deploy

# 기본 명령어 (help)
help:
	@echo "�� 멀티모달 RAG - 자동화 명령어"
	@echo "================================"
	@echo ""
	@echo "�� 설치 및 설정:"
	@echo "  make install         - 프로젝트 초기 설정"
	@echo "  make setup-streamlit - Streamlit Cloud 설정"
	@echo ""
	@echo "🚀 배포:"
	@echo "  make deploy          - 전체 배포 프로세스 (대화형)"
	@echo "  make quick-deploy    - 빠른 배포 (기본 메시지)"
	@echo "  make check-deploy    - 배포 준비 상태 확인"
	@echo ""
	@echo "💻 개발:"
	@echo "  make run            - 로컬 실행"
	@echo "  make test           - 테스트 실행"
	@echo "  make update-deps    - 의존성 업데이트"
	@echo "  make clean          - 캐시/임시 파일 정리"

# Git 저장소 찾기 함수
find-git-repo:
	@GIT_ROOT=$$(pwd); \
	while [ "$$GIT_ROOT" != "/" ]; do \
		if [ -d "$$GIT_ROOT/.git" ]; then \
			echo "$$GIT_ROOT"; \
			exit 0; \
		fi; \
		GIT_ROOT=$$(dirname "$$GIT_ROOT"); \
	done; \
	exit 1

# 프로젝트 초기 설정
install:
	@echo "�� 프로젝트 설정 중..."
	@if ! command -v uv &> /dev/null; then \
		echo "uv 설치 중..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	uv venv
	uv pip sync
	@echo "✅ 설치 완료! 'source .venv/bin/activate'로 가상환경 활성화"

# Streamlit Cloud 초기 설정
setup-streamlit:
	@echo "☁️ Streamlit Cloud 설정 파일 생성 중..."
	@# packages.txt 생성
	@echo "ffmpeg" > packages.txt
	@echo "libsndfile1" >> packages.txt
	@echo "build-essential" >> packages.txt
	@echo "python3-dev" >> packages.txt
	@echo "git" >> packages.txt
	@echo "✅ packages.txt 생성 완료"
	
	@# .streamlit 디렉토리 및 config.toml 생성
	@mkdir -p .streamlit
	@echo "[theme]" > .streamlit/config.toml
	@echo 'primaryColor = "#FF4B4B"' >> .streamlit/config.toml
	@echo 'backgroundColor = "#FFFFFF"' >> .streamlit/config.toml
	@echo 'secondaryBackgroundColor = "#F0F2F6"' >> .streamlit/config.toml
	@echo 'textColor = "#262730"' >> .streamlit/config.toml
	@echo 'font = "sans serif"' >> .streamlit/config.toml
	@echo "" >> .streamlit/config.toml
	@echo "[server]" >> .streamlit/config.toml
	@echo "maxUploadSize = 50" >> .streamlit/config.toml
	@echo "enableCORS = false" >> .streamlit/config.toml
	@echo "" >> .streamlit/config.toml
	@echo "[browser]" >> .streamlit/config.toml
	@echo "gatherUsageStats = false" >> .streamlit/config.toml
	@echo "✅ .streamlit/config.toml 생성 완료"
	
	@# .gitignore 생성/업데이트
	@if [ ! -f .gitignore ]; then \
		echo "# Python" > .gitignore; \
		echo "__pycache__/" >> .gitignore; \
		echo "*.py[cod]" >> .gitignore; \
		echo ".venv/" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# Environment" >> .gitignore; \
		echo ".env" >> .gitignore; \
		echo ".streamlit/secrets.toml" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# IDE" >> .gitignore; \
		echo ".vscode/" >> .gitignore; \
		echo ".idea/" >> .gitignore; \
		echo ".DS_Store" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# UV" >> .gitignore; \
		echo ".uv/" >> .gitignore; \
		echo "uv.lock" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# Data" >> .gitignore; \
		echo "data/" >> .gitignore; \
		echo "*.mp3" >> .gitignore; \
		echo "*.wav" >> .gitignore; \
		echo "✅ .gitignore 생성 완료"; \
	fi

# requirements.txt 생성
requirements:
	@echo "📋 requirements.txt 생성 중..."
	@uv pip compile pyproject.toml --no-deps -q > requirements_temp.txt

	@{ \
	  echo "# Auto-generated from pyproject.toml"; \
	  echo "# Generated at: $$(date -u +'%Y-%m-%dT%H:%M:%SZ')"; \
	  echo; \
	  echo "# Torch CPU version for Streamlit Cloud"; \
	  echo "--find-links https://download.pytorch.org/whl/torch_stable.html"; \
	  echo "torch==2.3.1+cpu"; \
	  echo; \
	  echo "# Audio processing dependencies"; \
	  echo "openai-whisper==20240930"; \
	  echo "pydub==0.25.1"; \
	  echo "numpy==2.3.2"; \
	  echo; \
	  echo "# Other dependencies"; \
	} > requirements.txt

	# 중복 제거: 위에서 고정한 패키지들은 temp에서 제외
	@grep -Ev '^(torch==|openai-whisper==|pydub==|numpy==)' requirements_temp.txt >> requirements.txt
	@rm -f requirements_temp.txt
	@echo "✅ requirements.txt 생성 완료"
requirements-faster:
	@echo "📋 requirements.txt(faster-whisper) 생성 중..."
	@uv pip compile pyproject.toml --no-deps -q > requirements_temp.txt

	@{ \
	  echo "# Auto-generated from pyproject.toml (faster-whisper)"; \
	  echo "# Generated at: $$(date -u +'%Y-%m-%dT%H:%M:%SZ')"; \
	  echo; \
	  echo "# Audio processing (CTranslate2 backend)"; \
	  echo "faster-whisper==1.0.2"; \
	  echo "pydub==0.25.1"; \
	  echo "numpy==2.3.2"; \
	  echo; \
	  echo "# Other dependencies"; \
	} > requirements.txt

	@grep -Ev '^(torch==|openai-whisper==|faster-whisper==|pydub==|numpy==)' requirements_temp.txt >> requirements.txt
	@rm -f requirements_temp.txt
	@echo "✅ requirements.txt(faster) 생성 완료"

# 배포 준비 상태 확인
check-deploy:
	@echo "🔍 배포 준비 상태 확인"
	@echo "====================="
	@echo ""
	@# 필수 파일 확인
	@echo "📁 필수 파일 확인:"
	@[ -f "pyproject.toml" ] && echo "  ✅ pyproject.toml" || echo "  ❌ pyproject.toml"
	@[ -f "app.py" ] && echo "  ✅ app.py" || echo "  ❌ app.py"
	@[ -f "packages.txt" ] && echo "  ✅ packages.txt" || echo "  ❌ packages.txt"
	@[ -f "requirements.txt" ] && echo "  ✅ requirements.txt" || echo "  ❌ requirements.txt"
	@[ -f ".streamlit/config.toml" ] && echo "  ✅ .streamlit/config.toml" || echo "  ⚠️  .streamlit/config.toml (선택)"
	@echo ""
	@# Git 상태 확인 (상위 디렉토리까지 검색)
	@echo "📊 Git 상태:"
	@GIT_ROOT=$$(pwd); \
	GIT_FOUND=false; \
	while [ "$$GIT_ROOT" != "/" ]; do \
		if [ -d "$$GIT_ROOT/.git" ]; then \
			echo "  ✅ Git 저장소 발견: $$GIT_ROOT"; \
			echo "  �� 현재 브랜치: $$(cd "$$GIT_ROOT" && git branch --show-current)"; \
			if cd "$$GIT_ROOT" && git remote get-url origin &>/dev/null; then \
				echo "  🔗 원격: $$(cd "$$GIT_ROOT" && git remote get-url origin)"; \
			else \
				echo "  ⚠️  원격 저장소 미설정"; \
			fi; \
			GIT_FOUND=true; \
			break; \
		fi; \
		GIT_ROOT=$$(dirname "$$GIT_ROOT"); \
	done; \
	if [ "$$GIT_FOUND" = "false" ]; then \
		echo "  ❌ Git 저장소를 찾을 수 없음"; \
	fi
	@echo ""
	@# 환경 변수 확인
	@echo "🔐 환경 설정:"
	@[ -f ".env" ] && echo "  ⚠️  .env 파일 존재 (gitignore 확인)" || echo "  ✅ .env 파일 없음"
	@echo ""
	@if [ -f "requirements.txt" ] && [ -f "packages.txt" ] && [ -f "app.py" ]; then \
		echo "✅ 배포 준비 완료!"; \
	else \
		echo "❌ 배포 준비 미완료. 'make setup-streamlit' 실행 필요"; \
	fi

# 전체 배포 프로세스
deploy: requirements
	@echo ""
	@echo "�� 배포 프로세스 시작..."
	@# Git 저장소 찾기
	@GIT_ROOT=$$(pwd); \
	GIT_FOUND=false; \
	while [ "$$GIT_ROOT" != "/" ]; do \
		if [ -d "$$GIT_ROOT/.git" ]; then \
			GIT_FOUND=true; \
			break; \
		fi; \
		GIT_ROOT=$$(dirname "$$GIT_ROOT"); \
	done; \
	if [ "$$GIT_FOUND" = "false" ]; then \
		echo "❌ Git 저장소를 찾을 수 없습니다. 'git init'을 먼저 실행하세요."; \
		exit 1; \
	fi; \
	echo "✅ Git 저장소 발견: $$GIT_ROOT"; \
	\
	# Streamlit Cloud용 파일들을 루트에 복사
	echo "📁 Streamlit Cloud용 파일 복사 중..."; \
	cp packages.txt "$$GIT_ROOT/"; \
	cp requirements.txt "$$GIT_ROOT/"; \
	cp app.py "$$GIT_ROOT/streamlit_app.py"; \
	echo "✅ 파일 복사 완료"; \
	\
	cd "$$GIT_ROOT" && git add . && git commit -m "Deploy: $$(date '+%Y-%m-%d %H:%M:%S')" && git push -u origin $$(git branch --show-current); \
	echo ""; \
	echo "✅ 배포 완료!"; \
	echo "🔗 Streamlit Cloud에서 배포: https://share.streamlit.io"

# 빠른 배포 (기본 커밋 메시지)
quick-deploy: requirements
	@echo "⚡ 빠른 배포 모드"
	@# Git 저장소 찾기
	@GIT_ROOT=$$(pwd); \
	GIT_FOUND=false; \
	while [ "$$GIT_ROOT" != "/" ]; do \
		if [ -d "$$GIT_ROOT/.git" ]; then \
			GIT_FOUND=true; \
			break; \
		fi; \
		GIT_ROOT=$$(dirname "$$GIT_ROOT"); \
	done; \
	if [ "$$GIT_FOUND" = "false" ]; then \
		echo "❌ Git 저장소를 찾을 수 없습니다."; \
		exit 1; \
	fi; \
	cd "$$GIT_ROOT" && git add . && git commit -m "Quick deploy: $$(date '+%Y-%m-%d %H:%M:%S')" && git push -u origin $$(git branch --show-current); \
	echo ""; \
	echo "✅ 푸시 완료!"; \
	echo "🔗 Streamlit Cloud에서 배포: https://share.streamlit.io"

# 의존성 업데이트
update-deps:
	@echo "�� 의존성 업데이트 중..."
	uv pip sync
	@$(MAKE) requirements
	@echo "✅ 의존성 업데이트 완료"

# 로컬 실행
run:
	@echo "🖥️  로컬 서버 시작..."
	@if [ ! -f ".venv/bin/activate" ]; then \
		echo "⚠️  가상환경이 없습니다. 'make install' 먼저 실행하세요."; \
		exit 1; \
	fi
	uv run streamlit run app.py

# 테스트 실행
test:
	@echo "🧪 테스트 실행..."
	@if [ -d "tests" ]; then \
		uv run pytest tests/ -v; \
	else \
		echo "⚠️  tests 디렉토리가 없습니다."; \
	fi

# 정리
clean:
	@echo "🧹 정리 중..."
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@rm -rf .coverage htmlcov 2>/dev/null || true
	@rm -rf data/cache/* 2>/dev/null || true
	@rm -f requirements_temp.txt 2>/dev/null || true
	@echo "✅ 정리 완료"

# Git 초기화 (새 프로젝트용)
git-init:
	@echo "��️ Git 저장소 초기화..."
	# @git init
	@git add .
	@git commit -m "Initial commit"
	@echo ""
	@echo "GitHub 저장소를 생성한 후:"
	@echo "  git remote add origin https://github.com/USERNAME/REPO.git"
	@echo "  git push -u origin main"

# 전체 초기 설정 (새 프로젝트)
init: install setup-streamlit git-init
	@echo ""
	@echo "🎉 프로젝트 초기화 완료!"
	@echo ""
	@echo "다음 단계:"
	@echo "1. GitHub에 저장소 생성"
	@echo "2. git remote add origin [URL]"
	@echo "3. make deploy"

# 배포 후 상태 확인
post-deploy:
	@echo "�� 배포 후 체크리스트"
	@echo "==================="
	@echo ""
	@echo "1. ☁️  Streamlit Cloud 대시보드 확인"
	@echo "   https://share.streamlit.io"
	@echo ""
	@echo "2. 🔐 Secrets 설정 확인"
	@echo "   - OPENAI_API_KEY"
	@echo "   - WHISPER_MODEL_SIZE (tiny 권장)"
	@echo "   - MAX_FILE_SIZE_MB"
	@echo ""
	@echo "3. 📱 앱 테스트"
	@echo "   - 파일 업로드 테스트"
	@echo "   - 음성 변환 테스트"
	@echo "   - 요약 기능 테스트"
	@echo ""
	@echo "4. �� 모니터링"
	@echo "   - 로그 확인"
	@echo "   - 메모리 사용량 확인"
	@echo "   - 에러 추적"
