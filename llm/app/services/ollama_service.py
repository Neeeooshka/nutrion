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
        """Проверка здоровья Ollama с расширенной диагностикой"""
        import logging
        logger = logging.getLogger("nutrition-llm")
        
        logger.info(f"🩺 Начинаем диагностику Ollama...")
        logger.info(f"📍 OLLAMA_HOST: {OLLAMA_HOST}")
        logger.info(f"📍 OLLAMA_MODEL: {OLLAMA_MODEL}")
        
        try:
            # Проверка №1: HTTP доступность
            import requests
            logger.info("🔍 Проверяем HTTP доступность...")
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
            logger.info(f"📡 HTTP статус: {response.status_code}")
            
            # Проверка №2: Через ollama client
            logger.info("🔍 Проверяем через ollama client...")
            models = self.client.list()
            if 'models' in models:
                available_models = [m['name'] for m in models['models']]
            else:
                available_models = []
                logger.warning(f"❌ Ключ 'models' не найден в ответе: {models}")
                
            logger.info(f"📋 Доступные модели: {available_models}")
            
            # Проверка №3: Доступность конкретной модели
            model_available = self.model in available_models
            logger.info(f"🔍 Модель {self.model} доступна: {model_available}")
            
            self._is_available = model_available
            return model_available
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"🔌 Ошибка подключения к Ollama: {e}")
            logger.error("💡 Проверьте:")
            logger.error("   - Запущен ли контейнер Ollama")
            logger.error("   - Правильно ли настроена сеть Docker")
            logger.error("   - Доступен ли Ollama по адресу: " + OLLAMA_HOST)
            return False
            
        except requests.exceptions.Timeout as e:
            logger.error(f"⏰ Таймаут подключения к Ollama: {e}")
            return False
            
        except Exception as e:
            logger.error(f"💥 Неожиданная ошибка: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False