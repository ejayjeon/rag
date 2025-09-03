"""Utility functions for multimodal RAG system"""

import logging
from typing import List, Callable, Any, Optional
from pathlib import Path
import os

# 안전한 import with 폴백
try:
    import requests
except ImportError:
    requests = None

try:
    import ollama
except ImportError:
    ollama = None


def setup_logging(level: int = logging.INFO, name: str = "multimodal_rag") -> logging.Logger:
    """로깅 설정
    
    Args:
        level: 로그 레벨 (기본값: INFO)
        name: 로거 이름 (기본값: "multimodal_rag")
    
    Returns:
        설정된 로거 객체
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 핸들러가 이미 있으면 추가하지 않음
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def validate_file_path(file_path: str | Path, allowed_extensions: Optional[List[str]] = None) -> None:
    """파일 경로 검증
    
    Args:
        file_path: 검증할 파일 경로
        allowed_extensions: 허용된 파일 확장자 목록 (선택사항)
    
    Raises:
        ValueError: 잘못된 경로나 확장자인 경우
        FileNotFoundError: 파일이 존재하지 않는 경우
    """
    if not file_path:
        raise ValueError("파일 경로가 비어있습니다.")
    
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    if path.is_dir():
        raise ValueError("디렉토리가 아닌 파일 경로를 입력해주세요.")
    
    if allowed_extensions:
        if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
            raise ValueError(f"허용되지 않는 파일 확장자입니다. 허용된 확장자: {allowed_extensions}")


def safe_file_operation(operation: Callable, file_path: str, *args, **kwargs) -> Any:
    """안전한 파일 작업 수행
    
    Args:
        operation: 수행할 파일 작업 함수
        file_path: 파일 경로
        *args: operation에 전달할 추가 인자
        **kwargs: operation에 전달할 추가 키워드 인자
    
    Returns:
        operation의 결과
    
    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
        PermissionError: 파일 접근 권한이 없는 경우
        Exception: 기타 파일 작업 오류
    """
    try:
        return operation(file_path, *args, **kwargs)
    except FileNotFoundError:
        raise  # FileNotFoundError는 그대로 전파
    except PermissionError as e:
        raise PermissionError(f"파일 접근 권한이 없습니다: {file_path}") from e
    except Exception as e:
        raise Exception(f"파일 작업 중 오류 발생: {str(e)}") from e


# Ollama 서버 설정
DEFAULT_OLLAMA_URL = "http://localhost:11434"
NGROK_OLLAMA_URL = "https://72e0239167b6.ngrok-free.app"

# 동적으로 ngrok URL을 업데이트할 수 있는 변수
_current_ngrok_url = NGROK_OLLAMA_URL

def update_ngrok_url(new_url: str) -> None:
    """ngrok URL 업데이트
    
    Args:
        new_url: 새로운 ngrok URL
    """
    global _current_ngrok_url
    _current_ngrok_url = new_url

def get_current_ngrok_url() -> str:
    """현재 설정된 ngrok URL 반환
    
    Returns:
        현재 ngrok URL
    """
    return _current_ngrok_url

def get_ollama_urls() -> List[str]:
    """사용 가능한 Ollama 서버 URL 목록 반환
    
    Returns:
        사용 가능한 Ollama 서버 URL 목록 (우선순위 순)
    """
    urls = []
    
    # 환경변수에서 Ollama URL 확인
    env_url = os.environ.get('OLLAMA_BASE_URL')
    if env_url:
        urls.append(env_url)
    
    # ngrok URL 추가 (동적 URL 사용)
    urls.append(_current_ngrok_url)
    
    # 로컬 URL 추가
    urls.append(DEFAULT_OLLAMA_URL)
    
    return urls

def check_ollama_status(url: str = None) -> tuple[bool, str]:
    """Ollama 서버 상태 확인
    
    Args:
        url: 확인할 Ollama 서버 URL (None이면 모든 URL 시도)
    
    Returns:
        (연결 성공 여부, 연결된 URL)
    """
    if not requests:
        return False, ""
    
    # ngrok용 헤더 설정
    headers = {
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'MultimodalRAG/1.0'
    }
    
    if url:
        # 특정 URL만 확인
        try:
            response = requests.get(f"{url}/api/tags", timeout=5, headers=headers)
            if response.status_code == 200:
                return True, url
        except:
            pass
        return False, ""
    
    # 모든 URL 시도
    for test_url in get_ollama_urls():
        try:
            response = requests.get(f"{test_url}/api/tags", timeout=5, headers=headers)
            if response.status_code == 200:
                return True, test_url
        except:
            continue
    
    # Streamlit Cloud 환경에서는 연결 실패로 간주하지만 앱은 계속 작동
    return False, "연결 실패 (텍스트 처리는 가능)"

def get_current_ollama_url() -> str:
    """현재 연결된 Ollama 서버 URL 반환
    
    Returns:
        현재 연결된 Ollama 서버 URL
    """
    is_available, url = check_ollama_status()
    return url if is_available else "연결 안됨"

def test_ngrok_connection() -> tuple[bool, str]:
    """ngrok 연결 테스트
    
    Returns:
        (연결 성공 여부, 상태 메시지)
    """
    if not requests:
        return False, "requests 모듈이 설치되지 않음"
    
    # ngrok용 헤더 설정
    headers = {
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'MultimodalRAG/1.0'
    }
    
    try:
        response = requests.get(f"{_current_ngrok_url}/api/tags", timeout=10, headers=headers)
        if response.status_code == 200:
            return True, f"ngrok 연결 성공: {_current_ngrok_url}"
        else:
            return False, f"ngrok 응답 오류: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "ngrok 연결 시간 초과"
    except requests.exceptions.ConnectionError:
        return False, "ngrok 연결 실패"
    except Exception as e:
        return False, f"ngrok 연결 오류: {str(e)}"


def call_ollama_api(endpoint: str, data: dict = None, timeout: int = 30) -> dict:
    """Ollama API 직접 호출 (CORS 문제 해결)
    
    Args:
        endpoint: API 엔드포인트 (예: 'api/tags', 'api/generate')
        data: POST 요청 데이터 (None이면 GET 요청)
        timeout: 요청 타임아웃 (초)
    
    Returns:
        API 응답 데이터 또는 None (실패 시)
    """
    if not requests:
        return None
    
    # ngrok용 헤더 설정
    headers = {
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'MultimodalRAG/1.0',
        'Content-Type': 'application/json'
    }
    
    # 연결 가능한 URL 찾기
    is_available, available_url = check_ollama_status()
    if not is_available:
        return None
    
    try:
        url = f"{available_url}/{endpoint}"
        
        if data:
            response = requests.post(url, json=data, timeout=timeout, headers=headers)
        else:
            response = requests.get(url, timeout=timeout, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ollama API 오류: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Ollama API 호출 실패: {str(e)}")
        return None

def get_ollama_models(url: str = None) -> List[str]:
    """설치된 Ollama 모델 목록 반환 (프록시 방식)
    
    Args:
        url: Ollama 서버 URL (사용하지 않음, 자동 감지)
    
    Returns:
        설치된 모델 이름 목록
    """
    # 직접 API 호출로 모델 목록 가져오기
    response = call_ollama_api('api/tags')
    if not response or 'models' not in response:
        return ['llava:latest']  # 기본값
    
    try:
        model_names = []
        for model in response['models']:
            if 'name' in model:
                # 태그 제거 (예: llava:latest -> llava)
                base_name = model['name'].split(':')[0]
                if base_name not in model_names:  # 중복 제거
                    model_names.append(base_name)
        
        return model_names
        
    except Exception as e:
        print(f"모델 목록 파싱 오류: {str(e)}")
        return ['llava:latest']

def get_ollama_models_with_versions(url: str = None) -> List[str]:
    """설치된 Ollama 모델 목록 반환 (버전 포함, 프록시 방식)
    
    Args:
        url: Ollama 서버 URL (사용하지 않음, 자동 감지)
    
    Returns:
        설치된 모델 이름 목록 (버전 포함, 예: llava:latest, llama2:latest)
    """
    # 직접 API 호출로 모델 목록 가져오기
    response = call_ollama_api('api/tags')
    if not response or 'models' not in response:
        return []
    
    try:
        model_names = []
        for model in response['models']:
            if 'name' in model and model['name'] not in model_names:
                model_names.append(model['name'])
        
        return model_names
        
    except Exception as e:
        print(f"모델 목록 파싱 오류: {str(e)}")
        return []

def generate_ollama_response(model: str, prompt: str, system: str = None) -> str:
    """Ollama 모델로 응답 생성 (프록시 방식)
    
    Args:
        model: 사용할 모델명
        prompt: 사용자 프롬프트
        system: 시스템 프롬프트 (선택사항)
    
    Returns:
        생성된 응답 또는 오류 메시지
    """
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    if system:
        data["system"] = system
    
    response = call_ollama_api('api/generate', data)
    if response and 'response' in response:
        return response['response']
    else:
        return "응답 생성에 실패했습니다."


def is_supported_file_type(file_path: str) -> str:
    """파일 유형 확인
    
    Args:
        file_path: 확인할 파일 경로
    
    Returns:
        파일 유형 ('pdf', 'image', 'text', 'unknown')
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.pdf':
        return 'pdf'
    elif suffix in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
        return 'image'
    elif suffix in ['.txt', '.md', '.rst', '.json', '.csv']:
        return 'text'
    else:
        return 'unknown'


def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형식으로 변환
    
    Args:
        size_bytes: 바이트 단위 파일 크기
    
    Returns:
        포맷된 파일 크기 문자열 (예: "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    i = 0
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"