from fastapi import APIRouter, Depends
from services.llm_orchestrator import LLMOrchestrator

router = APIRouter(tags=["health"])

def get_llm_orchestrator() -> LLMOrchestrator:
    from main import llm_orchestrator
    return llm_orchestrator

@router.get("/health")
async def health_check(orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)):
    """Проверка здоровья всех сервисов"""
    return await orchestrator.health_check()

@router.get("/")
async def root():
    """Корневой endpoint"""
    return {"status": "ok", "service": "nutrition-llm"}