from fastapi import FastAPI
import redis
import os

app = FastAPI()
r = redis.from_url(os.getenv("REDIS_URL"))

@app.post("/oxapay-webhook")
async def oxapay_webhook(request: Request):
    data = await request.json()
    if data.get("status") == "completed":
        order_id = data["orderId"]
        user_id = order_id.split("_")[-1]
        r.set(f"paid:{user_id}", "true")
    return {"status": "ok"}
