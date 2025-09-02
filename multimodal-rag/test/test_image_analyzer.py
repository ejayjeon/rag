"""Tests for image analyzer module"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.image_analyzer import ImageAnalyzer


class TestImageAnalyzer:
    
    def setup_method(self):
        """테스트 메서드 실행 전 준비"""
        self.analyzer = ImageAnalyzer()
    
    def test_init(self):
        """ImageAnalyzer 초기화 테스트"""
        assert self.analyzer is not None
        assert hasattr(self.analyzer, 'analyze_image')
        assert hasattr(self.analyzer, 'extract_text_from_image')
    
    @patch('src.image_analyzer.ChatOllama')
    @patch('src.image_analyzer.Image.open')
    def test_analyze_image_success(self, mock_image_open, mock_chat):
        """이미지 분석 성공 테스트"""
        # Mock setup
        mock_image = Mock()
        mock_image.size = (800, 600)
        mock_image_open.return_value = mock_image
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="This is a test image showing a cat.")
        mock_chat.return_value = mock_llm
        
        # Test
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            result = self.analyzer.analyze_image(tmp_file.name)
        
        assert "cat" in result.lower() or "test" in result.lower()
        mock_image_open.assert_called_once()
        mock_llm.invoke.assert_called_once()
    
    @patch('src.image_analyzer.pytesseract.image_to_string')
    @patch('src.image_analyzer.Image.open')
    def test_extract_text_from_image_success(self, mock_image_open, mock_tesseract):
        """이미지에서 텍스트 추출 성공 테스트"""
        # Mock setup
        mock_image = Mock()
        mock_image_open.return_value = mock_image
        mock_tesseract.return_value = "Extracted text from image"
        
        # Test
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            result = self.analyzer.extract_text_from_image(tmp_file.name)
        
        assert result == "Extracted text from image"
        mock_tesseract.assert_called_once_with(mock_image, lang='kor+eng')
    
    def test_validate_image_path_invalid_extension(self):
        """잘못된 이미지 확장자 테스트"""
        with pytest.raises(ValueError, match="지원하지 않는 이미지 형식입니다"):
            self.analyzer.analyze_image("test.txt")
    
    def test_validate_image_path_nonexistent_file(self):
        """존재하지 않는 파일 테스트"""
        with pytest.raises(FileNotFoundError):
            self.analyzer.analyze_image("nonexistent.jpg")
    
    @patch('src.image_analyzer.Image.open')
    def test_analyze_image_file_corrupted(self, mock_image_open):
        """손상된 이미지 파일 테스트"""
        mock_image_open.side_effect = Exception("Cannot identify image file")
        
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            with pytest.raises(Exception):
                self.analyzer.analyze_image(tmp_file.name)
    
    @patch('src.image_analyzer.pytesseract.image_to_string')
    @patch('src.image_analyzer.Image.open')
    def test_extract_text_tesseract_error(self, mock_image_open, mock_tesseract):
        """Tesseract 오류 처리 테스트"""
        mock_image_open.return_value = Mock()
        mock_tesseract.side_effect = Exception("Tesseract error")
        
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            with pytest.raises(Exception):
                self.analyzer.extract_text_from_image(tmp_file.name)
    
    @patch('src.image_analyzer.ChatOllama')
    @patch('src.image_analyzer.Image.open')
    def test_analyze_image_empty_response(self, mock_image_open, mock_chat):
        """빈 응답 처리 테스트"""
        mock_image_open.return_value = Mock(size=(100, 100))
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="")
        mock_chat.return_value = mock_llm
        
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
            result = self.analyzer.analyze_image(tmp_file.name)
        
        assert result == ""
    
    @patch('src.image_analyzer.logging')
    def test_logging_calls(self, mock_logging):
        """로깅 호출 테스트"""
        with patch('src.image_analyzer.Image.open') as mock_image_open:
            mock_image_open.side_effect = Exception("Test error")
            
            with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
                with pytest.raises(Exception):
                    self.analyzer.analyze_image(tmp_file.name)