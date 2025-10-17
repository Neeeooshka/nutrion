# llm/agents/planning.py
import asyncio
from typing import List, Dict, Any, Optional
from .base import BaseAgent
import logging
import os

logger = logging.getLogger("nutrition-llm")

class PlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "planning"
    
    @property
    def description(self) -> str:
        return "Агент для создания планов, программ тренировок, многошаговых целей."
    
    @property
    def keywords(self) -> List[str]:
        return ["тренир", "программ", "план", "расход энерги", "пропуск", "составь", "распиш", "зал", "функциональн"]
    
    def __init__(self, fast_llm_service, quality_llm_service):
        self.fast_llm = fast_llm_service  # Для подзадач
        self.quality_llm = quality_llm_service  # Для финального ответа
        self.conversation_history = []
    
    async def process_query(self, user_query: str) -> str:
        """Основной метод обработки запроса для менеджера"""
        logger.info(f"📋 PlanningAgent обрабатывает запрос: {user_query}")
        
        try:
            # Используем существующую логику планирования
            result = await self.execute_plan(user_query)
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка в PlanningAgent: {e}")
            return f"Ошибка: {str(e)}"
    
    async def execute_plan(self, user_goal: str) -> str:
        """Выполнение многошагового плана"""
        logger.info(f"🎯 Начинаем выполнение цели: {user_goal}")
        
        # Шаг 1: Создание плана (быстрая модель)
        plan = await self._create_plan(user_goal)
        logger.info(f"📋 План выполнения: {plan}")
        
        # Шаг 2: ПАРАЛЛЕЛЬНОЕ выполнение шагов (быстрая модель)
        tasks = [self._execute_step(step, user_goal) for step in plan]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Ошибка в шаге {plan[i]}: {result}")
            else:
                valid_results.append(result)
        
        # Шаг 3: Финальный синтез (качественная модель)
        final_result = await self._create_final_report(user_goal, valid_results)
        return final_result
    
    async def _create_plan(self, goal: str) -> List[str]:
        """Создание плана выполнения цели (быстрая модель)"""
        prompt = f"""
        Пользователь хочет: {goal}
        
        Создай пошаговый план для достижения этой цели в контексте фитнеса и питания.
        Верни только шаги в виде нумерованного списка.
        """
        
        response = await self.fast_llm.ask(prompt)
        response_text = response.get("answer", "") if isinstance(response, dict) else response
        
        # Парсим нумерованный список
        steps = [line.strip() for line in response_text.split('\n') if line.strip() and line[0].isdigit()]
        return [step[3:].strip() for step in steps if '. ' in step]  # Убираем нумерацию
    
    async def _execute_step(self, step: str, context: str) -> str:
        """Выполнение одного шага плана (быстрая модель)"""
        prompt = f"""
        Общая цель: {context}
        Текущий шаг: {step}
        
        Дай детальные рекомендации для выполнения этого шага.
        Будь максимально конкретным и практичным.
        """
        
        response = await self.fast_llm.ask(prompt)
        return response.get("answer", "") if isinstance(response, dict) else response
    
    async def _create_final_report(self, goal: str, step_results: List[str]) -> str:
        """Создание финального отчета (качественная модель)"""
        prompt = f"""
        Исходная цель: {goal}
        
        Результаты выполнения шагов:
        {chr(10).join([f"Шаг {i+1}: {result}" for i, result in enumerate(step_results)])}
        
        Создай финальный отчет с:
        1. Кратким резюме достигнутых результатов
        2. Конкретными рекомендациями для пользователя
        3. Планом поддержания результатов
        4. Дальнейшими шагами для развития
        
        Отвечай на русском языке.
        """
        
        response = await self.quality_llm.ask(prompt)
        return response.get("answer", "") if isinstance(response, dict) else response