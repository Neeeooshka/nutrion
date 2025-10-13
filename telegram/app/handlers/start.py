from aiogram import Router, types
from aiogram.filters import Command

start_router = Router()

@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я Нутрион — твой AI-ассистент по питанию и тренировкам.\n\n"
        "Хочешь, я помогу рассчитать калорийность и составлю меню\n"
        "или распишу план тренировок для мощной бицухи или ягодицы? 🍑💪"
    )
