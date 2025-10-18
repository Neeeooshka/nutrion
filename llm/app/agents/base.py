# llm/agents/base.py
from abc import ABC, abstractmethod
from typing import List

class BaseAgent(ABC):
    """Интерфейс для агентов с масштабируемыми свойствами"""
    
    _NAME: str  # class var, override in subclasses
    _DESCRIPTION: str
    _KEYWORDS: List[str]
    
    @abstractmethod
    async def process_query(self, user_query: str) -> str:
        """Основной метод обработки"""
        pass