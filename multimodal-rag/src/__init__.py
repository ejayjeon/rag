"""Multimodal RAG Package

A comprehensive multimodal RAG (Retrieval-Augmented Generation) system
that supports text, images, and PDF processing with advanced search capabilities.
"""

from .multimodal_rag import MultimodalRAG, SearchResult
from .pdf_processor import PDFProcessor
from .image_analyzer import ImageAnalyzer
from .utils import setup_logging, validate_file_path, safe_file_operation
from .document_processor import ProcessedDocument, UniversalDocumentProcessor

# 편의를 위한 별칭 및 추가 import
from .image_analyzer import (
    ImageAnalyzer,
    # 파일 관리 관련 함수들도 직접 import 가능
    ImageAnalyzer as VisionProcessor,  # Vision 처리용 별칭
)

__version__ = "0.1.0"
__all__ = [
    "MultimodalRAG",
    "SearchResult", 
    "PDFProcessor",
    "ImageAnalyzer",
    "VisionProcessor",  # Vision 처리용 별칭 추가
    "setup_logging",
    "validate_file_path",
    "safe_file_operation",
    "ProcessedDocument",
    "UniversalDocumentProcessor",
]

# 사용 예시를 위한 docstring 추가
__doc__ = """
Multimodal RAG Package

사용 예시:
    from multimodal_rag import ImageAnalyzer, MultimodalRAG
    
    # 이미지 분석기 생성
    analyzer = ImageAnalyzer(provider="ollama", model_name="llava")
    
    # 단일 이미지 분석
    result = analyzer.analyze_image("image.jpg")
    print(f"파일 ID: {result['file_id']}")
    print(f"분석 결과: {result['analysis']}")
    
    # 다중 이미지 컨텍스트 분석
    context_result = analyzer.analyze_multiple_images_in_context(["img1.jpg", "img2.jpg"])
    print(f"통합 분석: {context_result['combined_analysis']}")
    
    # 기존 컨텍스트에 새 이미지 추가
    updated_context = analyzer.update_image_context("new_img.jpg", context_result)
    
    # RAG 시스템 생성
    rag = MultimodalRAG()
    rag.add_image_document("image.jpg")
"""