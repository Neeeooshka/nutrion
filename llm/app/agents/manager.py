# llm/agents/manager.py
from typing import Dict, Any
import logging
from services.llm_orchestrator import LLMOrchestrator
from config import AGENT_CLASSES

logger = logging.getLogger("nutrition-llm")

class AgentManager:
    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.orchestrator = llm_orchestrator
        self.registry: Dict[str, Any] = self._register_agents()
    
    def _register_agents(self) -> Dict[str, Any]:
        from services.ollama_service import OllamaService
        import os
        
        fast_llm = OllamaService(model=os.getenv("OLLAMA_FAST_MODEL"))
        quality_llm = OllamaService(model=os.getenv("OLLAMA_MODEL"))
        
        registry = {}
        for agent_cls in AGENT_CLASSES:
            if agent_cls._NAME == "simple":
                agent = agent_cls(llm_orchestrator=self.orchestrator)
            else:
                agent = agent_cls(fast_llm, quality_llm, llm_orchestrator=self.orchestrator)
            registry[agent_cls._NAME] = agent
            logger.info(f"Registered agent: {agent_cls._NAME} - {agent_cls._DESCRIPTION}")
        
        return registry
    
    def _detect_agent_type(self, query: str) -> str:
        query_lower = query.lower()
        # Проверяем nutrition первым для точности
        nutrition_agent = self.registry.get("nutrition")
        if nutrition_agent and any(kw in query_lower for kw in nutrition_agent.__class__._KEYWORDS):
            return "nutrition"
        # Затем planning
        planning_agent = self.registry.get("planning")
        if planning_agent and any(kw in query_lower for kw in planning_agent.__class__._KEYWORDS):
            return "planning"
        # Simple как fallback
        return "simple"
    
    async def route_request(self, user_query: str, agent_type: str = "auto") -> dict:
        if agent_type == "auto":
            agent_type = self._detect_agent_type(user_query)
        
        agent = self.registry.get(agent_type, self.registry["simple"])
        
        agent_name = agent.__class__._NAME
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