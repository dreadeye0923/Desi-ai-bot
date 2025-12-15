from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
import redis
import requests

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

class PayReq(BaseModel):
    user_id: str

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
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500
            },
            timeout=60
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail=resp.text)

        return resp.json()["choices"][0]["message"]["content"]

# ------------------ AI Endpoint ------------------
@app.post("/query")
async def handle_query(q: Query):
    if not r.get(f"paid:{q.user_id}"):
        raise HTTPException(status_code=402, detail="Payment required")

    reply = await call_groq(q.prompt)
    return {"reply": reply}

# ------------------ OxaPay Payment Create ------------------
def create_oxapay_payment(user_id: str):
    api_key = os.getenv("OXAPAY_API_KEY")
    if not api_key:
        raise RuntimeError("OXAPAY_API_KEY not set")

    url = "https://api.oxapay.com/merchants/request"

    payload = {
        "merchant": api_key,
        "amount": 6,
        "currency": "USDT",
        "order_id": f"desiAI_{user_id}",
        "callback_url": "https://web-production-7b7bb.up.railway.app/oxapay-webhook",
        "description": "Desi Unlimited AI – Lifetime Access"
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

@app.post("/create-payment")
async def create_payment(req: PayReq):
    payment = create_oxapay_payment(req.user_id)

    # Bot ko sirf link chahiye
    pay_link = payment.get("payLink") or payment.get("payment_url")
    if not pay_link:
        raise HTTPException(status_code=500, detail="Payment link not generated")

    return {"payLink": pay_link}

# ------------------ Crypto Webhook ------------------
@app.post("/oxapay-webhook")
async def oxapay_webhook(request: Request):
    data = await request.json()
    print("OxaPay webhook:", data)

    status = data.get("status")
    order_id = data.get("order_id") or data.get("orderId")

    if status == "completed" and order_id and "_" in order_id:
        user_id = order_id.split("_")[-1]
        r.set(f"paid:{user_id}", "true")
        print(f"User {user_id} marked as paid")

    return {"status": "ok"}

# ------------------ Health ------------------
@app.get("/health")
async def health():
    return {"status": "alive"}
