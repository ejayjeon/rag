"""Tests for utils module"""

import pytest
import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.utils import setup_logging, validate_file_path, safe_file_operation


class TestUtils:
    
    def test_setup_logging_info_level(self):
        """INFO 레벨 로깅 설정 테스트"""
        logger = setup_logging(level=logging.INFO)
        
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
    
    def test_setup_logging_debug_level(self):
        """DEBUG 레벨 로깅 설정 테스트"""
        logger = setup_logging(level=logging.DEBUG)
        
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_custom_name(self):
        """커스텀 로거 이름 테스트"""
        logger_name = "test_logger"
        logger = setup_logging(name=logger_name)
        
        assert logger.name == logger_name
    
    def test_validate_file_path_existing_file(self):
        """존재하는 파일 경로 검증 테스트"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            path = Path(tmp_file.name)
            
            # Should not raise exception
            validate_file_path(str(path))
            validate_file_path(path)
    
    def test_validate_file_path_nonexistent_file(self):
        """존재하지 않는 파일 경로 검증 테스트"""
        with pytest.raises(FileNotFoundError, match="파일을 찾을 수 없습니다"):
            validate_file_path("/nonexistent/file.txt")
    
    def test_validate_file_path_directory(self):
        """디렉토리 경로 검증 테스트"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError, match="디렉토리가 아닌 파일 경로를 입력해주세요"):
                validate_file_path(tmp_dir)
    
    def test_validate_file_path_with_extensions(self):
        """허용된 확장자 검증 테스트"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            # Should not raise exception
            validate_file_path(tmp_file.name, allowed_extensions=['.txt'])
            
            # Should raise exception
            with pytest.raises(ValueError, match="허용되지 않는 파일 확장자입니다"):
                validate_file_path(tmp_file.name, allowed_extensions=['.pdf'])
    
    def test_safe_file_operation_success(self):
        """안전한 파일 작업 성공 테스트"""
        def test_operation(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            
            result = safe_file_operation(test_operation, tmp_file.name)
            assert result == "test content"
    
    def test_safe_file_operation_file_not_found(self):
        """파일 찾을 수 없음 오류 처리 테스트"""
        def failing_operation(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        
        with pytest.raises(FileNotFoundError):
            safe_file_operation(failing_operation, "/nonexistent/file.txt")
    
    def test_safe_file_operation_permission_error(self):
        """권한 오류 처리 테스트"""
        def failing_operation(file_path):
            raise PermissionError("Permission denied")
        
        with pytest.raises(PermissionError, match="파일 접근 권한이 없습니다"):
            safe_file_operation(failing_operation, "test.txt")
    
    def test_safe_file_operation_generic_error(self):
        """일반적인 오류 처리 테스트"""
        def failing_operation(file_path):
            raise ValueError("Generic error")
        
        with pytest.raises(Exception, match="파일 작업 중 오류 발생"):
            safe_file_operation(failing_operation, "test.txt")
    
    def test_safe_file_operation_with_args(self):
        """추가 인자와 함께 안전한 파일 작업 테스트"""
        def test_operation(file_path, mode, encoding):
            with open(file_path, mode, encoding=encoding) as f:
                return f.read()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            
            result = safe_file_operation(test_operation, tmp_file.name, 'r', 'utf-8')
            assert result == "test content"
    
    def test_safe_file_operation_with_kwargs(self):
        """키워드 인자와 함께 안전한 파일 작업 테스트"""
        def test_operation(file_path, **kwargs):
            mode = kwargs.get('mode', 'r')
            encoding = kwargs.get('encoding', 'utf-8')
            with open(file_path, mode, encoding=encoding) as f:
                return f.read()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write("test content")
            tmp_file.flush()
            
            result = safe_file_operation(test_operation, tmp_file.name, mode='r', encoding='utf-8')
            assert result == "test content"
    
    @patch('src.utils.logging.getLogger')
    def test_setup_logging_handler_setup(self, mock_get_logger):
        """로깅 핸들러 설정 테스트"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        setup_logging()
        
        mock_logger.setLevel.assert_called_once()
        mock_logger.addHandler.assert_called_once()
    
    def test_validate_file_path_empty_string(self):
        """빈 문자열 경로 검증 테스트"""
        with pytest.raises(ValueError, match="파일 경로가 비어있습니다"):
            validate_file_path("")
    
    def test_validate_file_path_none(self):
        """None 경로 검증 테스트"""
        with pytest.raises(ValueError, match="파일 경로가 비어있습니다"):
            validate_file_path(None)