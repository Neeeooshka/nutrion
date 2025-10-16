from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from backend.llm_memory import ask_llm
from backend.llm_history import add_to_memory
from backend.llm_profile import get_profile
from handlers.profile import start_profile_flow
from config.thinking import get_random_phrase
from config.errors import get_random_error_phrase
import logging
import asyncio

message_router = Router()
logger = logging.getLogger(__name__)

@message_router.message(~F.text.startswith("/"))
async def handle_message(msg: types.Message, state: FSMContext):
    
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    
    profile = await get_profile(chat_id, user_id)
    if not profile:
        # Профиль не заполнен — запускаем анкету
        logger.info("Запрос с незаполненным профилем")
        await start_profile_flow(msg, state)
        return
        
    user_input = msg.text
    try:
        # Фраза размышления
        await msg.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        thinking_text = get_random_phrase()
        await asyncio.sleep(1)
        await msg.answer(thinking_text)
        
        # Запрашиваем модель (LLM)
        stop_event = asyncio.Event()
        typing_task = asyncio.create_task(keep_typing(msg.bot, chat_id, stop_event))
        
        answer = await ask_llm(chat_id, user_id, user_input)
        
        stop_event.set()
        await typing_task
        
        # Ответ модели
        await msg.answer(answer)
        logger.info("Получен ответ от LLM")
        
    except Exception as e:
        stop_event.set()
        await typing_task
        
        error_text = get_random_error_phrase()
        await msg.answer(error_text)
        logger.exception(e)

async def keep_typing(bot, chat_id, stop_event: asyncio.Event):
    """Поддерживает статус 'typing' пока stop_event не установлен"""
    try:
        while not stop_event.is_set():
            await asyncio.sleep(7)
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception:
        pass  # чтобы не ронять поток при отмене