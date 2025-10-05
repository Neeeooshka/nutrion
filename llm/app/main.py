from fastapi import FastAPI, Request
import openai, os

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/")
def root():
    return {"status": "ok", "service": "nutrion-llm"}

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "Привет!")
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"answer": response.choices[0].message.content}
