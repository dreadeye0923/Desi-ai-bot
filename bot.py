from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os

BASE_URL = os.getenv("BASE_URL")

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await update.message.reply_text(
        "🔥 Desi Unlimited AI\n"
        "Llama 8B Instant (Groq) – super fast & smart\n"
        "₹499 lifetime access\n\n"
        f"🆔 Your user id: {user_id}\n\n"
        "/buy to get started!"
    )

# ---------------- BUY ----------------
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    try:
        resp = requests.post(
            f"{BASE_URL}/create-payment",
            json={"user_id": user_id},
            timeout=30
        )

        pay_link = resp.json().get("payLink")
        if not pay_link:
            await update.message.reply_text("❌ Payment Link not generating")
            return

        await update.message.reply_text(
            "💸 Crypto payment (anonymous) USDT TRC20\n"
            "₹499 lifetime access\n\n"
            f"{pay_link}\n\n"
            "Auto Unlock after Payment ✅"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ---------------- CHAT ----------------
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
            await update.message.reply_text("Buy first → /buy")
            return

        if resp.status_code != 200:
            await update.message.reply_text("Server error, try after some time")
            return

        await update.message.reply_text(resp.json()["reply"])

    except Exception:
        await update.message.reply_text("Busy, try after 10 sec")

# ---------------- APP ----------------
application = Application.builder().token(os.getenv("TG_TOKEN")).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("buy", buy))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

application.run_polling()
