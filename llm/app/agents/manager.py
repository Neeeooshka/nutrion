from typing import Dict, Any
from services.llm_orchestrator import LLMOrchestrator

class AgentManager:
    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.orchestrator = llm_orchestrator
        self.agents = self._initialize_agents()
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Инициализация всех агентов"""
        from .nutrition import NutritionAgent
        from .planning import PlanningAgent
        
        return {
            "nutrition": NutritionAgent(self.orchestrator),
            "planning": PlanningAgent(self.orchestrator),
            "simple": self.orchestrator  # Простой агент как fallback
        }
    
    async def route_request(self, user_query: str, agent_type: str = "auto") -> str:
        """Маршрутизация запроса к нужному агенту"""
        # Автоматическое определение типа агента
        if agent_type == "auto":
            agent_type = await self._detect_agent_type(user_query)
        
        agent = self.agents.get(agent_type, self.agents["simple"])
        return await agent.process_query(user_query)
    
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
        return response.strip().lower()