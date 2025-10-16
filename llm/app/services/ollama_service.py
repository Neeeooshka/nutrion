import os
import ollama
import asyncio
import logging
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
            logger = logging.getLogger("nutrition-llm")
            full_prompt = f"Контекст: {context}\nВопрос: {prompt}"
            def run_in_thread():
                logger.info("Вошли в потоковую функцию")
                text = ""
                stream = self.client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": full_prompt},
                    ],
                    options={
                        "temperature": TEMPERATURE,
                        "num_predict": MAX_TOKENS
                    },
                    stream=True
                )
                logger.info("начинаем стрим")
                for chunk in stream:
                    logger.info(f"ответ от бота: {chunk["message"]["content"]}")
                    if "message" in chunk and "content" in chunk["message"]:
                        text += chunk["message"]["content"]
                return text
            
            ai_text = await asyncio.to_thread(run_in_thread)
            
            return self._format_response(ai_text, self.model)
            
        except Exception as e:
            logger.exception(e)
            return self._format_error(str(e))
    
    async def is_available(self) -> bool:
        """Проверка доступности Ollama"""
        return await self.health_check()
    
    async def health_check(self) -> bool:
        """Упрощенная проверка здоровья Ollama"""
        logger = logging.getLogger("nutrition-llm")
        
        try:
            # Просто пытаемся использовать модель
            test_response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                options={'num_predict': 5}
            )
            
            # Если дошли сюда - модель работает
            self._is_available = True
            logger.info(f"✅ Модель {self.model} доступна")
            return True
            
        except Exception as e:
            logger.warning(f"❌ Модель {self.model} недоступна: {e}")
            self._is_available = False
            return False