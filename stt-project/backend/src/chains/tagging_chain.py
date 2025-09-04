# ================================
# 5. LangChain 체인들 (src/chains/)
# ================================

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from typing import List


class HashtagExtractionChain:
    """해시태그 추출 체인"""
    
    def __init__(self, llm_model: str = "llama2"):
        self.llm = ChatOllama(model=llm_model, temperature=0.3)
        self.chain = self._create_chain()
    
    def _create_chain(self) -> LLMChain:
        prompt = PromptTemplate(
            template="""다음 스토리에서 핵심 키워드를 추출하여 해시태그로 만들어주세요.

                        추출 기준:
                        - 주요 인물, 장소, 사건
                        - 감정이나 분위기
                        - 중요한 개념이나 주제  
                        - 특별한 의미가 있는 단어
                        - SNS에서 사용할만한 키워드

                        주의사항:
                        - 3-8개 정도로 선별
                        - # 기호 포함
                        - 한국어로 작성
                        - 너무 일반적인 단어는 제외

                        스토리: {story}

                        해시태그 목록:""",
            input_variables=["story"]
        )
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def extract_tags(self, story: str) -> List[str]:
        """해시태그 추출 실행"""
        result = self.chain.run(story=story)
        
        # 해시태그 추출 및 정리
        import re
        tags = re.findall(r'#\w+', result)
        
        # 중복 제거 및 정리
        unique_tags = list(dict.fromkeys(tags))
        
        return unique_tags[:8]  # 최대 8개