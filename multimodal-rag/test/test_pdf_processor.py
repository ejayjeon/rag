"""Tests for PDF processor module"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.pdf_processor import PDFProcessor


class TestPDFProcessor:
    
    def setup_method(self):
        """테스트 메서드 실행 전 준비"""
        self.processor = PDFProcessor()
    
    def test_init(self):
        """PDFProcessor 초기화 테스트"""
        assert self.processor is not None
        assert hasattr(self.processor, 'extract_text')
        assert hasattr(self.processor, 'extract_images')
    
    @patch('src.pdf_processor.fitz')
    def test_extract_text_success(self, mock_fitz):
        """PDF 텍스트 추출 성공 테스트"""
        # Mock PDF document setup
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Test PDF content"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.__enter__ = Mock(return_value=mock_doc)
        mock_doc.__exit__ = Mock(return_value=None)
        mock_fitz.open.return_value = mock_doc
        
        # Test
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            result = self.processor.extract_text(tmp_file.name)
            
        assert result == "Test PDF content"
        mock_fitz.open.assert_called_once_with(tmp_file.name)
    
    @patch('src.pdf_processor.fitz')
    def test_extract_text_file_not_found(self, mock_fitz):
        """존재하지 않는 파일 처리 테스트"""
        mock_fitz.open.side_effect = FileNotFoundError("File not found")
        
        with pytest.raises(FileNotFoundError):
            self.processor.extract_text("nonexistent.pdf")
    
    @patch('src.pdf_processor.fitz')
    def test_extract_images_success(self, mock_fitz):
        """PDF 이미지 추출 성공 테스트"""
        # Mock setup
        mock_doc = Mock()
        mock_page = Mock()
        mock_img_list = [Mock()]
        mock_img_list[0].get_pixmap.return_value.tobytes.return_value = b"fake_image_data"
        mock_page.get_images.return_value = [(0, 0, 0, 0, 0, "", "", 0, 0)]
        mock_page.load_image.return_value = mock_img_list[0]
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.__enter__ = Mock(return_value=mock_doc)
        mock_doc.__exit__ = Mock(return_value=None)
        mock_fitz.open.return_value = mock_doc
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.processor.extract_images("test.pdf", tmp_dir)
            
        assert len(result) == 1
        assert result[0].endswith('.png')
    
    @patch('src.pdf_processor.fitz')
    def test_extract_text_and_images_integration(self, mock_fitz):
        """텍스트와 이미지 통합 추출 테스트"""
        # Mock setup
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Test content"
        mock_page.get_images.return_value = []  # No images
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.__enter__ = Mock(return_value=mock_doc)
        mock_doc.__exit__ = Mock(return_value=None)
        mock_fitz.open.return_value = mock_doc
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            text, images = self.processor.extract_text_and_images("test.pdf", tmp_dir)
            
        assert text == "Test content"
        assert images == []
    
    def test_process_invalid_file_extension(self):
        """잘못된 파일 확장자 테스트"""
        with pytest.raises(ValueError, match="PDF 파일이 아닙니다"):
            self.processor.extract_text("test.txt")
    
    @patch('src.pdf_processor.logging')
    def test_logging_calls(self, mock_logging):
        """로깅 호출 테스트"""
        # This test ensures logging is called appropriately
        with patch('src.pdf_processor.fitz') as mock_fitz:
            mock_fitz.open.side_effect = Exception("Test error")
            
            with pytest.raises(Exception):
                self.processor.extract_text("test.pdf")