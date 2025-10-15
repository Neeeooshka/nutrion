from fastapi import FastAPI
import logging
import sys
import asyncio
from services.llm_orchestrator import LLMOrchestrator
from api.endpoints import router

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("nutrition-llm")

# Инициализация приложения
app = FastAPI(
    title="Nutrition LLM Service",
    version="1.0.0",
    description="Гибридный LLM сервис для вопросов о питании и фитнесе"
)

# Инициализация оркестратора
llm_orchestrator = LLMOrchestrator()

# Подключение роутера
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Запуск при старте приложения"""
    logger.info("🚀 Starting Nutrition LLM Service...")
    await asyncio.sleep(15)
    await llm_orchestrator.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    logger.info("🛑 Shutting down Nutrition LLM Service...")