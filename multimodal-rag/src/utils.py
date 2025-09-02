"""Utility functions for multimodal RAG system"""

import logging
from typing import List, Callable, Any, Optional
from pathlib import Path

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


def check_ollama_status() -> bool:
    """Ollama 서버 상태 확인
    
    Returns:
        Ollama 서버가 실행 중이면 True, 그렇지 않으면 False
    """
    if not requests:
        return False
        
    try:
        response = requests.get("http://localhost:11434", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_ollama_models() -> List[str]:
    """설치된 Ollama 모델 목록 반환
    
    Returns:
        설치된 모델 이름 목록
    """
    if not ollama:
        return ['llava:latest']
        
    try:
        models = ollama.list()
        
        # 디버깅: 실제 타입과 내용 확인
        if isinstance(models, str):
            # 문자열인 경우 'models=' 부분 제거하고 파싱
            if models.startswith('models='):
                models_str = models.replace('models=', '')
                # 간단한 파싱: 'llava:latest' 형태의 모델명 추출
                import re
                model_matches = re.findall(r"'([^']+)'", models_str)
                if model_matches:
                    model_names = []
                    for match in model_matches:
                        if ':' in match:  # 모델명:태그 형태
                            base_name = match.split(':')[0]
                            if base_name not in model_names:
                                model_names.append(base_name)
                    return model_names
                else:
                    raise ValueError(f"문자열에서 모델명을 추출할 수 없음: {models_str}")
        
        # ListResponse 타입인 경우
        if hasattr(models, 'models'):
            model_names = []
            for i, model in enumerate(models.models):
                try:
                    # Model 객체에서 'model' 속성 사용 (더 안전한 방법)
                    if hasattr(model, 'model') and model.model:
                        name = model.model
                    elif hasattr(model, 'name') and model.name:
                        name = model.name
                    else:
                        # 객체의 모든 속성 확인
                        attrs = [attr for attr in dir(model) if not attr.startswith('_')]
                        raise ValueError(f"모델 {i}에 'model' 속성이 없음. 사용 가능한 속성들: {attrs}")
                    
                    if name:
                        # 태그 제거 (예: llava:latest -> llava)
                        base_name = name.split(':')[0]
                        if base_name not in model_names:  # 중복 제거
                            model_names.append(base_name)
                            
                except Exception as model_error:
                    raise ValueError(f"모델 {i} 처리 중 오류: {model_error}")
            
            return model_names
        
        # 리스트인 경우 (기존 로직)
        if isinstance(models, list):
            model_names = []
            for i, model in enumerate(models):
                try:
                    # Model 객체에서 'model' 속성 사용 (더 안전한 방법)
                    if hasattr(model, 'model') and model.model:
                        name = model.model
                    elif hasattr(model, 'name') and model.name:
                        name = model.name
                    else:
                        # 객체의 모든 속성 확인
                        attrs = [attr for attr in dir(model) if not attr.startswith('_')]
                        raise ValueError(f"모델 {i}에 'model' 속성이 없음. 사용 가능한 속성들: {attrs}")
                    
                    if name:
                        # 태그 제거 (예: llava:latest -> llava)
                        base_name = name.split(':')[0]
                        if base_name not in model_names:  # 중복 제거
                            model_names.append(base_name)
                            
                except Exception as model_error:
                    raise ValueError(f"모델 {i} 처리 중 오류: {model_error}")
            
            return model_names
        
        # 기타 타입 - 에러 메시지에서 타입 정보 포함
        raise ValueError(f"예상과 다른 응답 구조: {models} (타입: {type(models)})")
            
    except Exception as e:
        # 에러를 다시 발생시켜서 Streamlit에서 처리할 수 있게
        raise Exception(f"Ollama 모델 목록 가져오기 실패: {e}")


def get_ollama_models_with_versions() -> List[str]:
    """설치된 Ollama 모델 목록 반환 (버전 포함)
    
    Returns:
        설치된 모델 이름 목록 (버전 포함, 예: llava:latest, llama2:latest)
    """
    if not ollama:
        return []
        
    try:
        models = ollama.list()
        
        # ListResponse 타입인 경우
        if hasattr(models, 'models'):
            model_names = []
            for i, model in enumerate(models.models):
                try:
                    # Model 객체에서 'model' 속성 사용 (더 안전한 방법)
                    if hasattr(model, 'model') and model.model:
                        name = model.model
                    elif hasattr(model, 'name') and model.name:
                        name = model.name
                    else:
                        # 객체의 모든 속성 확인
                        attrs = [attr for attr in dir(model) if not attr.startswith('_')]
                        raise ValueError(f"모델 {i}에 'model' 속성이 없음. 사용 가능한 속성들: {attrs}")
                    
                    if name and name not in model_names:  # 중복 제거
                        model_names.append(name)
                            
                except Exception as model_error:
                    raise ValueError(f"모델 {i} 처리 중 오류: {model_error}")
            
            return model_names
        
        # 리스트인 경우 (기존 로직)
        if isinstance(models, list):
            model_names = []
            for i, model in enumerate(models):
                try:
                    # Model 객체에서 'model' 속성 사용 (더 안전한 방법)
                    if hasattr(model, 'model') and model.model:
                        name = model.model
                    elif hasattr(model, 'name') and model.name:
                        name = model.name
                    else:
                        # 객체의 모든 속성 확인
                        attrs = [attr for attr in dir(model) if not attr.startswith('_')]
                        raise ValueError(f"모델 {i}에 'model' 속성이 없음. 사용 가능한 속성들: {attrs}")
                    
                    if name and name not in model_names:  # 중복 제거
                        model_names.append(name)
                            
                except Exception as model_error:
                    raise ValueError(f"모델 {i} 처리 중 오류: {model_error}")
            
            return model_names
        
        # 기타 타입 - 에러 메시지에서 타입 정보 포함
        raise ValueError(f"예상과 다른 응답 구조: {models} (타입: {type(models)})")
            
    except Exception as e:
        # 에러를 다시 발생시켜서 Streamlit에서 처리할 수 있게
        raise Exception(f"Ollama 모델 목록 가져오기 실패: {e}")


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