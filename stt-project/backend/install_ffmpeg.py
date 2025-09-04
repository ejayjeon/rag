#!/usr/bin/env python3
"""
Streamlit Cloud에서 ffmpeg 설치를 위한 스크립트
이 스크립트는 앱 시작 시 자동으로 실행되어 ffmpeg를 설치합니다.
"""

import subprocess
import os
import sys
import shutil
from pathlib import Path

def install_ffmpeg():
    """ffmpeg 설치 및 설정"""
    print("🔧 ffmpeg 설치 스크립트 시작...")
    
    # 1. 이미 설치되어 있는지 확인
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        print(f"✅ ffmpeg 이미 설치됨: {ffmpeg_path}")
        return True
    
    # 2. 일반적인 경로들 확인
    common_paths = [
        '/usr/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
        '/opt/conda/bin/ffmpeg',
        '/home/appuser/.local/bin/ffmpeg'
    ]
    
    for path in common_paths:
        if Path(path).exists():
            print(f"✅ ffmpeg 발견: {path}")
            # PATH에 추가
            current_path = os.environ.get('PATH', '')
            if path not in current_path:
                os.environ['PATH'] = f"{Path(path).parent}:{current_path}"
                print(f"🔧 PATH에 추가: {Path(path).parent}")
            return True
    
    # 3. apt로 설치 시도
    print("📦 apt로 ffmpeg 설치 시도...")
    try:
        # apt update
        result = subprocess.run(
            ['apt', 'update'], 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        if result.returncode != 0:
            print(f"⚠️ apt update 실패: {result.stderr}")
            return False
        
        # ffmpeg 설치
        result = subprocess.run(
            ['apt', 'install', '-y', 'ffmpeg'], 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        if result.returncode == 0:
            print("✅ apt로 ffmpeg 설치 성공")
            return True
        else:
            print(f"⚠️ apt ffmpeg 설치 실패: {result.stderr}")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"⚠️ apt 설치 시도 실패: {e}")
    
    # 4. conda로 설치 시도
    print("🐍 conda로 ffmpeg 설치 시도...")
    try:
        result = subprocess.run(
            ['conda', 'install', '-y', '-c', 'conda-forge', 'ffmpeg'], 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        if result.returncode == 0:
            print("✅ conda로 ffmpeg 설치 성공")
            return True
        else:
            print(f"⚠️ conda ffmpeg 설치 실패: {result.stderr}")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"⚠️ conda 설치 시도 실패: {e}")
    
    # 5. pip로 ffmpeg-python 설치 시도 (대안)
    print("🐍 pip로 ffmpeg-python 설치 시도...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'ffmpeg-python'], 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        if result.returncode == 0:
            print("✅ ffmpeg-python 설치 성공")
            return True
        else:
            print(f"⚠️ ffmpeg-python 설치 실패: {result.stderr}")
    except subprocess.TimeoutExpired as e:
        print(f"⚠️ pip 설치 시도 실패: {e}")
    
    print("❌ 모든 ffmpeg 설치 시도 실패")
    return False

def setup_ffmpeg_environment():
    """ffmpeg 환경 변수 설정"""
    try:
        # FFMPEG_BINARY 환경 변수 설정
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            os.environ['FFMPEG_BINARY'] = ffmpeg_path
            print(f"🔧 FFMPEG_BINARY 설정: {ffmpeg_path}")
            return True
        
        # 일반적인 경로들에서 찾기
        common_paths = [
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/conda/bin/ffmpeg',
            '/home/appuser/.local/bin/ffmpeg'
        ]
        
        for path in common_paths:
            if Path(path).exists():
                os.environ['FFMPEG_BINARY'] = path
                print(f"🔧 FFMPEG_BINARY 설정 (직접 경로): {path}")
                return True
        
        print("⚠️ ffmpeg 경로를 찾을 수 없음")
        return False
        
    except Exception as e:
        print(f"⚠️ ffmpeg 환경 설정 중 오류: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Streamlit Cloud ffmpeg 설치 스크립트")
    
    # 설치 시도
    if install_ffmpeg():
        print("✅ ffmpeg 설치 완료")
    else:
        print("❌ ffmpeg 설치 실패 - librosa fallback 모드 사용")
    
    # 환경 설정
    setup_ffmpeg_environment()
    
    print("🏁 ffmpeg 설정 완료")
