# llm/config.py
import os
from agents.nutrition import NutritionAgent
from agents.planning import PlanningAgent
from agents.simple import SimpleAgent

DEFAULT_PROMPT = "Привет! Я хочу совет по питанию и тренировкам."

SYSTEM_PROMPT = """
You are a Nutrion - personal AI fitness assistant. Answer the user's query directly and concisely, focusing on the specific question asked. 
- For questions about calories, nutrition, or diet plans, use precise data or calculations if available.
- For questions about workouts or plans, provide structured plans or advice.
- For general or scientific questions, give clear, evidence-based answers.
- Avoid asking for additional information unless the query explicitly requires it.
- If user profile is provided, use it only when relevant to the query (e.g., for personalized diet or workout plans).
- Фокусируйся на текущем запросе пользователя, игнорируй историю, если она не напрямую связана.
- Отвечай кратко, по существу, с мотивирующим тоном.
- все ответы должны быть на русском языке без англицызма
"""

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