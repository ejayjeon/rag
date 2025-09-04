"""
Streamlit 앱 진입점
배포 환경에서 올바른 경로 설정을 위한 메인 파일
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
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