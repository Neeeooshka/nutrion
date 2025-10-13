from fastapi import FastAPI, Request, HTTPException
import os
import traceback
from openai import OpenAI
from app.config import SYSTEM_PROMPT, MODEL, DEFAULT_PROMPT

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "service": "nutrition-llm"}

@app.post("/ask")
async def ask(request: Request):
    key = request.headers.get("X-API-Key")
    if key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    data = await request.json()
    prompt = data.get("prompt", DEFAULT_PROMPT)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_output_tokens=400
        )
        ai_text = response.choices[0].message['content']
        return {"answer": ai_text}

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
