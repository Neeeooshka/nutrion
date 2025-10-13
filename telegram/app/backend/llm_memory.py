# backend/llm_memory.py
import os
import httpx
from backend.db import database
from backend.models import user_memory

LLM_URL = os.getenv("LLM_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

def make_key(chat_id: int, user_id: int) -> dict:
    return {"chat_id": str(chat_id), "user_id": str(user_id)}

async def get_user_context(chat_id: int, user_id: int) -> str:
    """Собираем текущий контекст пользователя из истории сообщений в базе"""
    key = make_key(chat_id, user_id)
    query = (
        user_memory.select()
        .where((user_memory.c.chat_id == key["chat_id"]) & (user_memory.c.user_id == key["user_id"]))
        .order_by(user_memory.c.created_at.asc())
    )
    rows = await database.fetch_all(query)
    if not rows:
        return ""
    context = "\n".join(f"User: {r['user_message']}\nAI: {r['ai_response']}" for r in rows)
    return context

async def add_to_memory(chat_id: int, user_id: int, user_message: str, ai_response: str):
    """Добавляем новое сообщение пользователя и ответ AI в базу"""
    key = make_key(chat_id, user_id)
    ins = user_memory.insert().values(
        chat_id=key["chat_id"],
        user_id=key["user_id"],
        user_message=user_message,
        ai_response=ai_response
    )
    await database.execute(ins)

async def ask_llm(chat_id: int, user_id: int, user_message: str) -> str:
    """Формируем полный промт с контекстом и отправляем на LLM"""
    context = await get_user_context(chat_id, user_id)
    prompt = f"{context}\nUser: {user_message}" if context else f"User: {user_message}"

    headers = {"X-API-Key": INTERNAL_API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{LLM_URL}/ask",
            json={"prompt": prompt},
            headers=headers
        )
    resp.raise_for_status()
    data = resp.json()
    ai_text = data.get("answer", "Ошибка: нет ответа от модели")

    await add_to_memory(chat_id, user_id, user_message, ai_text)
    return ai_text
