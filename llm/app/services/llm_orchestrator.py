import logging
from typing import Dict
from .openai_service import OpenAIService
from .ollama_service import OllamaService

logger = logging.getLogger("nutrition-llm")

class LLMOrchestrator:
    """
    Оркестратор для управления LLM провайдерами.
    Автоматически переключается между сервисами при ошибках.
    """
    
    def __init__(self):
        self.services: Dict[str, BaseLLMService] = {
            "openai": OpenAIService(),
            "ollama": OllamaService()
        }
        self.current_provider = "ollama"
        self.openai_errors_count = 0
        self.MAX_OPENAI_ERRORS = 3
    
    async def initialize(self):
        """Инициализация всех сервисов"""
        logger.info("🔧 Initializing LLM Orchestrator...")
        
        for name, service in self.services.items():
            is_available = await service.is_available()
            status = "✅" if is_available else "❌"
            logger.info(f"  {status} {name}: {'available' if is_available else 'unavailable'}")
    
    async def ask(self, prompt: str, context: str = "") -> dict:
        """Основной метод для запросов с автоматическим переключением"""
        logger.info(f"📨 Запрос. Текущий провайдер: {self.current_provider}")
        
        # Пробуем текущий провайдер
        current_service = self.services[self.current_provider]
        
        if await current_service.is_available():
            result = await current_service.ask(prompt, context)
            
            # Если успех от OpenAI - сбрасываем счетчик ошибок
            if self.current_provider == "openai" and "error" not in result:
                self.openai_errors_count = 0
            
            # Если ошибка - обрабатываем
            if "error" in result:
                return await self._handle_error(result, prompt, context)
            
            return result
        else:
            # Текущий провайдер недоступен, ищем альтернативу
            return await self._switch_provider_and_retry(prompt, context)
    
    async def _handle_error(self, error_result: dict, prompt: str, context: str) -> dict:
        """Обработка ошибок с автоматическим переключением"""
        provider = error_result["provider"]
        error_msg = error_result["error"]
        
        logger.warning(f"⚠️ Ошибка {provider}: {error_msg}")
        
        if provider == "openai":
            return await self._handle_openai_error(error_msg, prompt, context)
        elif provider == "ollama":
            return await self._handle_ollama_error(error_msg, prompt, context)
        
        return error_result
    
    async def _handle_openai_error(self, error: str, prompt: str, context: str) -> dict:
        """Обработка ошибок OpenAI"""
        self.openai_errors_count += 1
        
        # Проверяем квоту
        if any(keyword in str(error).lower() for keyword in ["quota", "429", "insufficient_quota"]):
            self.services["openai"]._is_available = False
            logger.error("💸 Закончилась квота OpenAI! Отключаем провайдер.")
        
        # Переключаемся на Ollama при частых ошибках
        if self.openai_errors_count >= self.MAX_OPENAI_ERRORS:
            if await self.services["ollama"].is_available():
                self.current_provider = "ollama"
                logger.info("🔄 Переключились на Ollama из-за ошибок OpenAI")
                return await self.services["ollama"].ask(prompt, context)
        
        return self.services["openai"]._format_error(error)
    
    async def _handle_ollama_error(self, error: str, prompt: str, context: str) -> dict:
        """Обработка ошибок Ollama"""
        logger.error(f"❌ Ошибка Ollama: {error}")
        
        # Пробуем вернуться к OpenAI
        if await self.services["openai"].is_available():
            self.current_provider = "openai"
            logger.info("🔄 Пробуем вернуться к OpenAI...")
            return await self.services["openai"].ask(prompt, context)
        
        return self.services["ollama"]._format_error(error)
    
    async def _switch_provider_and_retry(self, prompt: str, context: str) -> dict:
        """Переключение провайдера и повторная попытка"""
        for provider_name, service in self.services.items():
            if provider_name != self.current_provider and await service.is_available():
                self.current_provider = provider_name
                logger.info(f"🔄 Автоматическое переключение на {provider_name}")
                return await service.ask(prompt, context)
        
        # Все провайдеры недоступны
        return {"error": "Все LLM провайдеры недоступны", "provider": "none"}
    
    async def switch_provider(self, provider: str) -> bool:
        """Ручное переключение провайдера"""
        if provider in self.services and await self.services[provider].is_available():
            self.current_provider = provider
            logger.info(f"🔄 Ручное переключение на {provider}")
            return True
        return False
    
    async def health_check(self) -> dict:
        """Проверка здоровья всех сервисов"""
        health_status = {}
        
        for name, service in self.services.items():
            is_healthy = await service.health_check()
            health_status[name] = is_healthy
        
        overall_health = any(health_status.values())
        
        return {
            "status": "healthy" if overall_health else "unhealthy",
            "current_provider": self.current_provider,
            "services": health_status
        }
    
    def get_status(self) -> dict:
        """Получение статуса системы"""
        return {
            "current_provider": self.current_provider,
            "openai_errors_count": self.openai_errors_count,
            "max_openai_errors": self.MAX_OPENAI_ERRORS,
            "models": {
                "openai": self.services["openai"].model,
                "ollama": self.services["ollama"].model
            }
        }