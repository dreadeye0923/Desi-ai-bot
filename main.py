from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
import redis

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL) if REDIS_URL else None

class Query(BaseModel):
    user_id: str
    prompt: str

async def call_groq(prompt: str):
    api_key = os.getenv("GROQ_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_KEY not set")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024
            },
            timeout=60
        )

        # 🔥 helpful debug
        if resp.status_code != 200:
            print(resp.text)

        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


@app.post("/query")
async def handle_query(q: Query):
    if not r:
        raise HTTPException(status_code=500, detail="Redis not configured")

    if not r.get(f"paid:{q.user_id}"):
        raise HTTPException(status_code=402, detail="Payment required")

    reply = await call_groq(q.prompt)
    return {"reply": reply}

@app.get("/health")
async def health():
    return {"status": "alive"}
