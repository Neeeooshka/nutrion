import os
import requests
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
LLM_URL = os.getenv("LLM_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TG_SECRET_TOKEN = os.getenv("TG_SECRET_TOKEN")  # ✅ добавлено
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")  # ✅ добавлено

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Обработка входящих сообщений ---
@dp.message()
async def handle_message(msg: types.Message):
    user_input = msg.text
    try:
        headers = {"X-API-Key": INTERNAL_API_KEY}  # ✅ защита запроса к LLM
        resp = requests.post(f"{LLM_URL}/ask", json={"prompt": user_input}, headers=headers)
        data = resp.json()
        await msg.answer(data.get("answer", "Ошибка: нет ответа от модели"))
    except Exception as e:
        await msg.answer("Произошла ошибка при обработке запроса 😕")
        print("Error:", e)

# --- FastAPI-приложение ---
app = FastAPI()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Принимаем обновления от Telegram"""
    # ✅ проверяем токен Telegram
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if token != TG_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    """Устанавливаем webhook при запуске"""
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL, secret_token=TG_SECRET_TOKEN)  # ✅ передаём токен
        print(f"Webhook установлен: {WEBHOOK_URL}")
