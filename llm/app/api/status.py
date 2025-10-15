from fastapi import APIRouter, Depends
from services.llm_orchestrator import LLMOrchestrator

router = APIRouter(tags=["status"])

def get_llm_orchestrator() -> LLMOrchestrator:
    from main import llm_orchestrator
    return llm_orchestrator

@router.get("/status")
async def get_status(orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)):
    """Получение текущего статуса системы"""
    return orchestrator.get_status()