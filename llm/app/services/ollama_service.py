import os
import asyncio
import aiohttp
import json
import logging
from .llm_service import BaseLLMService
from config import OLLAMA_MODEL, SYSTEM_PROMPT, TEMPERATURE, MAX_TOKENS

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

class OllamaService(BaseLLMService):
    """Асинхронный сервис для работы с Ollama"""

    def __init__(self):
        self.model = OLLAMA_MODEL
        self._is_available = False
        self.logger = logging.getLogger("nutrition-llm")

    async def ask(self, prompt: str, context: str = "") -> dict:
        """Асинхронный запрос к Ollama через HTTP стрим"""
        self.logger.info(f"⚙️ Отправляем запрос к Ollama ({self.model}) через aiohttp")

        full_prompt = f"{SYSTEM_PROMPT}\n\nКонтекст: {context}\n\nВопрос: {prompt}"

        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt},
            ],
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS
            ],
            "stream": True
        }

        text_accum = ""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=None)) as resp:
                    async for line in resp.content:
                        line = line.decode("utf-8").strip()
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            # бывает, что стрим шлёт куски без \n между ними
                            continue

                        if "message" in chunk and "content" in chunk["message"]:
                            piece = chunk["message"]["content"]
                            text_accum += piece
                            self.logger.debug(f"💬 {piece.strip()}")

                        if chunk.get("done"):
                            break

            self.logger.info(f"✅ Получен ответ длиной {len(text_accum)} символов")
            return self._format_response(text_accum, self.model)

        except asyncio.TimeoutError:
            self.logger.warning("⚠️ Превышен таймаут ожидания ответа от Ollama")
            return self._format_error("Истек таймаут ожидания от модели")
        except aiohttp.ClientError as e:
            self.logger.error(f"Ошибка HTTP при обращении к Ollama: {e}")
            return self._format_error(str(e))
        except Exception as e:
            self.logger.exception(e)
            return self._format_error(str(e))

    async def is_available(self) -> bool:
        """Проверка доступности Ollama"""
        return await self.health_check()

    async def health_check(self) -> bool:
        """Проверка здоровья Ollama"""
        url = f"{OLLAMA_HOST}/api/generate"
        self.logger.info(f"Проверка доступности модели {self.model}...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"model": self.model, "prompt": "ping", "stream": False}) as resp:
                    if resp.status == 200:
                        self._is_available = True
                        self.logger.info(f"✅ Модель {self.model} доступна")
                        return True
        except Exception as e:
            self.logger.warning(f"❌ Ollama недоступна: {e}")

        self._is_available = False
        return False
