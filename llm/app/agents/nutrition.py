import asyncio
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger("nutrition-llm")

class NutritionAgent:
    def __init__(self, fast_llm_service, quality_llm_service):
        self.fast_llm = fast_llm_service
        self.quality_llm = quality_llm_service
        self.tools = self._setup_tools()
    
    def _setup_tools(self):
        return {
            "calculate_calories": self.calculate_calories,
            "suggest_workout": self.suggest_workout,
            "analyze_nutrition": self.analyze_nutrition,
            "create_meal_plan": self.create_meal_plan
        }
    
    async def process_query(self, user_query: str) -> str:
        """Основной метод обработки запроса с параллельным выполнением"""
        # Шаг 1: Анализ запроса и выбор инструментов
        tools_to_use = await self._select_tools(user_query)
        
        # Шаг 2: ПАРАЛЛЕЛЬНОЕ выполнение инструментов
        tasks = [self.tools[tool_name](user_query) for tool_name in tools_to_use]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Ошибка в инструменте {tools_to_use[i]}: {result}")
            else:
                valid_results.append(result)
        
        # Шаг 3: Синтез финального ответа
        final_response = await self._synthesize_response(user_query, valid_results)
        return final_response
    
    # Остальные методы без изменений...
    async def _select_tools(self, query: str) -> List[str]:
        prompt = f"""..."""
        response = await self.fast_llm.ask(prompt)
        response_text = response.get("answer", "") if isinstance(response, dict) else response
        tools = [tool.strip() for tool in response_text.split(",")]
        return [tool for tool in tools if tool in self.tools]
    
    async def calculate_calories(self, query: str) -> str:
        prompt = f"""..."""
        response = await self.fast_llm.ask(prompt)
        return response.get("answer", "") if isinstance(response, dict) else response
    
    async def suggest_workout(self, query: str) -> str:
        prompt = f"""..."""
        response = await self.fast_llm.ask(prompt)
        return response.get("answer", "") if isinstance(response, dict) else response
    
    async def analyze_nutrition(self, query: str) -> str:
        prompt = f"""..."""
        response = await self.fast_llm.ask(prompt)
        return response.get("answer", "") if isinstance(response, dict) else response
    
    async def create_meal_plan(self, query: str) -> str:
        prompt = f"""..."""
        response = await self.fast_llm.ask(prompt)
        return response.get("answer", "") if isinstance(response, dict) else response
    
    async def _synthesize_response(self, original_query: str, tool_results: List[str]) -> str:
        prompt = f"""..."""
        response = await self.quality_llm.ask(prompt)
        return response.get("answer", "") if isinstance(response, dict) else response