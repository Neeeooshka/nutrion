import os
import asyncio
import aiohttp
import json
import logging
from .llm_service import BaseLLMService
from config import SYSTEM_PROMPT, TEMPERATURE, MAX_TOKENS

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

class OllamaService(BaseLLMService):
    """Асинхронный сервис для работы с Ollama"""
    
    def __init__(self, model: str = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")  # Динамическая модель
        self._is_available = False
        self.logger = logging.getLogger("nutrition-llm")
        self._buffer = ""  # Буфер для неполных JSON

    async def ask(self, prompt: str, context: str = "") -> dict:
        """Асинхронный запрос к Ollama через HTTP стрим"""
        self.logger.info(f"⚙️ Отправляем запрос к Ollama ({self.model}) через aiohttp")
        
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
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
                # Устанавливаем увеличенный таймаут
                timeout = aiohttp.ClientTimeout(total=300)  # 5 минут
                
                async with session.post(url, json=payload, timeout=timeout) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"Ошибка HTTP {resp.status}: {error_text}")
                        return self._format_error(f"HTTP {resp.status}: {error_text}")
                    
                    async for chunk_bytes in resp.content.iter_any():
                        if not chunk_bytes:
                            continue
                            
                        chunk_text = chunk_bytes.decode('utf-8')
                        self._buffer += chunk_text
                        
                        # Обрабатываем все полные JSON объекты из буфера
                        while '\n' in self._buffer:
                            line, self._buffer = self._buffer.split('\n', 1)
                            line = line.strip()
                            if not line:
                                continue
                                
                            try:
                                chunk_data = json.loads(line)
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"Не удалось распарсить JSON: {line}, ошибка: {e}")
                                continue
                            
                            # Обрабатываем данные чанка
                            if "message" in chunk_data and "content" in chunk_data["message"]:
                                piece = chunk_data["message"]["content"]
                                text_accum += piece
                                self.logger.debug(f"💬 Получен чанк: {piece.strip()}")
                            
                            if chunk_data.get("done", False):
                                self.logger.info(f"✅ Получен ответ длиной {len(text_accum)} символов")
                                self._buffer = ""  # Очищаем буфер
                                return self._format_response(text_accum, self.model)
                    
                    # Если поток завершился, но мы не получили done
                    if text_accum:
                        self.logger.info(f"⚠️ Поток завершился без флага done. Ответ: {len(text_accum)} символов")
                        return self._format_response(text_accum, self.model)
                    else:
                        return self._format_error("Пустой ответ от модели")
                        
        except asyncio.TimeoutError:
            self.logger.warning("⚠️ Превышен таймаут ожидания ответа от Ollama")
            return self._format_error("Истек таймаут ожидания от модели")
        except aiohttp.ClientError as e:
            self.logger.error(f"Ошибка HTTP при обращении к Ollama: {e}")
            return self._format_error(str(e))
        except Exception as e:
            self.logger.exception(f"Неожиданная ошибка: {e}")
            return self._format_error(str(e))

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