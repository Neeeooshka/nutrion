from sqlalchemy.dialects.postgresql import insert
from backend.models import profiles
from backend.db import database

# --- Сохранение или обновление профиля ---
async def save_profile(chat_id: int, user_id: int, data: dict):
    """
    Сохраняет профиль пользователя или обновляет, если он уже есть.
    data: dict с ключами gender, age, weight, goal, diet
    """
    query = insert(profiles).values(
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
            'gender': data['gender'],
            'age': data['age'],
            'weight': data['weight'],
            'goal': data['goal'],
            'diet': data['diet']
        }
    )
    await database.execute(query)


# --- Получение профиля пользователя ---
async def get_profile(chat_id: int, user_id: int):
    query = profiles.select().where(
        (profiles.c.chat_id == chat_id) & (profiles.c.user_id == user_id)
    )
    row = await database.fetch_one(query)
    if row:
        return dict(row)
    return None
