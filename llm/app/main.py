from fastapi import FastAPI, Request, HTTPException
import os
import traceback
from openai import OpenAI
from config import SYSTEM_PROMPT, MODEL, DEFAULT_PROMPT

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

@app.get("/")
def root():
    return {"status": "ok", "service": "nutrition-llm"}

@app.post("/ask")
async def ask(request: Request):
    # ✅ Проверяем API-ключ
    key = request.headers.get("X-API-Key")
    if key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

    data = await request.json()
    prompt = data.get("prompt", DEFAULT_PROMT)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,          # креативность
            max_output_tokens=400,    # длина ответа
        )
        answer = response.choices[0].message.content
        return {"answer": answer}

    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        print("🔥 Ошибка при запросе к OpenAI:")
        print(stack_trace)
        return {"error": error_message, "trace": stack_trace}
