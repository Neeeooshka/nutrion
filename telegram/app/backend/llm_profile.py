from backend.db import database
from backend.models import profiles
import sqlalchemy

# --- Сохраняем или обновляем профиль пользователя ---
async def save_profile(chat_id: int, user_id: int, data: dict):
    query = profiles.insert().values(
        chat_id=chat_id,
        user_id=user_id,
        gender=data['gender'],
        age=data['age'],
        weight=data['weight'],
        goal=data['goal'],
        diet=data['diet']
    ).on_conflict_do_update(
        index_elements=['chat_id', 'user_id'],
        set_={
            "gender": data['gender'],
            "age": data['age'],
            "weight": data['weight'],
            "goal": data['goal'],
            "diet": data['diet']
        }
    )
    await database.execute(query)

# --- Получаем профиль пользователя ---
async def get_profile(chat_id: int, user_id: int):
    query = profiles.select().where(
        (profiles.c.chat_id == chat_id) &
        (profiles.c.user_id == user_id)
    )
    row = await database.fetch_one(query)
    if not row:
        return None
    return dict(row)
