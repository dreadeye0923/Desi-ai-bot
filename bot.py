from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os
import httpx

BASE_URL = os.getenv("BASE_URL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Desi Unlimited AI\n"
        "Llama 70B (Groq) - super fast & smart\n"
        "₹499 lifetime - limited slots\n\n"
        "/buy kar aur shuru!"
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    amount_inr = 499
    
    # OxaPay invoice create (dynamic har user ke liye)
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.oxapay.com/merchants/request",
            json={
                "merchant_api_key": "TERA_OXAPAY_API_KEY",  # yaha paste kar
                "amount": amount_inr,
                "currency": "INR",
                "description": "Lifetime Unlimited Llama AI Access",
                "order_id": f"ai_bot_{user_id}",
                "callback_url": "https://your-railway-url.com/webhook"  # optional baad mein
            }
        )
        data = resp.json()
        if data["result"] == 1:
            pay_link = data["payLink"]
        else:
            pay_link = "https://oxapay.com"  # fallback
    
    await update.message.reply_text(
        f"🔥 ₹{amount_inr} Lifetime Access\n"
        f"USDT ya crypto se pay kar (auto INR convert)\n\n"
        f"{pay_link}\n\n"
        f"Payment success hone ke 2 min baad unlimited access unlock ho jaayega!"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    prompt = update.message.text

    try:
        resp = requests.post(
            f"{BASE_URL}/query",
            json={"user_id": user_id, "prompt": prompt},
            timeout=120
        )

        if resp.status_code == 402:
            await update.message.reply_text("Pay kar pehle → /buy")
            return

        if resp.status_code != 200:
            await update.message.reply_text(f"Error {resp.status_code}: {resp.text}")
            return

        await update.message.reply_text(resp.json()["reply"])

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


application = Application.builder().token(os.getenv("TG_TOKEN")).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("buy", buy))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.run_polling()
