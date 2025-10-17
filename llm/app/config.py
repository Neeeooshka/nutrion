# llm/config.py
import os
from agents.nutrition import NutritionAgent
from agents.planning import PlanningAgent
from agents.simple import SimpleAgent

DEFAULT_PROMPT = "Привет! Я хочу совет по питанию и тренировкам."

SYSTEM_PROMPT = (
    "Ты — Нутрион, персональный AI-фитнес-ассистент и нутрициолог. "
    "Твоя миссия — помогать пользователю достигать целей: похудеть, "
    "набирать мышечную массу или поддерживать форму. "
    "Отвечай кратко, по существу, с дружелюбным и мотивирующим тоном. "
    "Не используй избыточные вводные фразы, избегай воды. "
    "Если пользователь просит меню — составь примерный рацион с КБЖУ. "
    "Если речь о тренировках — предложи реалистичные упражнения по уровню."
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

MAX_TOKENS = 800
TEMPERATURE = 0.7
OLLAMA_TIMEOUT = 30

AGENT_CLASSES = [
    NutritionAgent,
    PlanningAgent,
    SimpleAgent,
    # Добавь будущие: from agents.image_processing import ImageProcessingAgent; AGENT_CLASSES.append(ImageProcessingAgent)
]