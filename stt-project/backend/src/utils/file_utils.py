"""
파일 처리 유틸리티
"""
import re
import unicodedata
from pathlib import Path
from datetime import datetime

def sanitize_filename(filename: str) -> str:
    """
    파일명을 시스템에서 안전하게 사용할 수 있도록 정리
    
    Args:
        filename: 원본 파일명
    
    Returns:
        정리된 파일명
    """
    if not filename:
        return f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 파일명과 확장자 분리
    path = Path(filename)
    name = path.stem
    extension = path.suffix
    
    # Unicode 정규화 (NFC 형식으로 통일)
    name = unicodedata.normalize('NFC', name)
    
    # 위험한 문자 제거 (파일시스템에서 문제가 될 수 있는 문자들)
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    name = re.sub(dangerous_chars, '_', name)
    
    # 연속된 공백이나 점을 하나로 줄이기
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'\.+', '.', name)
    
    # 앞뒤 공백과 점 제거
    name = name.strip(' .')
    
    # 빈 이름인 경우 타임스탬프 사용
    if not name:
        name = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 파일명 길이 제한 (255자 제한, 확장자 포함)
    max_length = 255 - len(extension) - 10  # 여유분 10자
    if len(name) > max_length:
        name = name[:max_length]
    
    return f"{name}{extension}"

def ensure_unique_filename(file_path: Path) -> Path:
    """
    파일이 이미 존재하는 경우 고유한 파일명 생성
    
    Args:
        file_path: 원본 파일 경로
    
    Returns:
        고유한 파일 경로
    """
    if not file_path.exists():
        return file_path
    
    stem = file_path.stem
    suffix = file_path.suffix
    parent = file_path.parent
    
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def safe_filename_for_temp(original_filename: str) -> str:
    """
    임시 파일을 위한 안전한 파일명 생성
    
    Args:
        original_filename: 원본 파일명
    
    Returns:
        임시 파일용 안전한 파일명
    """
    # 기본 정리
    clean_name = sanitize_filename(original_filename)
    
    # 타임스탬프 추가로 중복 방지
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]  # 마이크로초 3자리
    
    path = Path(clean_name)
    stem = path.stem
    suffix = path.suffix
    
    return f"temp_{timestamp}_{stem}{suffix}"

def get_file_encoding_info(file_path: Path) -> dict:
    """
    파일의 인코딩 정보를 반환
    
    Args:
        file_path: 파일 경로
    
    Returns:
        인코딩 정보 딕셔너리
    """
    try:
        # 파일명 인코딩 정보
        filename = str(file_path)
        filename_bytes = filename.encode('utf-8')
        
        return {
            'filename': filename,
            'filename_utf8': filename,
            'filename_bytes_length': len(filename_bytes),
            'is_ascii': filename.isascii(),
            'contains_korean': bool(re.search(r'[가-힣]', filename)),
            'normalized': unicodedata.normalize('NFC', filename)
        }
    except Exception as e:
        return {
            'error': str(e),
            'filename': str(file_path)
        }