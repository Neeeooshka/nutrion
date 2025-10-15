from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("nutrition-llm")


class PlanningAgent:
    def __init__(self, llm_service):
        self.llm = llm_service
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
            return f"Извините, не удалось создать план. Ошибка: {str(e)}"
    
    async def execute_plan(self, user_goal: str) -> str:
        """Выполнение многошагового плана"""
        logger.info(f"🎯 Начинаем выполнение цели: {user_goal}")
        
        # Шаг 1: Создание плана
        plan = await self._create_plan(user_goal)
        logger.info(f"📋 План выполнения: {plan}")
        
        # Шаг 2: Выполнение шагов
        results = []
        for step in plan:
            logger.info(f"🔧 Выполняем шаг: {step}")
            result = await self._execute_step(step, user_goal)
            results.append(result)
        
        # Шаг 3: Финальный синтез
        final_result = await self._create_final_report(user_goal, results)
        return final_result
    
    async def _create_plan(self, goal: str) -> List[str]:
        """Создание плана выполнения цели"""
        prompt = f"""
        Пользователь хочет: {goal}
        
        Создай пошаговый план для достижения этой цели в контексте фитнеса и питания.
        Верни только шаги в виде нумерованного списка.
        """
        
        response = await self.llm.ask(prompt)
        # Парсим нумерованный список
        steps = [line.strip() for line in response.split('\n') if line.strip() and line[0].isdigit()]
        return [step[3:].strip() for step in steps if '. ' in step]  # Убираем нумерацию
    
    async def _execute_step(self, step: str, context: str) -> str:
        """Выполнение одного шага плана"""
        prompt = f"""
        Общая цель: {context}
        Текущий шаг: {step}
        
        Дай детальные рекомендации для выполнения этого шага.
        Будь максимально конкретным и практичным.
        """
        
        return await self.llm.ask(prompt)
    
    async def _create_final_report(self, goal: str, step_results: List[str]) -> str:
        """Создание финального отчета"""
        prompt = f"""
        Исходная цель: {goal}
        
        Результаты выполнения шагов:
        {chr(10).join([f"Шаг {i+1}: {result}" for i, result in enumerate(step_results)])}
        
        Создай финальный отчет с:
        1. Кратким резюме достигнутых результатов
        2. Конкретными рекомендациями для пользователя
        3. Планом поддержания результатов
        4. Дальнейшими шагами для развития
        """
        
        return await self.llm.ask(prompt)