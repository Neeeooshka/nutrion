# llm/agents/manager.py
from typing import Dict, Any
import logging
from services.llm_orchestrator import LLMOrchestrator
from config import AGENT_CLASSES  # import

# Настройка логгера
logger = logging.getLogger("nutrition-llm")

class AgentManager:
    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.orchestrator = llm_orchestrator
        self.registry: Dict[str, Any] = self._register_agents()
    
    def _register_agents(self) -> Dict[str, Any]:
        """Автоматическая регистрация агентов из config"""
        from services.ollama_service import OllamaService
        import os
        
        fast_llm = OllamaService(model=os.getenv("OLLAMA_FAST_MODEL"))
        quality_llm = OllamaService(model=os.getenv("OLLAMA_MODEL"))
        
        registry = {}
        for agent_cls in AGENT_CLASSES:
            agent = agent_cls(fast_llm, quality_llm) if agent_cls.name != "simple" else agent_cls(self.orchestrator)
            registry[agent.name] = agent
            logger.info(f"Registered agent: {agent.name} - {agent.description}")
        
        return registry
    
    def _detect_agent_type(self, query: str) -> str:
        """Определение типа по keywords из registry"""
        query_lower = query.lower()
        for agent in self.registry.values():
            if any(kw in query_lower for kw in agent.keywords):
                return agent.name
        return "simple"  # fallback
    
    async def route_request(self, user_query: str, agent_type: str = "auto") -> dict:
        """Маршрутизация с использованием registry"""
        if agent_type == "auto":
            agent_type = self._detect_agent_type(user_query)
        
        agent = self.registry.get(agent_type, self.registry["simple"])
        
        agent_name = agent.name
        logger.info(f"🔄 Передаю управление агенту: {agent_name} (тип: {agent_type})")
        logger.info(f"📝 Запрос: {user_query}")
        
        answer = await agent.process_query(user_query)
        
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
    
    # Убрал _detect_agent_type async, так как теперь sync (no LLM)