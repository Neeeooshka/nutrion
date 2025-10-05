from fastapi import FastAPI, Request
import os
import traceback
from openai import OpenAI

app = FastAPI()

# Создаем клиент OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
def root():
    return {"status": "ok", "service": "nutrition-llm"}

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "Привет!")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        # В новой версии доступ к ответу через response.choices[0].message.content
        answer = response.choices[0].message.content
        return {"answer": answer}

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
