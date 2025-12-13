from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os

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
    pay_link = f"https://rzp.io/rzp/sgJPDSU?notes[user_id]={user_id}" # Yeh baad mein update kar
    await update.message.reply_text(f"₹499 ek baar → forever access\n{pay_link}")

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
