# llm/agents/base.py
from abc import ABC, abstractmethod
from typing import List

class BaseAgent(ABC):
    """Интерфейс для агентов с масштабируемыми свойствами"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Имя агента (уникальное)"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Описание компетенций агента"""
        pass
    
    @property
    @abstractmethod
    def keywords(self) -> List[str]:
        """Ключевые слова для роутинга"""
        pass
    
    @abstractmethod
    async def process_query(self, user_query: str) -> str:
        """Основной метод обработки (реализуется в подклассах)"""
        pass