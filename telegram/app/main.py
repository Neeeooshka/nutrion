from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
import asyncio, os, requests

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
LLM_URL = os.getenv("LLM_URL")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(msg: types.Message):
    user_input = msg.text
    resp = requests.post(f"{LLM_URL}/ask", json={"prompt": user_input})
    data = resp.json()
    await msg.answer(data["answer"])

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(dp.start_polling(bot))
