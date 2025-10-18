# llm/services/ollama_service.py
import os
import asyncio
import aiohttp
import json
import logging
from typing import AsyncIterator
from .llm_service import BaseLLMService
from config import SYSTEM_PROMPT, TEMPERATURE, MAX_TOKENS

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

class OllamaService(BaseLLMService):
    """Асинхронный сервис для работы с Ollama"""
    
    def __init__(self, model: str = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        self._is_available = False
        self.logger = logging.getLogger("nutrition-llm")
        self._buffer = ""
    
    async def ask(self, prompt: str, context: str = "") -> dict:
        self.logger.info(f"⚙️ Отправляем запрос к Ollama ({self.model}) через aiohttp")
        
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},  # Здесь остаётся
                {"role": "user", "content": f"Контекст: {context}\n\nВопрос: {prompt}"},
            ],
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS
            },
            "stream": False  # for non-stream
        }
        
        text_accum = ""
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=300)
                async with session.post(url, json=payload, timeout=timeout) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"Ошибка HTTP {resp.status}: {error_text}")
                        return self._format_error(f"HTTP {resp.status}: {error_text}")
                    
                    response_data = await resp.json()
                    text_accum = response_data.get("message", {}).get("content", "")
                    self.logger.info(f"✅ Получен ответ длиной {len(text_accum)} символов")
                    return self._format_response(text_accum, self.model)
        except Exception as e:
            self.logger.exception(f"Неожиданная ошибка: {e}")
            return self._format_error(str(e))
    
    async def ask_stream(self, prompt: str, context: str = "") -> AsyncIterator[str]:
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},  # Здесь остаётся
                {"role": "user", "content": f"Контекст: {context}\n\nВопрос: {prompt}"},
            ],
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS
            },
            "stream": True
        }
        text_accum = ""
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=300)
                async with session.post(url, json=payload, timeout=timeout) as resp:
                    async for chunk_bytes in resp.content.iter_any():
                        chunk_text = chunk_bytes.decode('utf-8')
                        self._buffer += chunk_text
                        while '\n' in self._buffer:
                            line, self._buffer = self._buffer.split('\n', 1)
                            if not line.strip(): continue
                            try:
                                chunk_data = json.loads(line)
                                if "message" in chunk_data and "content" in chunk_data["message"]:
                                    piece = chunk_data["message"]["content"]
                                    yield piece
                                    text_accum += piece
                                if chunk_data.get("done", False):
                                    self._last_full_response = text_accum
                                    return
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"Не удалось распарсить JSON: {line}, ошибка: {e}")
                                continue
        except Exception as e:
            self.logger.exception(f"Неожиданная ошибка: {e}")
            err = self._format_error(str(e))
            yield f"Ошибка: {err}"
             
    def get_last_full_response(self) -> str:
        return getattr(self, '_last_full_response', '')
    
    async def health_check(self) -> bool:
        """Проверка здоровья Ollama"""
        url = f"{OLLAMA_HOST}/api/tags"
        self.logger.info(f"Проверка доступности Ollama...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        self._is_available = True
                        self.logger.info(f"✅ Ollama доступен")
                        return True
                    else:
                        self.logger.warning(f"❌ Ollama недоступен, статус: {resp.status}")
                        self._is_available = False
                        return False
        except Exception as e:
            self.logger.warning(f"❌ Ollama недоступен: {e}")
            self._is_available = False
            return False

    async def is_available(self) -> bool:
        """Проверка доступности Ollama"""
        return await self.health_check()