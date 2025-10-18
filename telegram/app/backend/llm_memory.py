# backend/llm_memory.py
import httpx
import logging
from typing import AsyncIterator
from backend.db import database
from backend.models import user_memory
from backend.llm_profile import get_profile
from config.errors import get_random_error_phrase
import os
import json

LLM_URL = os.getenv("LLM_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

logger = logging.getLogger(__name__)

def make_key(chat_id: int, user_id: int) -> dict:
    return {"chat_id": str(chat_id), "user_id": str(user_id)}

async def add_to_memory(chat_id: int, user_id: int, user_message: str, ai_response: str, topic: str):
    key = make_key(chat_id, user_id)
    ins = user_memory.insert().values(
        chat_id=key["chat_id"],
        user_id=key["user_id"],
        user_message=user_message,
        ai_response=ai_response,
        topic=topic
    )
    await database.execute(ins)

async def ask_llm(prompt: str, topic: str) -> str:
    headers = {"X-API-Key": INTERNAL_API_KEY, "Content-Type": "application/json"}
    
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            f"{LLM_URL}/ask",
            json={"prompt": prompt, "agent_type": topic},
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
    
    ai_text = data.get("answer", "")
    
    if data.get("status") == "error":
        ai_text = get_random_error_phrase()
    
    return ai_text

async def ask_llm_stream(prompt: str, topic: str) -> AsyncIterator[str]:
    headers = {"X-API-Key": INTERNAL_API_KEY, "Content-Type": "application/json"}
    
    async with httpx.AsyncClient(timeout=300) as client:
        async with client.stream(
            "POST",
            f"{LLM_URL}/ask",
            json={"prompt": prompt, "agent_type": topic, "stream": True},
            headers=headers
        ) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_text():
                if chunk:
                    try:
                        data = json.loads(chunk)
                        if "chunk" in data:
                            yield data["chunk"]  # Extract text from JSON
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON chunk: {chunk}")
                        continue