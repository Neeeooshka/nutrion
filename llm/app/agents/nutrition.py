# llm/agents/nutrition.py
import asyncio
from typing import List, Dict, Any, Optional
import logging
import os
import re  # для extract

from .base import BaseAgent  # import

logger = logging.getLogger("nutrition-llm")

class NutritionAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "nutrition"
    
    @property
    def description(self) -> str:
        return "Агент для вопросов по питанию, калориям, БЖУ, диетам, продуктам и БАДам."
    
    @property
    def keywords(self) -> List[str]:
        return ["питан", "калор", "рацион", "белк", "жир", "углевод", "бад", "протеин", "bcaa", "креатин", "продукт", "есть после", "на ночь", "утром", "днем"]
        
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
        # Assume profile in query (from prompt)
        gender = extract_param("gender", query, 'м')
        age = float(extract_param("age", query, 30))  # defaults if not
        weight = float(extract_param("weight", query, 70))
        height = float(extract_param("height", query, 170))  # add height to profile if needed
        goal = extract_param("goal", query, "maintain")
        
        # Harris-Benedict
        if gender.lower() == 'м':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        # Activity factor example: 1.2 sedentary, 1.55 moderate, etc.
        activity_factor = 1.55  # from profile or query
        calories = bmr * activity_factor
        
        # Adjust for goal
        if "похуд" in goal.lower():
            calories -= 500
        elif "набор" in goal.lower():
            calories += 500
        
        kbju = f"Daily calories: {calories:.0f}, Protein: {weight*2:.0f}g, Carbs: {calories*0.5/4:.0f}g, Fats: {calories*0.3/9:.0f}g"
        
        personalize_prompt = f"Based on KBJU {kbju}, suggest for query: {query}. Be brief."
        response = await self.quality_llm.ask(personalize_prompt)
        return response.get("answer", "")
    
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
    
    def extract_param(param_name, text: str, default=None):
        # Simple regex, improve as needed
        match = re.search(f"{param_name}:\\s*(\\w+)", text, re.I)
        return match.group(1) if match else default