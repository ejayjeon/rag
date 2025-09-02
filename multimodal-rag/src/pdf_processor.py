import fitz  # PyMuPDF
import os
from pathlib import Path
from typing import List, Dict, Any
# 안전한 import with 폴백
try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:
    try:
        from langchain.document_loaders import PyPDFLoader
    except ImportError:
        PyPDFLoader = None

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        RecursiveCharacterTextSplitter = None

try:
    from langchain.schema import Document
except ImportError:
    try:
        from langchain_core.documents import Document
    except ImportError:
        Document = None

class PDFProcessor:
    """PDF 파일 처리 전용 클래스"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        # 의존성 확인 및 초기화
        if RecursiveCharacterTextSplitter:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        else:
            # 폴백: 간단한 텍스트 분할기
            self.text_splitter = None
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
    
    def extract_text_chunks(self, pdf_path: str) -> List[Document]:
        """PDF에서 텍스트 추출 및 청킹"""
        if not Document:
            raise ImportError("Document 클래스를 import할 수 없습니다.")
            
        if PyPDFLoader and self.text_splitter:
            # LangChain 사용
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            return self.text_splitter.split_documents(documents)
        else:
            # 폴백: PyMuPDF 사용
            return self._extract_text_with_pymupdf(pdf_path)
    
    def _extract_text_with_pymupdf(self, pdf_path: str) -> List[Document]:
        """PyMuPDF를 사용한 텍스트 추출"""
        if not Document:
            raise ImportError("Document 클래스를 import할 수 없습니다.")
            
        documents = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            if text.strip():
                # 간단한 청킹
                chunks = self._simple_chunk(text)
                for i, chunk in enumerate(chunks):
                    documents.append(Document(
                        page_content=chunk,
                        metadata={
                            "source": pdf_path,
                            "page": page_num + 1,
                            "chunk": i
                        }
                    ))
        
        doc.close()
        return documents
    
    def _simple_chunk(self, text: str) -> List[str]:
        """간단한 텍스트 청킹"""
        if not self.text_splitter:  # 폴백 모드
            chunks = []
            words = text.split()
            current_chunk = ""
            
            for word in words:
                if len(current_chunk + " " + word) <= self.chunk_size:
                    current_chunk += " " + word if current_chunk else word
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = word
            
            if current_chunk:
                chunks.append(current_chunk)
                
            return chunks
        return [text]  # 청킹 안함
    
    def extract_images(self, pdf_path: str, output_dir: str = "temp_images") -> List[Dict[str, Any]]:
        """PDF에서 이미지 추출"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        doc = fitz.open(pdf_path)
        image_info = []
        
        try:
            for page_num in range(doc.page_count):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_filename = f"page_{page_num+1}_img_{img_index+1}.png"
                            img_path = os.path.join(output_dir, img_filename)
                            
                            pix.save(img_path)
                            
                            image_info.append({
                                "path": img_path,
                                "page": page_num + 1,
                                "index": img_index + 1,
                                "filename": img_filename
                            })
                        
                        pix = None
                    except Exception as e:
                        print(f"이미지 추출 오류: {e}")
                        continue
        finally:
            doc.close()
        
        return image_info