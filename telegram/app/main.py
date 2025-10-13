import os
import sys
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update

from backend.db import connect, disconnect
from handlers.start import start_router
from handlers.photo import photo_router
from handlers.message import message_router
from handlers.history import history_router
from handlers.profile import profile_router

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TG_SECRET_TOKEN = os.getenv("TG_SECRET_TOKEN")

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- Подключаем роутеры ---
dp.include_router(start_router)
dp.include_router(photo_router)
dp.include_router(message_router)
dp.include_router(history_router)
dp.include_router(profile_router)

# --- Стартап / шутдаун ---
@app.on_event("startup")
async def startup():
    await connect()
    await bot.set_webhook(WEBHOOK_URL, secret_token=TG_SECRET_TOKEN)

@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()
    await disconnect()

# --- Webhook ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if token != TG_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    update_data = await request.json()

    if "my_chat_member" in update_data or "chat_member" in update_data:
        logger.info("Игнорирую системное обновление")
        return {"ok": True}

    message = update_data.get("message")
    if message:
        if "new_chat_members" in message or "left_chat_member" in message:
            logger.info("Игнорирую сообщение о добавлении/удалении участника")
            return {"ok": True}

    try:
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.info(f"Ошибка при обработке обновления: {e}")
    return {"ok": True}
