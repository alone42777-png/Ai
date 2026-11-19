import os
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CLOUD_URL = "http://127.0.0.1:8000"
CLOUD_API_KEY = os.environ["CLOUD_API_KEY"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سڵاو! من ALONE CLOUD AI ـم. پرسیارەکەت بنێرە.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    payload = {"messages": [{"role": "user", "content": question}]}
    headers = {"Authorization": f"Bearer {CLOUD_API_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=100) as client:
            response = await client.post(f"{CLOUD_URL}/v1/chat/completions",
                                         json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        answer = data["choices"][0]["message"]["content"]
        await update.message.reply_text(answer[:4000])
    except Exception:
        await update.message.reply_text("ببورە، کێشەیەک لە پەیوەندی بە Cloud هەیە.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()

if __name__ == "__main__":
    main()
