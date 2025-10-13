import os
import sys
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import Update
from aiogram.filters import Command
from backend.llm_memory import ask_llm  # асинхронный
from backend.db import connect, disconnect
from backend.llm_history import add_to_memory, get_history

# --- Настройки из .env ---
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
LLM_URL = os.getenv("LLM_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TG_SECRET_TOKEN = os.getenv("TG_SECRET_TOKEN")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")


# --- Инициализация логгера ---
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

logging.getLogger("aiogram").setLevel(logging.INFO)
logging.getLogger("aiogram").handlers = [logging.StreamHandler(sys.stdout)]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True  # Принудительно переопределяет существующие обработчики
)
logger = logging.getLogger(__name__)

# --- Инициализация бота и диспетчера ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- Роутеры ---
command_router = Router()
message_router = Router()

# Хэндлер на команду /start (самый специфичный)
@command_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я Нутрион — твой AI-ассистент по питанию и тренировкам\nХочешь, я помогу рассчитать калорийность и составлю меню\nили распишу план тренировок для мощной бицухи или ягодицы?")


# Хэндлер на получение фото
@message_router.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("Это должно быть очень вкусно! Скоро я научусь считать калории, а пока можешь прислать мне еще фоток ;-)")
    
# --- Хэндлер команды /history ---
@command_router.message(Command("history"))
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

# --- Хэндлер обычных сообщений ---
@message_router.message(~F.text.startswith("/"))
async def handle_message(msg: types.Message):
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    user_input = msg.text
    try:
        answer = await ask_llm(chat_id, user_id, user_input)
        await add_to_memory(chat_id, user_id, user_input, answer)
        await msg.answer(answer)
    except Exception as e:
        await msg.answer("Произошла ошибка при обработке запроса 😕")
        logger.exception(e)

# --- Подключаем роутеры к Dispatcher ---
dp.include_router(command_router)
dp.include_router(message_router)

# --- Подключение к базе при старте ---
@app.on_event("startup")
async def startup():
    await connect()
    await bot.set_webhook(WEBHOOK_URL, secret_token=TG_SECRET_TOKEN)
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL, secret_token=TG_SECRET_TOKEN)
        logger.info(f"Webhook установлен: {WEBHOOK_URL}")

# --- Отключение базы при завершении ---
@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()
    await disconnect()

# --- Прием обновлений от Telegram ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if token != TG_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    update_data = await request.json()
    print(update_data)
     # --- 🧩 Игнорируем системные события (добавление в группу, изменение статуса и т.д.) ---
    if "my_chat_member" in update_data or "chat_member" in update_data:
        logger.info("Игнорирую системное обновление (добавление/удаление бота)")
        return {"ok": True}

    message = update_data.get("message")
    if message:
        # Игнорируем события приглашения участников
        if "new_chat_members" in message or "left_chat_member" in message:
            logger.info("Игнорирую сообщение о добавлении/удалении участника")
            return {"ok": True}
                
    try:
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.info(f"Ошибка при обработке обновления: {e}")  # Отладка
    return {"ok": True}
