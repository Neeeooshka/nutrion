# llm/api/ask.py
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from services.llm_orchestrator import LLMOrchestrator
from config import DEFAULT_PROMPT
import os
import json
import asyncio

router = APIRouter(tags=["ask"])
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

def get_llm_orchestrator() -> LLMOrchestrator:
    from main import llm_orchestrator
    return llm_orchestrator

def verify_api_key(request: Request):
    key = request.headers.get("X-API-Key")
    if key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

@router.post("/ask")
async def ask_agent(
    request: Request,
    orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator)
):
    verify_api_key(request)
    
    data = await request.json()
    prompt = data.get("prompt", DEFAULT_PROMPT)
    agent_type = data.get("agent_type", "auto")
    context = data.get("context", "")
    stream = data.get("stream", False)
    
    from agents.manager import AgentManager
    agent_manager = AgentManager(orchestrator)
    
    full_prompt = f"{context}\n{prompt}" if context else prompt
    
    if stream:
        async def stream_response():
            result = await agent_manager.route_request(full_prompt, agent_type)
            # Assuming agent_manager can handle stream internally
            # For now, simulate stream from single response
            answer = result.get("answer", "")
            for i in range(0, len(answer), 50):  # chunk by ~50 chars
                yield json.dumps({"chunk": answer[i:i+50]}) + "\n"
                await asyncio.sleep(0.1)  # simulate
            yield json.dumps({"done": True}) + "\n"
        
        return StreamingResponse(stream_response(), media_type="text/event-stream")
    
    result = await agent_manager.route_request(full_prompt, agent_type)
    
    return {
        "answer": result.get("answer", ""),
        "agent_type": result.get("agent_type", "unknown"),
        "status": result.get("status", "error"),
        "error": result.get("error", "")
    }