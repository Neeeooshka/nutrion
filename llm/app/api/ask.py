from fastapi import APIRouter, Request, HTTPException, Depends
from services.llm_orchestrator import LLMOrchestrator
import os

router = APIRouter(tags=["ask"])
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

def get_llm_orchestrator() -> LLMOrchestrator:
    from main import llm_orchestrator
    return llm_orchestrator

def verify_api_key(request: Request):
    """Проверка API ключа"""
    key = request.headers.get("X-API-Key")
    if key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

@router.post("/ask")
async def ask(
    request: Request,
    orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)
):
    """Основной endpoint для запросов к LLM"""
    verify_api_key(request)
    
    data = await request.json()
    prompt = data.get("prompt", "Ответь на вопрос о питании или фитнесе")
    context = data.get("context", "")
    
    return await orchestrator.ask(prompt, context)