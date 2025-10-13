from aiogram import Router, types, F
from backend.llm_memory import ask_llm
from backend.llm_history import add_to_memory
import logging

message_router = Router()
logger = logging.getLogger(__name__)

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
