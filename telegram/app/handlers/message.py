from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from backend.llm_memory import ask_llm
from backend.llm_history import add_to_memory
from backend.llm_profile import get_profile
from handlers.profile import cmd_start
import logging

message_router = Router()
logger = logging.getLogger(__name__)

@message_router.message(~F.text.startswith("/"))
async def handle_message(msg: types.Message, state: FSMContext):
    
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    
    profile = await get_profile(chat_id, user_id)
    if not profile:
        # Профиль не заполнен — запускаем анкету
        await cmd_start(msg, state)
        return
        
    user_input = msg.text
    try:
        answer = await ask_llm(chat_id, user_id, user_input)
        await add_to_memory(chat_id, user_id, user_input, answer)
        await msg.answer(answer)
    except Exception as e:
        await msg.answer("Произошла ошибка при обработке запроса 😕")
        logger.exception(e)
