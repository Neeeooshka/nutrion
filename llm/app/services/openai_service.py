import os
from openai import OpenAI
from .llm_service import BaseLLMService
from config import OPENAI_MODEL, SYSTEM_PROMPT, TEMPERATURE, MAX_TOKENS

class OpenAIService(BaseLLMService):
    """Сервис для работы с OpenAI API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = OPENAI_MODEL
        self._is_available = True
    
    async def ask(self, prompt: str, context: str = "") -> dict:
        """Запрос к OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"{context}\n{prompt}"}
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )
            
            ai_text = response.choices[0].message.content
            return self._format_response(ai_text, self.model)
            
        except Exception as e:
            # Проверяем квоту
            if any(keyword in str(e).lower() for keyword in ["quota", "429", "insufficient_quota"]):
                self._is_available = False
            
            return self._format_error(str(e))
    
    async def is_available(self) -> bool:
        """Проверка доступности OpenAI"""
        return self._is_available
    
    async def health_check(self) -> bool:
        """Проверка здоровья OpenAI"""
        try:
            self.client.models.list()
            self._is_available = True
            return True
        except:
            self._is_available = False
            return False