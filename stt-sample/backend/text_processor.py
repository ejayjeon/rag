# text_processor.py
import re
from typing import List, Dict, Optional
from collections import Counter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document

class TextProcessor:
    def __init__(self, openai_api_key: str):
        """
        Initialize text processor with LangChain and OpenAI
        
        Args:
            openai_api_key: OpenAI API key
        """
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o-mini",
            temperature=0.3
        )
        
        # 한국어 습관어 패턴
        self.korean_fillers = [
            r'\b(음+|어+|그+|아+|오+)\b',
            r'\b(있잖아|거든|이제|뭐|막|좀|약간)\b',
            r'\b(그니까|그러니까|그래서|그래가지고)\b',
            r'\b(뭐랄까|뭐지|어떻게|왜냐하면|왜냐면)\b'
        ]
        
        # 영어 습관어 패턴
        self.english_fillers = [
            r'\b(um+|uh+|ah+|oh+|hmm+)\b',
            r'\b(like|you know|I mean|basically|actually|literally)\b',
            r'\b(sort of|kind of|so to speak)\b',
            r'\b(well|so|anyway|right)\b'
        ]
        
    def detect_language(self, text: str) -> str:
        """
        Detect primary language of text
        
        Args:
            text: Input text
            
        Returns:
            Language code ('ko', 'en', or 'mixed')
        """
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        total_chars = korean_chars + english_chars
        if total_chars == 0:
            return 'unknown'
        
        korean_ratio = korean_chars / total_chars
        
        if korean_ratio > 0.7:
            return 'ko'
        elif korean_ratio < 0.3:
            return 'en'
        else:
            return 'mixed'
    
    def remove_fillers(self, text: str, language: Optional[str] = None) -> Dict:
        """
        Remove filler words and hesitations from text
        
        Args:
            text: Input text
            language: Language code or None for auto-detect
            
        Returns:
            Dictionary with cleaned text and statistics
        """
        if language is None:
            language = self.detect_language(text)
        
        original_text = text
        removed_fillers = []
        
        # Select filler patterns based on language
        if language == 'ko':
            filler_patterns = self.korean_fillers
        elif language == 'en':
            filler_patterns = self.english_fillers
        else:
            filler_patterns = self.korean_fillers + self.english_fillers
        
        # Remove fillers and track what was removed
        for pattern in filler_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            removed_fillers.extend(matches)
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up extra spaces and punctuation
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        text = text.strip()
        
        # Calculate statistics
        filler_counts = Counter(removed_fillers)
        
        return {
            'original': original_text,
            'cleaned': text,
            'removed_fillers': dict(filler_counts),
            'total_fillers': len(removed_fillers),
            'reduction_ratio': 1 - (len(text) / len(original_text)) if original_text else 0,
            'language': language
        }
    
    def clean_repetitions(self, text: str) -> str:
        """
        Remove word/phrase repetitions
        
        Args:
            text: Input text
            
        Returns:
            Text with repetitions removed
        """
        # Remove immediate word repetitions
        words = text.split()
        cleaned_words = []
        
        for i, word in enumerate(words):
            if i == 0 or word.lower() != words[i-1].lower():
                cleaned_words.append(word)
        
        text = ' '.join(cleaned_words)
        
        # Remove phrase repetitions (2-3 word phrases)
        text = re.sub(r'\b(\w+\s+\w+)\s+\1\b', r'\1', text)
        text = re.sub(r'\b(\w+\s+\w+\s+\w+)\s+\1\b', r'\1', text)
        
        return text
    
    def summarize_text(self, text: str, 
                      summary_type: str = "comprehensive",
                      max_length: int = 500) -> Dict:
        """
        Summarize text using LangChain and OpenAI
        
        Args:
            text: Input text
            summary_type: Type of summary (comprehensive, bullet_points, key_points)
            max_length: Maximum length of summary
            
        Returns:
            Summary dictionary
        """
        # Clean text first
        cleaned_result = self.remove_fillers(text)
        cleaned_text = self.clean_repetitions(cleaned_result['cleaned'])
        
        # Create document for LangChain
        doc = Document(page_content=cleaned_text)
        
        # Choose prompt based on summary type
        if summary_type == "bullet_points":
            prompt_template = """다음 내용을 핵심 포인트 위주로 불릿 포인트 형식으로 요약해주세요:

{text}

요약 (최대 5개 포인트):"""
        elif summary_type == "key_points":
            prompt_template = """다음 내용에서 가장 중요한 핵심 메시지를 추출해주세요:

{text}

핵심 메시지:"""
        else:  # comprehensive
            prompt_template = """다음 내용을 종합적으로 요약해주세요. 중요한 정보는 모두 포함하되, 간결하게 정리해주세요:

{text}

요약:"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["text"]
        )
        
        # Split text if too long
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", ", ", " "]
        )
        
        docs = text_splitter.split_documents([doc])
        
        # Summarize
        if len(docs) == 1:
            # Simple summarization for short text
            summary = self.llm.invoke(
                prompt.format(text=cleaned_text)
            ).content
        else:
            # Map-reduce for longer text
            chain = load_summarize_chain(
                llm=self.llm,
                chain_type="map_reduce",
                map_prompt=prompt,
                combine_prompt=prompt
            )
            summary = chain.run(docs)
        
        return {
            'original_length': len(text),
            'cleaned_length': len(cleaned_text),
            'summary': summary,
            'summary_type': summary_type,
            'fillers_removed': cleaned_result['total_fillers'],
            'language': cleaned_result['language']
        }
    
    def extract_topics(self, text: str, num_topics: int = 5) -> List[str]:
        """
        Extract main topics from text using LLM
        
        Args:
            text: Input text
            num_topics: Number of topics to extract
            
        Returns:
            List of topics
        """
        prompt = f"""다음 텍스트에서 주요 주제/키워드를 {num_topics}개 추출해주세요.
각 주제는 한 단어 또는 짧은 구문으로 표현해주세요.

텍스트: {text}

주제 (콤마로 구분):"""
        
        response = self.llm.invoke(prompt).content
        topics = [topic.strip() for topic in response.split(',')]
        
        return topics[:num_topics]