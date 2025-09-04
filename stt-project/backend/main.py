"""
Streamlit 앱 진입점
배포 환경에서 올바른 경로 설정을 위한 메인 파일
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가 (배포 환경 대응)
current_dir = Path.cwd()
project_root = None

# 가능한 프로젝트 루트 경로들을 순서대로 확인
possible_paths = [
    current_dir / "stt-project" / "backend",  # Streamlit Cloud 배포 환경 (우선순위 1)
    Path("/mount/src/rag/stt-project/backend"),  # Streamlit Cloud 절대 경로 (우선순위 2)
    Path(__file__).parent,  # 로컬 개발 환경 (우선순위 3)
    current_dir,  # 현재 디렉토리가 프로젝트 루트인 경우 (우선순위 4)
]

# 디버깅을 위한 경로 확인
print(f"🔍 [main.py] 경로 감지 중...")
print(f"현재 작업 디렉토리: {current_dir}")
print(f"파일 위치: {Path(__file__)}")

for i, path in enumerate(possible_paths):
    print(f"경로 {i+1}: {path} - 존재: {path.exists()}")
    if path.exists() and (path / "src").exists():
        print(f"✅ 유효한 프로젝트 루트 발견: {path}")
        project_root = path
        break

# 프로젝트 루트를 찾지 못한 경우 현재 디렉토리 사용
if project_root is None:
    print(f"⚠️ 프로젝트 루트를 찾지 못함. 현재 디렉토리 사용: {current_dir}")
    project_root = current_dir

print(f"🎯 최종 프로젝트 루트: {project_root}")

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"📁 Python path에 추가: {project_root}")

# Streamlit 앱 import 및 실행
if __name__ == "__main__":
    # Streamlit 앱 직접 import
    try:
        from src.interfaces.streamlit_app import main
        main()
    except ImportError as e:
        print(f"Import error: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path[:3]}...")
        print(f"Project root: {project_root}")
        
        # Fallback: streamlit CLI 사용
        import streamlit.web.cli as stcli
        sys.argv = [
            "streamlit", 
            "run", 
            str(project_root / "src" / "interfaces" / "streamlit_app.py"),
            "--server.port=8501",
            "--server.address=0.0.0.0"
        ]
        sys.exit(stcli.main())