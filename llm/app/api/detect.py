# llm/api/detect.py
from fastapi import APIRouter, Request, HTTPException, Depends
from services.llm_orchestrator import LLMOrchestrator
import os

router = APIRouter(tags=["detect"])

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

def get_llm_orchestrator() -> LLMOrchestrator:
    from main import llm_orchestrator
    return llm_orchestrator

def verify_api_key(request: Request):
    key = request.headers.get("X-API-Key")
    if key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

@router.post("/detect_type")
async def detect_agent_type(
    request: Request,
    orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)
):
    verify_api_key(request)
    
    data = await request.json()
    query = data.get("query", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query required")
    
    from agents.manager import AgentManager
    agent_manager = AgentManager(orchestrator)
    agent_type = agent_manager._detect_agent_type(query)
    
    return {"type": agent_type}