#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한글 파일명 처리 테스트 스크립트
Docker 컨테이너에서 한글 파일명이 올바르게 처리되는지 확인
"""

import os
import sys
import locale
import tempfile
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.file_utils import sanitize_filename, safe_filename_for_temp, get_file_encoding_info

def test_locale_setup():
    """로케일 설정 확인"""
    print("🌏 로케일 설정 확인")
    print("=" * 50)
    
    # 환경 변수 확인
    print(f"LANG: {os.environ.get('LANG', 'Not set')}")
    print(f"LC_ALL: {os.environ.get('LC_ALL', 'Not set')}")
    print(f"PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING', 'Not set')}")
    
    # 현재 로케일 확인
    try:
        current_locale = locale.getlocale()
        print(f"Current locale: {current_locale}")
        
        # UTF-8 지원 확인
        encoding = locale.getpreferredencoding()
        print(f"Preferred encoding: {encoding}")
        
    except Exception as e:
        print(f"❌ 로케일 확인 실패: {e}")
    
    print()

def test_korean_filenames():
    """한글 파일명 처리 테스트"""
    print("🇰🇷 한글 파일명 처리 테스트")
    print("=" * 50)
    
    test_filenames = [
        "한글파일.mp3",
        "안녕하세요 테스트.wav",
        "음성파일_20241205.m4a",
        "특수문자<>:?\"|*.mp4",
        "매우긴파일명테스트입니다여러글자로이루어져있습니다.ogg",
        "english_file.flac",
        "혼합mixed파일명123.mp3"
    ]
    
    for filename in test_filenames:
        print(f"\n원본: {filename}")
        
        # 파일명 정리
        sanitized = sanitize_filename(filename)
        print(f"정리됨: {sanitized}")
        
        # 임시 파일명 생성
        temp_name = safe_filename_for_temp(filename)
        print(f"임시파일: {temp_name}")
        
        # 인코딩 정보
        file_info = get_file_encoding_info(Path(filename))
        print(f"인코딩정보: {file_info}")
    
    print()

def test_file_operations():
    """파일 생성/읽기 테스트"""
    print("📁 파일 생성/읽기 테스트")
    print("=" * 50)
    
    korean_content = "안녕하세요! 한글 내용 테스트입니다."
    
    test_cases = [
        ("한글파일.txt", korean_content),
        ("english_file.txt", "Hello World!"),
        ("혼합mixed123.txt", "Mixed content: 한글 + English")
    ]
    
    temp_dir = Path(tempfile.gettempdir()) / "korean_test"
    temp_dir.mkdir(exist_ok=True)
    
    for filename, content in test_cases:
        try:
            # 안전한 파일명으로 변환
            safe_name = sanitize_filename(filename)
            file_path = temp_dir / safe_name
            
            # 파일 생성
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                read_content = f.read()
            
            # 결과 확인
            success = content == read_content
            status = "✅" if success else "❌"
            
            print(f"{status} {filename} -> {safe_name}")
            print(f"   파일경로: {file_path}")
            print(f"   내용일치: {success}")
            
            # 파일 정리
            if file_path.exists():
                file_path.unlink()
                
        except Exception as e:
            print(f"❌ {filename} 처리 실패: {e}")
    
    # 임시 디렉토리 정리
    try:
        temp_dir.rmdir()
    except:
        pass
    
    print()

def test_pathlib_support():
    """pathlib의 한글 경로 지원 테스트"""
    print("🗂️ pathlib 한글 경로 지원 테스트")
    print("=" * 50)
    
    korean_paths = [
        "한글/디렉토리/파일.txt",
        "프로젝트/소스코드/main.py",
        "음성파일/테스트/샘플.wav"
    ]
    
    for path_str in korean_paths:
        try:
            path = Path(path_str)
            print(f"✅ 경로 생성 성공: {path}")
            print(f"   부모: {path.parent}")
            print(f"   이름: {path.name}")
            print(f"   확장자: {path.suffix}")
            print(f"   절대경로: {path.resolve()}")
        except Exception as e:
            print(f"❌ 경로 처리 실패 ({path_str}): {e}")
        print()

def main():
    """메인 테스트 실행"""
    print("🧪 한글 파일명 처리 테스트 시작")
    print("=" * 70)
    
    try:
        test_locale_setup()
        test_korean_filenames()
        test_file_operations()
        test_pathlib_support()
        
        print("🎉 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())