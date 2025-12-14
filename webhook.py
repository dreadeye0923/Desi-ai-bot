from fastapi import FastAPI, Request
import redis
import os

app = FastAPI()

# ---------- Redis (SAFE INIT) ----------
REDIS_URL = os.getenv("REDIS_URL")
try:
    r = redis.from_url(REDIS_URL) if REDIS_URL else None
except Exception as e:
    print("Redis error:", e)
    r = None


@app.post("/oxapay-webhook")
async def oxapay_webhook(request: Request):
    data = await request.json()
    print("Webhook received:", data)

    if not r:
        return {"error": "Redis not configured"}

    status = data.get("status")
    order_id = data.get("orderId")

    # Accept all successful statuses
    if status in ["paid", "completed", "success"] and order_id:
        # BEST PRACTICE: orderId == telegram user_id
        user_id = str(order_id)

        r.set(f"paid:{user_id}", "true")
        print(f"User {user_id} marked as paid")

    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "webhook alive"}
