from fastapi import APIRouter, HTTPException, Depends
from services.llm_orchestrator import LLMOrchestrator

router = APIRouter(tags=["provider"])

def get_llm_orchestrator() -> LLMOrchestrator:
    from main import llm_orchestrator
    return llm_orchestrator

@router.get("/switch-provider/{provider}")
async def switch_provider(
    provider: str,
    orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)
):
    """Ручное переключение между LLM провайдерами"""
    success = await orchestrator.switch_provider(provider)
    
    if success:
        return {
            "message": f"Переключились на {provider}", 
            "provider": orchestrator.current_provider
        }
    else:
        raise HTTPException(
            status_code=400, 
            detail="Невозможно переключиться на указанный провайдер"
        )