import logging

logger = logging.getLogger("nutrition-llm")

class SimpleAgent:
    def __init__(self, llm_orchestrator):
        self.orchestrator = llm_orchestrator
    
    async def process_query(self, user_query: str) -> str:
        """Простая обработка запроса - напрямую к LLM"""
        logger.info(f"💬 SimpleAgent обрабатывает запрос: {user_query}")
        
        try:
            # Просто передаем запрос в orchestrator
            response = await self.orchestrator.ask(user_query)
            
            # Извлекаем ответ из словаря
            if isinstance(response, dict) and 'answer' in response:
                return response['answer']
            elif isinstance(response, dict) and 'error' in response:
                return f"Ошибка: {response['error']}"
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"❌ Ошибка в SimpleAgent: {e}")
            return f"Ошибка: {str(e)}"