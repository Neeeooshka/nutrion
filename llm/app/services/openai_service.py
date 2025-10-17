import httpx
import logging
from .llm_service import BaseLLMService

class OpenAIService(BaseLLMService):
    """Сервис для работы с OpenAI API"""
    
    def __init__(self):
        self.client = os.getenv("OPEN_AI_HOST")
        self._is_available = True
        self.headers = {"X-API-Key": INTERNAL_API_KEY, "Content-Type": "application/json"}
        self.logger = logging.getLogger("nutrition-llm")
    
    async def ask(self, prompt: str, context: str = "") -> dict:
        """Запрос к OpenAI"""
        try:
            
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{LLM_URL}/ask",
                    json={"prompt": prompt, "context": context},
                    headers=self.headers
                )
                
                resp.raise_for_status()
                
                return resp
            
        except Exception as e:
            # Проверяем квоту
            if any(keyword in str(e).lower() for keyword in ["quota", "429", "insufficient_quota"]):
                self._is_available = False
            
            self.logger.exception(e)
            
            return self._format_error(str(e))
    
    async def is_available(self) -> bool:
        """Проверка доступности OpenAI"""
        return self._is_available
    
    async def health_check(self) -> bool:
        """Проверка здоровья OpenAI"""
        return true