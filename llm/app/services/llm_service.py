from abc import ABC, abstractmethod
import logging

logger = logging.getLogger("nutrition-llm")

class BaseLLMService(ABC):
    """Абстрактный базовый класс для всех LLM провайдеров"""
    
    @abstractmethod
    async def ask(self, prompt: str, context: str = "") -> dict:
        """Основной метод для запросов"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Проверка доступности сервиса"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Проверка здоровья сервиса"""
        pass
    
    def _format_response(self, answer: str, model: str) -> dict:
        """Форматирование успешного ответа"""
        return {
            "answer": answer,
            "provider": self.__class__.__name__.replace("Service", "").lower(),
            "model": model
        }
    
    def _format_error(self, error: str) -> dict:
        """Форматирование ошибки"""
        return {
            "error": error,
            "provider": self.__class__.__name__.replace("Service", "").lower()
        }