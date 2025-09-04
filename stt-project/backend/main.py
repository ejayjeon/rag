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
    import streamlit.web.cli as stcli
    
    # Streamlit 앱 실행
    sys.argv = [
        "streamlit", 
        "run", 
        str(project_root / "src" / "interfaces" / "streamlit_app.py"),
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]
    
    sys.exit(stcli.main())