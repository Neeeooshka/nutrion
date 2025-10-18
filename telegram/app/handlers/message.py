# handlers/message.py
from aiogram import Router, types, F, Bot
from typing import Tuple
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from backend.llm_memory import ask_llm, ask_llm_stream, add_to_memory, make_key
from backend.llm_profile import get_profile
from handlers.profile import start_profile_flow
from config.thinking import get_random_phrase
from config.errors import get_random_error_phrase
from backend.models import user_memory
from backend.db import database
import redis.asyncio as redis
import logging
import asyncio
import time
import os
import json
import httpx

LLM_URL = os.getenv("LLM_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")

message_router = Router()
logger = logging.getLogger(__name__)
redis = redis.Redis.from_url(REDIS_URL)

@message_router.message(~F.text.startswith("/"))
async def handle_message(msg: types.Message, state: FSMContext):
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    
    profile = await get_profile(chat_id, user_id)
    if not profile:
        logger.info("Запрос с незаполненным профилем")
        await start_profile_flow(msg, state)
        return
        
    user_input = msg.text
    try:
        thinking_text = get_random_phrase()
        await msg.answer(thinking_text)
        
        asyncio.create_task(
            process_llm_background(
                bot=msg.bot,
                chat_id=chat_id,
                user_id=user_id,
                user_input=user_input
            )
        )
        
        logger.info(f"Запрос от пользователя {user_id} принят в обработку")
        
    except Exception as e:
        error_text = get_random_error_phrase()
        await msg.answer(error_text)
        logger.exception(e)

async def process_llm_background(bot: Bot, chat_id: int, user_id: int, user_input: str):
    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(bot, chat_id, stop_event))
    
    try:
        prompt, topic = await build_prompt_and_topic(chat_id, user_id, user_input)
        stream_msg = await bot.send_message(chat_id=chat_id, text="...")
        current_text = ""
        buffer = ""
        start_time = time.time()
        
        async for chunk in ask_llm_stream(prompt, topic):
            buffer += chunk
            if len(buffer) > 50 or (time.time() - start_time > 5):
                current_text += buffer
                await bot.edit_message_text(chat_id=chat_id, message_id=stream_msg.message_id, text=current_text)
                buffer = ""
                start_time = time.time()
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        if buffer:
            current_text += buffer
            await bot.edit_message_text(chat_id=chat_id, message_id=stream_msg.message_id, text=current_text)
        
        stop_event.set()
        await typing_task
        
        await add_to_memory(chat_id, user_id, user_input, current_text, topic)
        
        logger.info(f"Ответ LLM отправлен пользователю {user_id}")
        
    except Exception as e:
        stop_event.set()
        await typing_task
        error_text = get_random_error_phrase()
        await bot.send_message(chat_id=chat_id, text=f"❌ {error_text}")
        logger.exception(f"Ошибка в фоновой задаче LLM: {e}")
        
async def keep_typing(bot, chat_id, stop_event: asyncio.Event):
    """Поддерживает статус 'typing' пока stop_event не установлен"""
    try:
        while not stop_event.is_set():
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(5)  # Отправляем действие каждые 5 секунд
    except Exception as e:
        logger.debug(f"Индикатор набора завершен: {e}")
        

async def build_prompt_and_topic(chat_id: int, user_id: int, user_message: str) -> Tuple[str, str]:
    headers = {"X-API-Key": INTERNAL_API_KEY, "Content-Type": "application/json"}
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{LLM_URL}/detect_type",
            json={"query": user_message},
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        topic = data.get("type", "simple")
    
    profile = await get_profile(chat_id, user_id)
    profile_info = ""
    if profile and topic in ["nutrition", "planning"]:
        profile_info = (
            f"User profile:\n"
            f"- Gender: {profile['gender']}\n"
            f"- Age: {profile['age']} years\n"
            f"- Weight: {profile['weight']} kg\n"
            f"- Goal: {profile['goal']}\n"
            f"- Diet: {profile['diet']}\n\n"
        )
    
    context = await get_user_context(chat_id, user_id, topic)
    prompt = f"{profile_info}{context}\nUser: {user_message}" if context else f"{profile_info}User: {user_message}"
    
    return prompt, topic
    
    
async def get_user_context(chat_id: int, user_id: int, current_topic: str) -> str:
    cache_key = f"context:{chat_id}:{user_id}:{current_topic}"
    cached = await redis.get(cache_key)
    if cached:
        return cached.decode()
    
    key = make_key(chat_id, user_id)
    query = (
        user_memory.select()
        .where((user_memory.c.chat_id == key["chat_id"]) & 
               (user_memory.c.user_id == key["user_id"]) & 
               (user_memory.c.topic == current_topic))
        .order_by(user_memory.c.created_at.asc())
        .limit(5)
    )
    rows = await database.fetch_all(query)
    
    if not rows:
        return ""
    
    if len(rows) > 3:
        old_msgs = "\n".join(f"User: {r['user_message']}\nAI: {r['ai_response']}" for r in rows[:-3])
        summary_prompt = f"Summarize this relevant history in 50-100 words, keep key facts on {current_topic}: {old_msgs}"
        from services.llm_orchestrator import LLMOrchestrator
        orchestrator = LLMOrchestrator()
        summary = (await orchestrator.ask(summary_prompt))['answer']
        recent = "\n".join(f"User: {r['user_message']}\nAI: {r['ai_response']}" for r in rows[-3:])
        context = f"Summary of past {current_topic}: {summary}\nRecent: {recent}"
    else:
        context = "\n".join(f"User: {r['user_message']}\nAI: {r['ai_response']}" for r in rows)
    
    context_lines = context.split('\n')
    unique_lines = []
    for line in context_lines:
        if line not in unique_lines:
            unique_lines.append(line)
    context = '\n'.join(unique_lines)
    
    logger.info(f"Context size: {len(context)} chars")
    await redis.set(cache_key, context, ex=300)
    return context
