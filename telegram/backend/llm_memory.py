import os
import requests
from backend.db import database
from backend.models import user_memory
from sqlalchemy import select, update, insert

LLM_URL = os.getenv("LLM_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Ты AI-тренер")
MODEL = os.getenv("MODEL", "gpt-4o-mini")
DEFAULT_PROMPT = os.getenv("DEFAULT_PROMPT", "Привет!")

def make_key(chat_id: int, user_id: int) -> dict:
    return {"chat_id": str(chat_id), "user_id": str(user_id)}

async def get_user_context(chat_id: int, user_id: int) -> str:
    key = make_key(chat_id, user_id)
    query = select(user_memory.c.context).where(
        (user_memory.c.chat_id == key["chat_id"]) & 
        (user_memory.c.user_id == key["user_id"])
    )
    row = await database.fetch_one(query)
    return row["context"] if row else ""

async def update_user_context(chat_id: int, user_id: int, user_message: str, ai_response: str):
    key = make_key(chat_id, user_id)
    context = await get_user_context(chat_id, user_id)
    new_context = context + f"\nUser: {user_message}\nAI: {ai_response}"

    query = select(user_memory.c.id).where(
        (user_memory.c.chat_id == key["chat_id"]) &
        (user_memory.c.user_id == key["user_id"])
    )
    row = await database.fetch_one(query)
    if row:
        upd = update(user_memory).where(user_memory.c.id == row["id"]).values(context=new_context)
        await database.execute(upd)
    else:
        ins = insert(user_memory).values(chat_id=key["chat_id"], user_id=key["user_id"], context=new_context)
        await database.execute(ins)

async def ask_llm(chat_id: int, user_id: int, user_message: str) -> str:
    context = await get_user_context(chat_id, user_id)
    prompt = f"{SYSTEM_PROMPT}\n{context}\nUser: {user_message or DEFAULT_PROMPT}"

    headers = {"X-API-Key": INTERNAL_API_KEY}
    resp = requests.post(
        f"{LLM_URL}/ask",
        json={"prompt": prompt, "model": MODEL},
        headers=headers
    )
    data = resp.json()
    ai_text = data.get("answer", "Ошибка: нет ответа от модели")
    
    await update_user_context(chat_id, user_id, user_message, ai_text)
    return ai_text
