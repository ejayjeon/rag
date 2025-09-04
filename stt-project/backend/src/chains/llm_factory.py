# ================================
# LLM Factory (src/chains/llm_factory.py)
# ================================

from typing import Any
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from ..core.config import Config, LLMProvider

class LLMFactory:
    """LLM 제공자에 따른 LLM 인스턴스 생성 팩토리"""
    
    @staticmethod
    def create_llm(provider: str = None, model: str = None, **kwargs) -> Any:
        """LLM 제공자에 따라 적절한 LLM 인스턴스 생성"""
        
        # provider가 명시되지 않으면 Config에서 가져오기
        if not provider:
            llm_config = Config.get_llm_config()
            provider = llm_config["provider"]
            model = model or llm_config["model"]
        
        # OpenAI 사용
        if provider.lower() == "openai":
            openai_kwargs = {
                "model": model or Config.OPENAI_MODEL,
                "temperature": kwargs.get("temperature", 0.5),
                "api_key": Config.OPENAI_API_KEY,
            }
            
            # 커스텀 base_url이 있다면 추가
            if Config.OPENAI_BASE_URL:
                openai_kwargs["base_url"] = Config.OPENAI_BASE_URL
                
            return ChatOpenAI(**openai_kwargs)
        
        # Ollama 사용 (기본값)
        else:
            ollama_kwargs = {
                "model": model or Config.OLLAMA_MODEL,
                "temperature": kwargs.get("temperature", 0.5),
                "base_url": Config.OLLAMA_BASE_URL,
            }
            
            return ChatOllama(**ollama_kwargs)
    
    @staticmethod
    def get_provider_info() -> dict:
        """현재 설정된 제공자 정보 반환"""
        llm_config = Config.get_llm_config()
        provider = llm_config["provider"]
        
        if provider == "openai":
            return {
                "provider": "OpenAI",
                "model": llm_config["model"],
                "api_key_configured": bool(llm_config["api_key"]),
                "status": "Ready" if llm_config["api_key"] else "API Key Required"
            }
        else:
            return {
                "provider": "Ollama",
                "model": llm_config["model"],
                "base_url": llm_config["base_url"],
                "status": "Ready" if Config.OLLAMA_BASE_URL else "Server Required"
            }