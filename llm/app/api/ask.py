from fastapi import APIRouter, Request, HTTPException, Depends
from services.llm_orchestrator import LLMOrchestrator
from config import DEFAULT_PROMPT
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
    prompt = data.get("prompt", DEFAULT_PROMPT)
    context = data.get("context", "")
    
    result = await orchestrator.ask(prompt, context)
    
    return {
        "answer": result.get("answer", "Извините, произошла ошибка"),
        "provider": result.get("provider", "unknown"),
        "model": result.get("model", "unknown"),
        "status": "success" if "answer" in result else "error",
        "error": result.get("error","")
    }
    
@router.post("/ask-agent")
async def ask_agent(
    request: Request,
    orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)
):
    """Эндпоинт для работы с агентами"""
    verify_api_key(request)
    
    data = await request.json()
    prompt = data.get("prompt", DEFAULT_PROMPT)
    agent_type = data.get("agent_type", "auto")  # auto, nutrition, planning, simple
    context = data.get("context", "")
    
    from agents.manager import AgentManager
    agent_manager = AgentManager(orchestrator)
    
    full_prompt = f"{context}\n{prompt}" if context else prompt
    result = await agent_manager.route_request(full_prompt, agent_type)
    
    return {
        "answer": result.get("answer", "Извините, произошла ошибка"),
        "agent_type": result.get("agent_type", "unknown"),
        "status": result.get("status", "error"),
        "error": result.get("error","")
    }