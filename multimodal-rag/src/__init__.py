"""Multimodal RAG Package

A comprehensive multimodal RAG (Retrieval-Augmented Generation) system
that supports text, images, and PDF processing with advanced search capabilities.
"""

from .multimodal_rag import MultimodalRAG, SearchResult
from .pdf_processor import PDFProcessor
from .image_analyzer import ImageAnalyzer
from .utils import setup_logging, validate_file_path, safe_file_operation
from .document_processor import ProcessedDocument, UniversalDocumentProcessor

__version__ = "0.1.0"
__all__ = [
    "MultimodalRAG",
    "SearchResult", 
    "PDFProcessor",
    "ImageAnalyzer",
    "setup_logging",
    "validate_file_path",
    "safe_file_operation",
    "ProcessedDocument",
    "UniversalDocumentProcessor",
]