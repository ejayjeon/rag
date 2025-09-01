"""
RAG 시스템의 핵심 로직
"""
import os
from pathlib import Path
from typing import List, Optional

# LangChain 최신 버전 import 경로
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# OpenAI 사용하는 경우
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

# Ollama 사용하는 경우
try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None


class SimpleRAG:
    def __init__(self, persist_directory: str = "./vectorstore"):
        load_dotenv()
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = None
        self.qa_chain = None

    def load_documents(self, file_paths: List[str]) -> List:
        """문서들을 로드하고 청크로 분할"""
        documents = []
        
        for file_path in file_paths:
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                print(f"지원하지 않는 파일 형식: {file_path}")
                continue
                
            docs = loader.load()
            documents.extend(docs)
        
        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        return text_splitter.split_documents(documents)

    def create_vectorstore(self, documents: List) -> None:
        """벡터 저장소 생성"""
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        self.vectorstore.persist()

    def load_vectorstore(self) -> None:
        """기존 벡터 저장소 로드"""
        if Path(self.persist_directory).exists():
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            raise FileNotFoundError("벡터 저장소가 존재하지 않습니다.")

    def setup_qa_chain(self, model_type: str = "openai") -> None:
        """QA 체인 설정"""
        if not self.vectorstore:
            raise ValueError("먼저 벡터 저장소를 생성하거나 로드해야 합니다.")

        # LLM 선택
        if model_type == "openai" and ChatOpenAI:
            llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0
            )
        elif model_type == "ollama" and ChatOllama:
            llm = ChatOllama(
                model="llama2",
                temperature=0
            )
        else:
            raise ValueError(f"지원하지 않는 모델 타입: {model_type}")

        # 프롬프트 템플릿
        prompt_template = """
        다음 컨텍스트를 바탕으로 질문에 정확하게 답해주세요.
        모르는 내용이면 "주어진 문서에서 해당 정보를 찾을 수 없습니다"라고 답하세요.

        컨텍스트:
        {context}

        질문: {question}

        답변:
        """

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        # QA 체인 생성
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )

    def ask_question(self, question: str) -> dict:
        """질문하기"""
        if not self.qa_chain:
            raise ValueError("먼저 QA 체인을 설정해야 합니다.")
        
        result = self.qa_chain.invoke({"query": question})
        
        return {
            "answer": result["result"],
            "source_documents": result["source_documents"]
        }