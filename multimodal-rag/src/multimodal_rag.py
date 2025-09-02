from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import logging
from dataclasses import dataclass

# 안전한 import with 폴백
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    try:
        from langchain.embeddings import HuggingFaceEmbeddings
    except ImportError:
        HuggingFaceEmbeddings = None

try:
    from langchain_community.vectorstores import Chroma
except ImportError:
    try:
        from langchain.vectorstores import Chroma
    except ImportError:
        Chroma = None

try:
    from langchain_ollama import ChatOllama
except ImportError:
    try:
        from langchain.llms import Ollama as ChatOllama
    except ImportError:
        ChatOllama = None

try:
    from langchain.schema import Document
except ImportError:
    try:
        from langchain_core.documents import Document
    except ImportError:
        Document = None

try:
    from langchain.prompts import PromptTemplate
except ImportError:
    try:
        from langchain_core.prompts import PromptTemplate
    except ImportError:
        PromptTemplate = None

from .pdf_processor import PDFProcessor
from .image_analyzer import ImageAnalyzer

@dataclass
class SearchResult:
    """검색 결과 데이터 클래스"""
    answer: str
    sources: List[Document]
    confidence: float
    processing_time: float

class MultimodalRAG:
    """멀티모달 RAG 시스템 핵심 클래스"""
    
    def __init__(
        self, 
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model: str = "llama2",
        vision_model: str = "llava",
        base_url: str = "http://localhost:11434"
    ):
        self.logger = logging.getLogger(__name__)
        
        # 의존성 확인
        self._check_dependencies()
        
        # 컴포넌트 초기화
        if HuggingFaceEmbeddings:
            self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        else:
            raise ImportError("HuggingFaceEmbeddings를 import할 수 없습니다. langchain_community 또는 langchain을 설치하세요.")
        
        if ChatOllama:
            self.llm = ChatOllama(
                model=llm_model,
                temperature=0,
                base_url=base_url
            )
        else:
            raise ImportError("ChatOllama를 import할 수 없습니다. langchain_ollama를 설치하세요.")
        
        # 프로세서들
        self.pdf_processor = PDFProcessor()
        self.image_analyzer = ImageAnalyzer(vision_model)
        
        # 상태
        self.vectorstore: Optional[Chroma] = None
        self.text_docs: List[Document] = []
        self.image_docs: List[Document] = []
        self.is_ready = False
    
    def _check_dependencies(self) -> None:
        """필수 의존성 확인"""
        missing_deps = []
        
        if not HuggingFaceEmbeddings:
            missing_deps.append("HuggingFaceEmbeddings (langchain_community 또는 langchain)")
        if not Chroma:
            missing_deps.append("Chroma (langchain_community 또는 langchain)")
        if not Document:
            missing_deps.append("Document (langchain 또는 langchain_core)")
        if not PromptTemplate:
            missing_deps.append("PromptTemplate (langchain 또는 langchain_core)")
        
        if missing_deps:
            deps_str = ", ".join(missing_deps)
            raise ImportError(f"다음 의존성들을 import할 수 없습니다: {deps_str}")
            
        self.logger.info("모든 의존성 확인 완료")
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 파일을 처리하고 벡터 저장소 생성"""
        try:
            self.logger.info(f"Processing PDF: {pdf_path}")
            
            # 1. 텍스트 추출
            self.text_docs = self.pdf_processor.extract_text_chunks(pdf_path)
            
            # 2. 이미지 추출 및 분석
            images_info = self.pdf_processor.extract_images(pdf_path)
            self.image_docs = []
            
            for img_info in images_info:
                description = self.image_analyzer.analyze_image(img_info['path'])
                
                image_doc = Document(
                    page_content=f"[이미지 {img_info['page']}페이지] {description}",
                    metadata={
                        "source": pdf_path,
                        "page": img_info['page'],
                        "type": "image",
                        "image_path": img_info['path'],
                        "filename": img_info['filename']
                    }
                )
                self.image_docs.append(image_doc)
            
            # 3. 벡터 저장소 생성
            all_docs = self.text_docs + self.image_docs
            if all_docs:
                self.vectorstore = Chroma.from_documents(
                    documents=all_docs,
                    embedding=self.embeddings
                )
                self.is_ready = True
            
            return {
                "success": True,
                "text_chunks": len(self.text_docs),
                "images": len(self.image_docs),
                "total_docs": len(all_docs)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """멀티모달 검색"""
        if not self.is_ready or not self.vectorstore:
            raise ValueError("시스템이 준비되지 않았습니다. 먼저 문서를 추가하세요.")
        
        return self.vectorstore.similarity_search(query, k=k)
    
    def answer_question(self, question: str, k: int = 3) -> SearchResult:
        """질문에 대한 답변 생성"""
        import time
        start_time = time.time()
        
        try:
            # 검색
            relevant_docs = self.similarity_search(question, k=k)
            
            # 컨텍스트 구성
            context_parts = []
            text_context = []
            image_context = []
            
            for doc in relevant_docs:
                if doc.metadata.get("type") == "image":
                    image_context.append(doc.page_content)
                else:
                    text_context.append(doc.page_content)
            
            if text_context:
                context_parts.append("**텍스트 정보:**\n" + "\n\n".join(text_context))
            if image_context:
                context_parts.append("**이미지 정보:**\n" + "\n\n".join(image_context))
            
            full_context = "\n\n".join(context_parts)
            
            # 프롬프트 생성 및 LLM 호출
            answer = self._generate_answer(question, full_context)
            
            # 신뢰도 계산 (간단한 버전)
            confidence = self._calculate_confidence(relevant_docs, question)
            
            processing_time = time.time() - start_time
            
            return SearchResult(
                answer=answer,
                sources=relevant_docs,
                confidence=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Error answering question: {str(e)}")
            raise
    
    def _generate_answer(self, question: str, context: str) -> str:
        """LLM으로 답변 생성"""
        prompt_template = """
        다음 정보를 바탕으로 질문에 답해주세요.
        텍스트와 이미지 정보를 모두 고려해서 종합적으로 답변해주세요.
        
        컨텍스트:
        {context}
        
        질문: {question}
        
        답변:
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        formatted_prompt = prompt.format(context=context, question=question)
        response = self.llm.invoke(formatted_prompt)
        
        return response.content
    
    def _calculate_confidence(self, docs: List[Document], question: str) -> float:
        """답변의 신뢰도 계산 (간단한 버전)"""
        if not docs:
            return 0.0
        
        # 검색된 문서 수와 내용 길이 기반으로 간단한 신뢰도 계산
        doc_count_score = min(len(docs) / 3.0, 1.0)  # 최대 3개 문서에서 1.0
        
        avg_length = sum(len(doc.page_content) for doc in docs) / len(docs)
        length_score = min(avg_length / 500.0, 1.0)  # 평균 500자에서 1.0
        
        return (doc_count_score + length_score) / 2.0
    
    def get_status(self) -> Dict[str, Any]:
        """시스템 상태 정보 반환"""
        return {
            "ready": self.is_ready,
            "text_documents": len(self.text_docs),
            "image_documents": len(self.image_docs),
            "total_documents": len(self.text_docs) + len(self.image_docs),
            "vectorstore_exists": self.vectorstore is not None
        }
    
    def add_text_document(self, file_path: str) -> None:
        """텍스트 문서 추가"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            doc = Document(
                page_content=content,
                metadata={
                    "source": str(path),
                    "type": "text",
                    "filename": path.name
                }
            )
            
            self.text_docs.append(doc)
            self._update_vectorstore()
            self.logger.info(f"텍스트 문서 추가됨: {path.name}")
            
        except Exception as e:
            self.logger.error(f"텍스트 문서 추가 오류: {str(e)}")
            raise
    
    def add_pdf_document(self, file_path: str) -> None:
        """PDF 문서 추가"""
        result = self.process_pdf(file_path)
        if not result["success"]:
            raise Exception(f"PDF 처리 실패: {result.get('error', 'Unknown error')}")
    
    def add_image_document(self, file_path: str) -> None:
        """이미지 문서 추가"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
            # 이미지 분석
            description = self.image_analyzer.analyze_image(str(path))
            
            doc = Document(
                page_content=f"[이미지] {description}",
                metadata={
                    "source": str(path),
                    "type": "image",
                    "filename": path.name,
                    "image_path": str(path)
                }
            )
            
            self.image_docs.append(doc)
            self._update_vectorstore()
            self.logger.info(f"이미지 문서 추가됨: {path.name}")
            
        except Exception as e:
            self.logger.error(f"이미지 문서 추가 오류: {str(e)}")
            raise
    
    def add_documents(self, file_paths: List[str]) -> None:
        """여러 문서 일괄 추가"""
        for file_path in file_paths:
            path = Path(file_path)
            suffix = path.suffix.lower()
            
            try:
                if suffix == '.pdf':
                    self.add_pdf_document(file_path)
                elif suffix in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                    self.add_image_document(file_path)
                elif suffix in ['.txt', '.md']:
                    self.add_text_document(file_path)
                else:
                    self.logger.warning(f"지원하지 않는 파일 형식: {file_path}")
                    raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}")
            except Exception as e:
                self.logger.error(f"파일 처리 실패 {file_path}: {str(e)}")
                raise
    
    def search(self, query: str, top_k: int = 3) -> SearchResult:
        """검색 및 답변 생성"""
        return self.answer_question(query, k=top_k)
    
    def _update_vectorstore(self) -> None:
        """벡터 저장소 업데이트"""
        all_docs = self.text_docs + self.image_docs
        if all_docs:
            if self.vectorstore is None:
                self.vectorstore = Chroma.from_documents(
                    documents=all_docs,
                    embedding=self.embeddings
                )
            else:
                # 새 문서만 추가 (실제로는 전체 재구성)
                self.vectorstore = Chroma.from_documents(
                    documents=all_docs,
                    embedding=self.embeddings
                )
            self.is_ready = True