from fastapi import FastAPI, Request, HTTPException
import os
import traceback
import logging
import sys
from openai import OpenAI
from app.config import SYSTEM_PROMPT, MODEL, DEFAULT_PROMPT

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

# Настраиваем logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("nutrition-llm")

@app.get("/")
def root():
    return {"status": "ok", "service": "nutrition-llm"}

@app.post("/ask")
async def ask(request: Request):
    key = request.headers.get("X-API-Key")
    if key != INTERNAL_API_KEY:
        logger.warning("Неавторизованный запрос!")
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    data = await request.json()
    prompt = data.get("prompt", DEFAULT_PROMPT)
    context = data.get("context", "")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{context}\n{prompt}"}
            ],
            temperature=0.7,
            max_output_tokens=400
        )
        ai_text = response.choices[0].message['content']
        logger.info("Ответ успешно получен от модели.")
        return {"answer": ai_text}

    except Exception as e:
        logger.error(f"Ошибка OpenAI API: {e}")
        logger.debug(traceback.format_exc())
        return {"error": str(e)}
