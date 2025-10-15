from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from backend.llm_memory import ask_llm
from backend.llm_history import add_to_memory
from backend.llm_profile import get_profile
from handlers.profile import start_profile_flow
from config.thinking import get_random_phrase
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
        await msg.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        answer = await ask_llm(chat_id, user_id, user_input)
        await add_to_memory(chat_id, user_id, user_input, answer)
        
        # Ответ модели
        await msg.answer(answer)
        logger.info("Получен ответ от LLM")
        
    except Exception as e:
        await msg.answer("Произошла ошибка при обработке запроса 😕")
        logger.exception(e)
