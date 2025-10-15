import os
import ollama
from .llm_service import BaseLLMService
from config import OLLAMA_MODEL, SYSTEM_PROMPT, TEMPERATURE, MAX_TOKENS

OLLAMA_HOST = os.getenv("OLLAMA_HOST")

class OllamaService(BaseLLMService):
    """Сервис для работы с локальной Ollama"""
    
    def __init__(self):
        self.client = ollama.Client(host=OLLAMA_HOST)
        self.model = OLLAMA_MODEL
        self._is_available = False
    
    async def ask(self, prompt: str, context: str = "") -> dict:
        """Запрос к Ollama"""
        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\nКонтекст: {context}\n\nВопрос: {prompt}"
            
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": full_prompt}],
                options={
                    'temperature': TEMPERATURE,
                    'num_predict': MAX_TOKENS
                }
            )
            
            ai_text = response['message']['content']
            return self._format_response(ai_text, self.model)
            
        except Exception as e:
            return self._format_error(str(e))
    
    async def is_available(self) -> bool:
        """Проверка доступности Ollama"""
        return await self.health_check()
    
    async def health_check(self) -> bool:
        """Проверка здоровья Ollama"""
        try:
            models = self.client.list()
            available_models = [m['name'] for m in models['models']]
            
            if self.model in available_models:
                self._is_available = True
                return True
            else:
                self._is_available = False
                return False
                
        except Exception:
            self._is_available = False
            return False