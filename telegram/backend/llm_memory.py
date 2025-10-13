import requests
import os

LLM_URL = os.getenv("LLM_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

# Память пользователей хранится в PostgreSQL или временно здесь
user_memory = {}

def make_key(chat_id: int, user_id: int) -> str:
    return f"{chat_id}_{user_id}"

def get_user_context(chat_id: int, user_id: int) -> str:
    return user_memory.get(make_key(chat_id, user_id), "")

def update_user_context(chat_id: int, user_id: int, user_message: str, ai_response: str):
    key = make_key(chat_id, user_id)
    if key not in user_memory:
        user_memory[key] = ""
    user_memory[key] += f"\nUser: {user_message}\nAI: {ai_response}"

def ask_llm(chat_id: int, user_id: int, user_message: str) -> str:
    context = get_user_context(chat_id, user_id)

    headers = {"X-API-Key": INTERNAL_API_KEY}
    resp = requests.post(f"{LLM_URL}/ask", json={"prompt": user_message}, headers=headers)
    data = resp.json()
    ai_text = data.get("answer", "Ошибка: нет ответа от модели")
    
    update_user_context(chat_id, user_id, user_message, ai_text)
    return ai_text
