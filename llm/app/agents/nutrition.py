from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("nutrition-llm")

class NutritionAgent:
    def __init__(self, llm_service):
        self.llm = llm_service
        self.tools = self._setup_tools()
    
    def _setup_tools(self):
        """Настройка инструментов агента"""
        return {
            "calculate_calories": self.calculate_calories,
            "suggest_workout": self.suggest_workout,
            "analyze_nutrition": self.analyze_nutrition,
            "create_meal_plan": self.create_meal_plan
        }
    
    async def process_query(self, user_query: str) -> str:
        """Основной метод обработки запроса"""
        # Шаг 1: Анализ запроса и выбор инструментов
        tools_to_use = await self._select_tools(user_query)
        
        # Шаг 2: Выполнение инструментов
        results = []
        for tool_name in tools_to_use:
            result = await self.tools[tool_name](user_query)
            results.append(result)
        
        # Шаг 3: Синтез финального ответа
        final_response = await self._synthesize_response(user_query, results)
        return final_response
    
    async def _select_tools(self, query: str) -> List[str]:
        """Выбор подходящих инструментов для запроса"""
        prompt = f"""
        Проанализируй запрос пользователя и выбери подходящие инструменты из списка:
        Запрос: {query}
        
        Доступные инструменты:
        - calculate_calories: расчет калорий, БЖУ
        - suggest_workout: рекомендации по тренировкам
        - analyze_nutrition: анализ питания
        - create_meal_plan: создание плана питания
        
        Верни только названия инструментов через запятую.
        """
        
        response = await self.llm.ask(prompt)
        tools = [tool.strip() for tool in response.split(",")]
        return [tool for tool in tools if tool in self.tools]
    
    # Реализации инструментов
    async def calculate_calories(self, query: str) -> str:
        """Расчет калорий и БЖУ"""
        prompt = f"""
        Рассчитай калории и БЖУ на основе запроса:
        {query}
        
        Дай конкретные цифры и рекомендации.
        """
        return await self.llm.ask(prompt)
    
    async def suggest_workout(self, query: str) -> str:
        """Рекомендации по тренировкам"""
        prompt = f"""
        Дай рекомендации по тренировкам на основе запроса:
        {query}
        
        Учитывай уровень подготовки, цели и ограничения.
        """
        return await self.llm.ask(prompt)
    
    async def analyze_nutrition(self, query: str) -> str:
        """Анализ текущего питания"""
        prompt = f"""
        Проанализируй текущее питание пользователя:
        {query}
        
        Выдели сильные и слабые стороны, дай рекомендации.
        """
        return await self.llm.ask(prompt)
    
    async def create_meal_plan(self, query: str) -> str:
        """Создание плана питания"""
        prompt = f"""
        Создай персонализированный план питания:
        {query}
        
        Включи завтрак, обед, ужин и перекусы.
        """
        return await self.llm.ask(prompt)
    
    async def _synthesize_response(self, original_query: str, tool_results: List[str]) -> str:
        """Синтез финального ответа из результатов инструментов"""
        prompt = f"""
        Исходный запрос: {original_query}
        
        Результаты анализа:
        {chr(10).join(tool_results)}
        
        Создай целостный, персонализированный ответ объединяя все результаты.
        Будь конкретен и дай практические рекомендации.
        """
        return await self.llm.ask(prompt)