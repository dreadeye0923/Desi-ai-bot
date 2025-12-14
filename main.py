from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
import redis

app = FastAPI()

# ------------------ Redis ------------------
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

r = redis.from_url(REDIS_URL, decode_responses=True)

# ------------------ Models ------------------
class Query(BaseModel):
    user_id: str
    prompt: str

# ------------------ Groq Call ------------------
async def call_groq(prompt: str):
    api_key = os.getenv("GROQ_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_KEY not set")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama3-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            },
            timeout=60
        )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Groq error: {resp.text}"
            )

        return resp.json()["choices"][0]["message"]["content"]

# ------------------ AI Endpoint ------------------
@app.post("/query")
async def handle_query(q: Query):
    if not r.get(f"paid:{q.user_id}"):
        raise HTTPException(status_code=402, detail="Payment required")

    reply = await call_groq(q.prompt)
    return {"reply": reply}

# ------------------ Crypto Webhook ------------------
@app.post("/oxapay-webhook")
async def oxapay_webhook(request: Request):
    data = await request.json()

    # Example payload handling
    if data.get("status") == "completed":
        order_id = data.get("orderId", "")
        user_id = order_id.split("_")[-1]

        r.set(f"paid:{user_id}", "true")

    return {"status": "ok"}

# ------------------ Health ------------------
@app.get("/health")
async def health():
    return {"status": "alive"}
