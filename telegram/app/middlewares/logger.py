from aiogram import BaseMiddleware
import logging

logger = logging.getLogger("handlers_logger")

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        msg = data.get("event") or data.get("update")
        if hasattr(msg, "message"):
            chat_id = msg.message.chat.id
            user_id = msg.message.from_user.id
            logger.info(f"Handler {handler.__name__} called for chat {chat_id}, user {user_id}")
        return await handler(event, data)


