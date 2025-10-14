from aiogram.fsm.context import FSMContext
from aiogram import types

async def start_profile_flow(msg: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "👋 Привет! Я Нутрион — твой AI-ассистент по питанию и тренировкам.\n\n"
        "Давай познакомимся поближе — ответь на несколько вопросов, чтобы я мог подобрать рекомендации специально для тебя 💪\n\n"
    )
    await msg.answer(text, parse_mode="Markdown")
    await msg.answer("🔹 Укажи свой пол (м/ж):")
    await state.set_state(ProfileForm.gender)
