from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
import redis

app = FastAPI()

# ---------- Redis setup (SAFE) ----------
REDIS_URL = os.getenv("REDIS_URL")
try:
    r = redis.from_url(REDIS_URL) if REDIS_URL else None
except Exception as e:
    print("Redis connection error:", e)
    r = None


# ---------- Request model ----------
class Query(BaseModel):
    user_id: str
    prompt: str


# ---------- Groq call ----------
async def call_groq(prompt: str):
    api_key = os.getenv("GROQ_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_KEY not set")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512
            }
        )

        if resp.status_code != 200:
            print("Groq error:", resp.text)

        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ---------- API endpoint ----------
@app.post("/query")
async def handle_query(q: Query):
    # Redis must be available
    if not r:
        raise HTTPException(status_code=503, detail="Service unavailable")

    # Check payment
    paid = r.get(f"paid:{q.user_id}")
    if not paid:
        raise HTTPException(status_code=402, detail="Payment required")

    try:
        reply = await call_groq(q.prompt)
        return {"reply": reply}
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="AI service error")


# ---------- Health check ----------
@app.get("/health")
async def health():
    return {"status": "alive"}
