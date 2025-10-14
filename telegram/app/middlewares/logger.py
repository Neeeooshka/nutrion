import logging
from datetime import datetime
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

# Настраиваем стиль логов
class ColorFormatter(logging.Formatter):
    COLORS = {
        "RESET": "\033[0m",
        "CYAN": "\033[36m",
        "YELLOW": "\033[33m",
        "GREEN": "\033[32m",
        "RED": "\033[31m",
        "BOLD": "\033[1m",
    }

    def format(self, record):
        color = self.COLORS["CYAN"]
        level_color = self.COLORS["YELLOW"] if record.levelno == logging.INFO else self.COLORS["RED"]
        time_str = datetime.now().strftime("%H:%M:%S")
        msg = f"{self.COLORS['BOLD']}{level_color}[{time_str}] {record.levelname:<8}{self.COLORS['RESET']} {color}{record.getMessage()}{self.COLORS['RESET']}"
        return msg


# Инициализация логгера
logger = logging.getLogger("bot_logger")
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter())
logger.setLevel(logging.INFO)
logger.addHandler(handler)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        chat_id = None
        username = None
        text = None
        event_type = type(event).__name__

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            username = event.from_user.username if event.from_user else None
            chat_id = event.chat.id if event.chat else None
            text = event.text or event.caption

        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            username = event.from_user.username
            chat_id = event.message.chat.id if event.message else None
            text = event.data

        logger.info(
            f"📨 {event_type:<12} | 👤 {username or user_id} | 💬 {text or '(no text)'} | 🧩 Handler → {handler.__name__}"
        )

        return await handler(event, data)
