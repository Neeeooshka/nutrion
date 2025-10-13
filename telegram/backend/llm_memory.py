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
    """Получаем текущий контекст пользователя из базы"""
    key = make_key(chat_id, user_id)
    query = user_memory.select().where(
        (user_memory.c.chat_id == key["chat_id"]) &
        (user_memory.c.user_id == key["user_id"])
    )
    row = await database.fetch_one(query)
    if row:
        return row["context"]
    return ""

async def update_user_context(chat_id: int, user_id: int, user_message: str, ai_response: str):
    """Обновляем память пользователя в базе"""
    key = make_key(chat_id, user_id)
    current_context = await get_user_context(chat_id, user_id)
    new_context = f"{current_context}\nUser: {user_message}\nAI: {ai_response}" if current_context else f"User: {user_message}\nAI: {ai_response}"

    # Проверяем, есть ли запись
    query = user_memory.select().where(
        (user_memory.c.chat_id == key["chat_id"]) &
        (user_memory.c.user_id == key["user_id"])
    )
    row = await database.fetch_one(query)
    if row:
        upd = user_memory.update().where(user_memory.c.id == row["id"]).values(context=new_context)
        await database.execute(upd)
    else:
        ins = user_memory.insert().values(chat_id=key["chat_id"], user_id=key["user_id"], context=new_context)
        await database.execute(ins)

async def ask_llm(chat_id: int, user_id: int, user_message: str) -> str:
    """Формируем полный промт с контекстом и отправляем на LLM"""
    context = await get_user_context(chat_id, user_id)

    headers = {"X-API-Key": INTERNAL_API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{LLM_URL}/ask",
            json={"prompt": prompt, "context": context},
            headers=headers
        )
    resp.raise_for_status()
    data = resp.json()
    ai_text = data.get("answer", "Ошибка: нет ответа от модели")

    await update_user_context(chat_id, user_id, user_message, ai_text)
    return ai_text
