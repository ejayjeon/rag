"""Tests for multimodal RAG module"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.multimodal_rag import MultimodalRAG, SearchResult


class TestMultimodalRAG:
    
    def setup_method(self):
        """테스트 메서드 실행 전 준비"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.tmp_dir = tmp_dir
            self.rag = MultimodalRAG(
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                llm_model="llama3.2",
                persist_directory=tmp_dir
            )
    
    def test_init(self):
        """MultimodalRAG 초기화 테스트"""
        assert self.rag is not None
        assert hasattr(self.rag, 'add_documents')
        assert hasattr(self.rag, 'search')
    
    @patch('src.multimodal_rag.HuggingFaceEmbeddings')
    @patch('src.multimodal_rag.Chroma')
    @patch('src.multimodal_rag.ChatOllama')
    def test_init_with_mocks(self, mock_chat, mock_chroma, mock_embeddings):
        """모킹을 사용한 초기화 테스트"""
        mock_embeddings.return_value = Mock()
        mock_chroma.return_value = Mock()
        mock_chat.return_value = Mock()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            rag = MultimodalRAG(persist_directory=tmp_dir)
            assert rag is not None
    
    @patch('src.multimodal_rag.PDFProcessor')
    @patch('src.multimodal_rag.ImageAnalyzer')
    def test_add_pdf_document(self, mock_image_analyzer, mock_pdf_processor):
        """PDF 문서 추가 테스트"""
        # Mock setup
        mock_processor = Mock()
        mock_processor.extract_text_and_images.return_value = ("Test content", [])
        mock_pdf_processor.return_value = mock_processor
        
        mock_analyzer = Mock()
        mock_image_analyzer.return_value = mock_analyzer
        
        # Mock vectorstore
        with patch.object(self.rag, 'vectorstore') as mock_vectorstore:
            mock_vectorstore.add_documents = Mock()
            
            with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
                self.rag.add_pdf_document(tmp_file.name)
            
            mock_processor.extract_text_and_images.assert_called_once()
            mock_vectorstore.add_documents.assert_called_once()
    
    @patch('src.multimodal_rag.ImageAnalyzer')
    def test_add_image_document(self, mock_image_analyzer):
        """이미지 문서 추가 테스트"""
        # Mock setup
        mock_analyzer = Mock()
        mock_analyzer.analyze_image.return_value = "Image description"
        mock_analyzer.extract_text_from_image.return_value = "OCR text"
        mock_image_analyzer.return_value = mock_analyzer
        
        # Mock vectorstore
        with patch.object(self.rag, 'vectorstore') as mock_vectorstore:
            mock_vectorstore.add_documents = Mock()
            
            with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
                self.rag.add_image_document(tmp_file.name)
            
            mock_analyzer.analyze_image.assert_called_once()
            mock_analyzer.extract_text_from_image.assert_called_once()
            mock_vectorstore.add_documents.assert_called_once()
    
    def test_add_text_document(self):
        """텍스트 문서 추가 테스트"""
        with patch.object(self.rag, 'vectorstore') as mock_vectorstore:
            mock_vectorstore.add_documents = Mock()
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
                tmp_file.write("Test text content")
                tmp_file.flush()
                
                self.rag.add_text_document(tmp_file.name)
            
            mock_vectorstore.add_documents.assert_called_once()
    
    def test_search_with_results(self):
        """검색 결과가 있는 경우 테스트"""
        with patch.object(self.rag, 'vectorstore') as mock_vectorstore:
            with patch.object(self.rag, 'llm') as mock_llm:
                # Mock search results
                mock_doc = Mock()
                mock_doc.page_content = "Test content"
                mock_doc.metadata = {"source": "test.pdf"}
                mock_vectorstore.similarity_search.return_value = [mock_doc]
                
                # Mock LLM response
                mock_llm.invoke.return_value = Mock(content="Test answer")
                
                result = self.rag.search("test query")
                
                assert isinstance(result, SearchResult)
                assert result.answer == "Test answer"
                assert len(result.sources) == 1
                assert result.confidence > 0
    
    def test_search_no_results(self):
        """검색 결과가 없는 경우 테스트"""
        with patch.object(self.rag, 'vectorstore') as mock_vectorstore:
            mock_vectorstore.similarity_search.return_value = []
            
            result = self.rag.search("test query")
            
            assert isinstance(result, SearchResult)
            assert "관련 문서를 찾을 수 없습니다" in result.answer
            assert len(result.sources) == 0
            assert result.confidence == 0.0
    
    def test_add_documents_batch(self):
        """배치 문서 추가 테스트"""
        with patch.object(self.rag, 'add_pdf_document') as mock_add_pdf:
            with patch.object(self.rag, 'add_image_document') as mock_add_image:
                with patch.object(self.rag, 'add_text_document') as mock_add_text:
                    
                    documents = [
                        "test1.pdf",
                        "test2.jpg", 
                        "test3.txt"
                    ]
                    
                    self.rag.add_documents(documents)
                    
                    mock_add_pdf.assert_called_once_with("test1.pdf")
                    mock_add_image.assert_called_once_with("test2.jpg")
                    mock_add_text.assert_called_once_with("test3.txt")
    
    def test_unsupported_file_type(self):
        """지원하지 않는 파일 형식 테스트"""
        with pytest.raises(ValueError, match="지원하지 않는 파일 형식입니다"):
            self.rag.add_documents(["test.xyz"])
    
    @patch('src.multimodal_rag.logging')
    def test_error_handling(self, mock_logging):
        """오류 처리 테스트"""
        with patch.object(self.rag, 'vectorstore') as mock_vectorstore:
            mock_vectorstore.similarity_search.side_effect = Exception("Search error")
            
            result = self.rag.search("test query")
            
            assert isinstance(result, SearchResult)
            assert "검색 중 오류가 발생했습니다" in result.answer