from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
import redis

app = FastAPI()
r = redis.from_url(os.getenv("REDIS_URL"))

class Query(BaseModel):
    user_id: str
    prompt: str

async def call_groq(prompt: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_KEY')}"},
            json={
                "model": "llama3-70b-8192",  # Best chat model abhi, GPT level reasoning
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000
            },
            timeout=60
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

@app.post("/query")
async def handle_query(q: Query):
    if not r.get(f"paid:{q.user_id}"):
        raise HTTPException(status_code=402, detail="Payment required → /buy")
    
    reply = await call_groq(q.prompt)
    return {"reply": reply}

@app.get("/health")
async def health():
    return {"status": "alive"}
