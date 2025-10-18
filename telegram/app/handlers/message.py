# handlers/message.py
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from backend.llm_memory import ask_llm, ask_llm_stream
from backend.llm_profile import get_profile
from handlers.profile import start_profile_flow
from config.thinking import get_random_phrase
from config.errors import get_random_error_phrase
import logging
import asyncio
import time
import json

message_router = Router()
logger = logging.getLogger(__name__)

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
        stream_msg = await bot.send_message(chat_id=chat_id, text="Генерирую ответ...")
        current_text = ""
        buffer = ""
        start_time = time.time()
        
        async for chunk in ask_llm_stream(chat_id, user_id, user_input):
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
        
        await add_to_memory(chat_id, user_id, user_input, current_text, topic="")  # topic set in ask_llm_stream
        
        logger.info(f"Ответ LLM отправлен пользователю {user_id}")
        
    except Exception as e:
        stop_event.set()
        await typing_task
        error_text = get_random_error_phrase()
        await bot.send_message(chat_id=chat_id, text=f"❌ {error_text}")
        logger.exception(f"Ошибка в фоновой задаче LLM: {e}")