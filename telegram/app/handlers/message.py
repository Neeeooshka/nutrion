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
        # Немедленно отправляем фразу размышления (через 1 секунду)
        await asyncio.sleep(1)
        thinking_text = get_random_phrase()
        processing_msg = await msg.answer(thinking_text)
        
        # Запускаем фоновую задачу для LLM
        asyncio.create_task(
            process_llm_background(
                bot=msg.bot,
                chat_id=chat_id,
                user_id=user_id,
                user_input=user_input,
                processing_message_id=processing_msg.message_id
            )
        )
        
        logger.info(f"Запрос от пользователя {user_id} принят в обработку")
        
    except Exception as e:
        error_text = get_random_error_phrase()
        await msg.answer(error_text)
        logger.exception(e)

async def process_llm_background(bot: Bot, chat_id: int, user_id: int, user_input: str, processing_message_id: int):
    """Фоновая задача для обработки LLM запроса"""
    stop_event = asyncio.Event()
    typing_task = None
    
    try:
        # Запускаем индикатор набора
        typing_task = asyncio.create_task(keep_typing(bot, chat_id, stop_event))
        
        # Выполняем запрос к LLM
        answer = await ask_llm(chat_id, user_id, user_input)
        
        # Останавливаем индикатор набора
        stop_event.set()
        if typing_task:
            await typing_task
        
        # Редактируем исходное сообщение с результатом
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=processing_message_id,
            text=answer
        )
        
        logger.info(f"Ответ LLM отправлен пользователю {user_id}")
        
    except Exception as e:
        # Останавливаем индикатор набора при ошибке
        stop_event.set()
        if typing_task:
            await typing_task
        
        error_text = get_random_error_phrase()
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=processing_message_id,
            text=f"❌ {error_text}\n\nОшибка: {str(e)}"
        )
        logger.exception(f"Ошибка в фоновой задаче LLM: {e}")

async def keep_typing(bot, chat_id, stop_event: asyncio.Event):
    """Поддерживает статус 'typing' пока stop_event не установлен"""
    try:
        while not stop_event.is_set():
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(5)  # Отправляем действие каждые 5 секунд
    except Exception as e:
        logger.debug(f"Индикатор набора завершен: {e}")