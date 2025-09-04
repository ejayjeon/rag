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
    Path(__file__).parent,  # 로컬 개발 환경
    current_dir / "stt-project" / "backend",  # Streamlit Cloud 배포 환경
    current_dir,  # 현재 디렉토리가 프로젝트 루트인 경우
    Path("/mount/src/rag/stt-project/backend"),  # Streamlit Cloud 절대 경로
]

for path in possible_paths:
    if path.exists() and (path / "src").exists():
        project_root = path
        break

# 프로젝트 루트를 찾지 못한 경우 현재 디렉토리 사용
if project_root is None:
    project_root = current_dir

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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