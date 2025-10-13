# backend/llm_history.py
from backend.db import database
from backend.models import user_memory
import sqlalchemy

async def add_to_memory(chat_id: int, user_id: int, user_message: str, ai_response: str):
    query = user_memory.insert().values(
        chat_id=str(chat_id),
        user_id=str(user_id),
        user_message=user_message,
        ai_response=ai_response
    )
    await database.execute(query)

async def get_history(chat_id: int, user_id: int, limit: int = 5):
    limit = min(limit, 10)
    query = (
        user_memory.select()
        .where(
            (user_memory.c.chat_id == str(chat_id)) &
            (user_memory.c.user_id == str(user_id))
        )
        .order_by(user_memory.c.created_at.desc())
        .limit(limit)
    )
    rows = await database.fetch_all(query)
    # возвращаем в обратном порядке (от старых к новым)
    return list(reversed(rows))
