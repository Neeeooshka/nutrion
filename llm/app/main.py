from fastapi import FastAPI, Request
import openai
import os
import traceback

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/")
def root():
    return {"status": "ok", "service": "nutrition-llm"}

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "Привет!")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"answer": response.choices[0].message.content}

    except Exception as e:
        # Подробный вывод ошибки
        error_message = str(e)
        stack_trace = traceback.format_exc()

        print("🔥 Ошибка при запросе к OpenAI:")
        print(stack_trace)

        return {
            "error": error_message,
            "trace": stack_trace
        }
