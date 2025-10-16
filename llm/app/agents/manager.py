from typing import Dict, Any
import logging
from services.llm_orchestrator import LLMOrchestrator

# Настройка логгера
logger = logging.getLogger("nutrition-llm")

class AgentManager:
    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.orchestrator = llm_orchestrator
        self.agents = self._initialize_agents()
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Инициализация всех агентов с двумя LLM сервисами"""
        from .nutrition import NutritionAgent
        from .planning import PlanningAgent
        from .simple import SimpleAgent
        
        # Создаем отдельные сервисы для быстрых и качественных моделей
        from services.ollama_service import OllamaService
        import os
        
        fast_llm = OllamaService(model=os.getenv("OLLAMA_FAST_MODEL"))
        quality_llm = OllamaService(model=os.getenv("OLLAMA_MODEL"))
        
        return {
            "nutrition": NutritionAgent(fast_llm, quality_llm),
            "planning": PlanningAgent(fast_llm, quality_llm),
            "simple": SimpleAgent(self.orchestrator)  # Оставляем как есть для простых запросов
        }
    
    async def route_request(self, user_query: str, agent_type: str = "auto") -> dict:
        """Маршрутизация запроса к нужному агенту с логированием"""
        # Автоматическое определение типа агента
        if agent_type == "auto":
            agent_type = await self._detect_agent_type(user_query)
        
        agent = self.agents.get(agent_type, self.agents["simple"])
        
        # Логируем передачу управления агенту
        agent_name = agent.__class__.__name__
        logger.info(f"🔄 Передаю управление агенту: {agent_name} (тип: {agent_type})")
        logger.info(f"📝 Запрос: {user_query}")
        
        answer = await agent.process_query(user_query)
        
        # Логируем завершение работы агента
        logger.info(f"✅ Агент {agent_name} завершил обработку")
        
        if answer.startswith("Ошибка:"):
            logger.warning(f"❌ {answer}")
        
        return {
            "answer": "" if answer.startswith("Ошибка:") else answer,
            "agent_type": agent_type,
            "agent_name": agent_name,
            "status": "error" if answer.startswith("Ошибка:") else "success",
            "error": answer if answer.startswith("Ошибка:") else ""
        }
    
    async def _detect_agent_type(self, query: str) -> str:
        """Автоматическое определение типа агента для запроса"""
        prompt = f"""
        Определи тип запроса пользователя:
        "{query}"
        
        Варианты:
        - nutrition: вопросы по питанию, калориям, БЖУ, диетам
        - planning: создание планов, программ, многошаговые цели  
        - simple: простые вопросы, общие консультации
        
        Верни только одно слово: nutrition, planning или simple
        """
        
        response = await self.orchestrator.ask(prompt)
        
        # Извлекаем текст из словаря
        if isinstance(response, dict) and 'answer' in response:
            agent_type = response['answer'].strip().lower()
        elif isinstance(response, str):
            agent_type = response.strip().lower()
        else:
            agent_type = "simple"  # fallback
        
        logger.info(f"🎯 Определен тип агента: {agent_type} для запроса: {query}")
        return agent_type