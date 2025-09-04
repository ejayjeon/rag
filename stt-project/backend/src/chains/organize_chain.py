# ================================
# 5. LangChain 체인들 (src/chains/)
# ================================

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from typing import Dict, Any

class StoryOrganizingChain:
    """스토리 구조화 체인"""
    
    def __init__(self, llm_model: str = "llama2"):
        self.llm = ChatOllama(model=llm_model, temperature=0)
        self.chain = self._create_chain()
    
    def _create_chain(self) -> LLMChain:
        prompt = PromptTemplate(
            template="""다음 텍스트를 논리적인 구조로 정리해주세요.

                        구조화 규칙:
                        1. 주제나 시간순으로 문단 나누기
                        2. 각 문단에 적절한 제목 부여
                        3. 핵심 문장과 부연설명 구분
                        4. JSON 형태로 결과 반환

                        반환 형식:
                        {{
                            "title": "전체 제목",
                            "summary": "한 줄 요약",
                            "sections": [
                                {{
                                    "section_title": "섹션 제목",
                                    "content": "섹션 내용",
                                    "key_points": ["핵심 포인트1", "핵심 포인트2"]
                                }}
                            ]
                        }}

                        텍스트: {text}

                        구조화 결과:""",
            input_variables=["text"]
        )
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def organize(self, text: str) -> Dict[str, Any]:
        """스토리 구조화 실행"""
        try:
            result = self.chain.run(text=text)
            # JSON 파싱 시도
            import json
            organized = json.loads(result)
            return organized
        except json.JSONDecodeError:
            # JSON 파싱 실패시 기본 구조 반환
            return {
                "title": "사용자 스토리",
                "summary": text[:100] + "..." if len(text) > 100 else text,
                "sections": [
                    {
                        "section_title": "메인 스토리",
                        "content": text,
                        "key_points": []
                    }
                ]
            }