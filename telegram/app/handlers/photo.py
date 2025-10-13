from aiogram import Router, types
from aiogram.filters import F

photo_router = Router()

@photo_router.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer(
        "📸 Это должно быть очень вкусно! Скоро я научусь считать калории, "
        "а пока можешь прислать мне еще фоток 😉"
    )
