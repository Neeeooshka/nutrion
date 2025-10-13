from aiogram import Router, types
from aiogram.filters import Command
from backend.llm_history import get_history

history_router = Router()

@history_router.message(Command("history"))
async def handle_history(msg: types.Message):
    chat_id = msg.chat.id
    user_id = msg.from_user.id

    try:
        parts = msg.text.strip().split()
        num = int(parts[1]) if len(parts) > 1 else 3
        num = min(num, 10)
    except ValueError:
        await msg.answer("Неверный формат команды. Используйте /history {число}")
        return

    rows = await get_history(chat_id, user_id, num)
    if not rows:
        await msg.answer("История пустая 😕")
        return

    history_text = ""
    for i, row in enumerate(rows, 1):
        history_text += f"{i}. Ты: {row['user_message']}\n   AI: {row['ai_response']}\n\n"

    await msg.answer(history_text.strip())
