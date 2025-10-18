# llm/agents/nutrition.py
import asyncio
from typing import List, Dict, Any, Optional
import logging
import os
import re  # для extract

from .base import BaseAgent  # import

logger = logging.getLogger("nutrition-llm")

class NutritionAgent(BaseAgent):
    _NAME = "nutrition"
    _DESCRIPTION = "Агент для вопросов по питанию, калориям, БЖУ, диетам, продуктам и БАДам."
    _KEYWORDS = ["питан", "калор", "рацион", "белк", "жир", "углевод", "бад", "протеин", "bcaa", "креатин", "продукт", "есть после", "на ночь", "утром", "днем"]
    
    def __init__(self, fast_llm_service, quality_llm_service, **kwargs):
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
        query_lower = user_query.lower()
        tools_to_run = []
        
        if "калор" in query_lower:
            tools_to_run.append(self.tools["calculate_calories"](user_query))
        if "рацион" in query_lower or "питан" in query_lower:
            tools_to_run.append(self.tools["create_meal_plan"](user_query))
        
        if tools_to_run:
            results = await asyncio.gather(*tools_to_run)
            return "\n".join(r for r in results if r)
        
        # Fallback: если нет tools, прямой запрос к LLM
        from config import SYSTEM_PROMPT
        prompt = f"{SYSTEM_PROMPT}\nUser: {user_query}"
        response = await self.quality_llm.ask(prompt)
        return response.get("answer", "")
    
    # Остальные методы без изменений...
    async def _select_tools(self, query: str) -> List[str]:
        prompt = f"""..."""
        response = await self.fast_llm.ask(prompt)
        response_text = response.get("answer", "") if isinstance(response, dict) else response
        tools = [tool.strip() for tool in response_text.split(",")]
        return [tool for tool in tools if tool in self.tools]
    
    async def calculate_calories(self, query: str) -> str:
        gender = self.extract_param("gender", query, 'м')
        age = float(self.extract_param("age", query, 30))
        weight = float(self.extract_param("weight", query, 70))
        height = float(self.extract_param("height", query, 170))
        goal = self.extract_param("goal", query, "maintain")
        
        if gender.lower() == 'м':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        activity_factor = 1.55
        calories = bmr * activity_factor
        
        if "похуд" in goal.lower():
            calories -= 500
        elif "набор" in goal.lower():
            calories += 500
        
        kbju = f"Daily calories: {calories:.0f}, Protein: {weight*2:.0f}g, Carbs: {calories*0.5/4:.0f}g, Fats: {calories*0.3/9:.0f}g"
        
        # Для простых запросов (напр., "калории в яблоке")
        if "яблок" in query.lower():
            return "В среднем яблоке (около 182 г) примерно 95 калорий."
        
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
    
    def extract_param(self, param_name, text: str, default=None):
        match = re.search(f"{param_name}:\\s*(\\w+)", text, re.I)
        return match.group(1) if match else default
    