# ================================
# 5. LangChain 체인들 (src/chains/)
# ================================

from typing import Dict, Any
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama

class TextCleaningChain:
    """습관어 제거 및 텍스트 정리 체인"""
    
    def __init__(self, llm_model: str = "llama2"):
        self.llm = ChatOllama(model=llm_model, temperature=0.5)
        self.chain = self._create_chain()
    
    def _create_chain(self) -> LLMChain:
        prompt = PromptTemplate(
            template="""다음 음성 인식 텍스트를 깔끔하게 정리해주세요.
                        제거할 요소들:
                        - 습관어: '음...', '어...', '그...', '뭐지', '그게' 등
                        - 불필요한 반복: 같은 단어나 구문의 반복
                        - 망설임 표현: '아니', '잠깐', '어떻게 말하지' 등  
                        - 의미없는 연결어: 문맥상 불필요한 '그래서', '그리고' 등

                        정리 원칙:
                        1. 원래 의미와 의도는 보존
                        2. 자연스러운 문장으로 재구성
                        3. 중요한 내용은 절대 삭제하지 말 것
                        4. 한국어 문법에 맞게 수정

                        원본 텍스트: {text}

                        정리된 텍스트:""",
            input_variables=["text"]
        )
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def clean(self, text: str) -> Dict[str, Any]:
        """텍스트 정리 실행"""
        result = self.chain.run(text=text)
        
        # 제거된 습관어 추출 (간단한 휴리스틱)
        filler_words = ["음", "어", "그", "뭐지", "그게", "아니", "잠깐"]
        removed_fillers = [word for word in filler_words if word in text and word not in result]
        
        return {
            "cleaned_text": result.strip(),
            "removed_fillers": removed_fillers,
            "reduction_rate": 1 - len(result) / len(text)
        }