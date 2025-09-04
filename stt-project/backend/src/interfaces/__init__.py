"""
Interfaces 모듈

사용자 인터페이스를 담당하는 모듈들을 포함합니다:
- FastAPIApp: FastAPI 웹 서버 인터페이스
- StreamlitApp: Streamlit 웹 앱 인터페이스
"""

from .fastapi_app import app as fastapi_app
from .streamlit_app import main as streamlit_main

__all__ = [
    "fastapi_app",
    "streamlit_main",
]
