# llm/agents/simple.py
from .base import BaseAgent
import logging

logger = logging.getLogger("nutrition-llm")

class SimpleAgent(BaseAgent):
    _NAME = "simple"
    _DESCRIPTION = "Агент для простых вопросов, общих консультаций, причин, рекомендаций."
    _KEYWORDS = ["причин", "рекомендац", "науч", "что будет если", "правда ли", "почему"]
    
    def __init__(self, llm_orchestrator, **kwargs):
        self.orchestrator = llm_orchestrator
    
    async def process_query(self, user_query: str) -> str:
        from config import SYSTEM_PROMPT
        prompt = f"{SYSTEM_PROMPT}\nUser: {user_query}"
        
        # Простые вопросы о калориях перенаправляем в nutrition
        if "калор" in user_query.lower():
            from agents.nutrition import NutritionAgent
            from services.ollama_service import OllamaService
            import os
            fast_llm = OllamaService(model=os.getenv("OLLAMA_FAST_MODEL"))
            quality_llm = OllamaService(model=os.getenv("OLLAMA_MODEL"))
            nutrition_agent = NutritionAgent(fast_llm, quality_llm)
            return await nutrition_agent.calculate_calories(user_query)
        
        response = await self.orchestrator.ask(prompt)
        return response.get("answer", "")