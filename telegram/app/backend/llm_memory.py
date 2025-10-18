# backend/llm_memory.py
import redis.asyncio as redis
import httpx
import logging
from typing import Tuple, AsyncIterator
from backend.db import database
from backend.models import user_memory
from backend.llm_profile import get_profile
from config.errors import get_random_error_phrase
import os

logger = logging.getLogger(__name__)
LLM_URL = os.getenv("LLM_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
redis = redis.Redis.from_url(REDIS_URL)

def make_key(chat_id: int, user_id: int) -> dict:
    return {"chat_id": str(chat_id), "user_id": str(user_id)}

async def get_user_context(chat_id: int, user_id: int, current_topic: str) -> str:
    """Собираем релевантный контекст с лимитом и summary"""
    cache_key = f"context:{chat_id}:{user_id}:{current_topic}"
    cached = await redis.get(cache_key)
    if cached:
        return cached.decode()
    
    key = make_key(chat_id, user_id)
    query = (
        user_memory.select()
        .where((user_memory.c.chat_id == key["chat_id"]) & 
               (user_memory.c.user_id == key["user_id"]) & 
               (user_memory.c.topic == current_topic))
        .order_by(user_memory.c.created_at.asc())
        .limit(5)
    )
    rows = await database.fetch_all(query)
    
    if not rows:
        return ""
    
    if len(rows) > 3:
        old_msgs = "\n".join(f"User: {r['user_message']}\nAI: {r['ai_response']}" for r in rows[:-3])
        summary_prompt = f"Summarize this relevant history in 50-100 words, keep key facts on {current_topic}: {old_msgs}"
        from services.llm_orchestrator import LLMOrchestrator
        orchestrator = LLMOrchestrator()
        summary = (await orchestrator.ask(summary_prompt))['answer']
        recent = "\n".join(f"User: {r['user_message']}\nAI: {r['ai_response']}" for r in rows[-3:])
        context = f"Summary of past {current_topic}: {summary}\nRecent: {recent}"
    else:
        context = "\n".join(f"User: {r['user_message']}\nAI: {r['ai_response']}" for r in rows)
    
    logger.info(f"Context size: {len(context)} chars")
    await redis.set(cache_key, context, ex=300)
    return context

async def add_to_memory(chat_id: int, user_id: int, user_message: str, ai_response: str, topic: str):
    """Добавляем с topic"""
    key = make_key(chat_id, user_id)
    ins = user_memory.insert().values(
        chat_id=key["chat_id"],
        user_id=key["user_id"],
        user_message=user_message,
        ai_response=ai_response,
        topic=topic
    )
    await database.execute(ins)

async def build_prompt_and_topic(chat_id: int, user_id: int, user_message: str) -> Tuple[str, str]:
    """Формируем промпт и topic через API"""
    headers = {"X-API-Key": INTERNAL_API_KEY, "Content-Type": "application/json"}
    
    async with httpx.AsyncClient(timeout=10) as client:  # short timeout for detect
        resp = await client.post(
            f"{LLM_URL}/detect_type",
            json={"query": user_message},
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        topic = data.get("type", "simple")
    
    profile = await get_profile(chat_id, user_id)
    profile_info = ""
    if profile and topic in ["nutrition", "planning"]:
        profile_info = (
            f"User profile:\n"
            f"- Gender: {profile['gender']}\n"
            f"- Age: {profile['age']} years\n"
            f"- Weight: {profile['weight']} kg\n"
            f"- Goal: {profile['goal']}\n"
            f"- Diet: {profile['diet']}\n\n"
        )
    
    context = await get_user_context(chat_id, user_id, topic)
    prompt = f"{profile_info}{context}\nUser: {user_message}" if context else f"{profile_info}User: {user_message}"
    
    return prompt, topic

async def ask_llm(chat_id: int, user_id: int, user_message: str) -> str:
    """Формируем полный промт и отправляем на LLM"""
    prompt, topic = await build_prompt_and_topic(chat_id, user_id, user_message)
    
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
    
    if data.get("status") != "error":
        await add_to_memory(chat_id, user_id, user_message, ai_text, topic)
    else:
        ai_text = get_random_error_phrase()
    
    return ai_text

async def ask_llm_stream(chat_id: int, user_id: int, user_message: str) -> AsyncIterator[str]:
    """Стриминг ответ от LLM"""
    prompt, topic = await build_prompt_and_topic(chat_id, user_id, user_message)
    
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
                    yield chunk  # HTTP stream chunks
            # Full text accumulated in bot