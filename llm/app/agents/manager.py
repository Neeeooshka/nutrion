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
    
    def _detect_agent_type(self, query: str) -> str:  # sync
        query_lower = query.lower()
        nutrition_keywords = ["питан", "калор", "рацион", "белк", "жир", "углевод", "бад", "протеин", "bcaa", "креатин", "продукт", "есть после", "на ночь", "утром", "днем"]
        planning_keywords = ["тренир", "программ", "план", "расход энерги", "пропуск", "составь", "распиш", "зал", "функциональн"]
        if any(kw in query_lower for kw in nutrition_keywords):
            return "nutrition"
        elif any(kw in query_lower for kw in planning_keywords):
            return "planning"
        return "simple"