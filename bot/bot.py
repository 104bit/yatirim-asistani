"""
Telegram Bot for Financial Research Agent
==========================================
Webhook-based bot for Render deployment.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from react_agent import run_react_agent

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "")

app = Flask(__name__)


def format_for_telegram(text: str) -> str:
    """
    Convert standard markdown to Telegram-compatible format.
    Telegram uses a simpler markdown syntax.
    """
    import re
    
    # Remove ### headings, keep text
    text = re.sub(r'^###\s*', '📊 ', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s*', '📈 ', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s*', '🔹 ', text, flags=re.MULTILINE)
    
    # Convert **bold** to *bold* (Telegram style)
    text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
    
    # Remove code blocks markers
    text = re.sub(r'```[a-z]*\n?', '', text)
    
    # Clean up extra newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def get_bot_app():
    """Create Telegram application."""
    return Application.builder().token(TELEGRAM_TOKEN).build()


async def start_command(update: Update, context):
    """Handle /start command."""
    welcome_message = """
🤖 **Finansal Araştırma Asistanı**

Merhaba! Ben yatırım araştırma botuyum.

**Örnek sorular:**
• Altın alınır mı?
• Bitcoin analizi yap
• Banka sektörü nasıl?
• THYAO vs SAHOL karşılaştır
• Dolar kuru nedir?

Herhangi bir finansal soru sorabilirsiniz!
"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def handle_message(update: Update, context):
    """Handle user messages with progress updates."""
    user_message = update.message.text
    chat_id = update.message.chat_id
    
    # Send initial status message
    status_msg = await update.message.reply_text(
        "🔍 *Sorgunuz analiz ediliyor...*",
        parse_mode="Markdown"
    )
    
    try:
        # Update status - analyzing query
        await status_msg.edit_text(
            "🧠 *Düşünüyorum...*\n\n"
            f"📝 Soru: _{user_message}_",
            parse_mode="Markdown"
        )
        
        # Send typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Update status - working
        await status_msg.edit_text(
            "⚙️ *Veri topluyorum ve analiz ediyorum...*\n\n"
            f"📝 Soru: _{user_message}_\n\n"
            "🔹 Piyasa verileri çekiliyor\n"
            "🔹 Haberler taranıyor\n"
            "🔹 Teknik analiz yapılıyor",
            parse_mode="Markdown"
        )
        
        # Run the financial research agent
        report = run_react_agent(user_message)
        
        # Delete status message
        await status_msg.delete()
        
        # Format report for Telegram
        formatted_report = format_for_telegram(report)
        
        # Send final response (split if too long)
        if len(formatted_report) > 4000:
            for i in range(0, len(formatted_report), 4000):
                await update.message.reply_text(formatted_report[i:i+4000])
        else:
            await update.message.reply_text(formatted_report)
            
    except Exception as e:
        # Update status with error
        await status_msg.edit_text(
            f"❌ *Bir hata oluştu*\n\n`{str(e)[:100]}`",
            parse_mode="Markdown"
        )


@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates via webhook."""
    import asyncio
    
    update = Update.de_json(request.get_json(), Bot(TELEGRAM_TOKEN))
    
    async def process():
        # Create and initialize application
        bot_app = get_bot_app()
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Initialize before processing
        await bot_app.initialize()
        
        try:
            await bot_app.process_update(update)
        finally:
            await bot_app.shutdown()
    
    asyncio.run(process())
    
    return "OK", 200


@app.route("/")
def health():
    """Health check endpoint."""
    return "Bot is running!", 200


@app.route("/set_webhook")
def set_webhook():
    """Set webhook URL."""
    import asyncio
    
    if not WEBHOOK_URL:
        return "RENDER_EXTERNAL_URL not set", 400
    
    webhook_url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    bot = Bot(TELEGRAM_TOKEN)
    
    async def set_hook():
        await bot.set_webhook(webhook_url)
    
    asyncio.run(set_hook())
    return f"Webhook set to {webhook_url}", 200


if __name__ == "__main__":
    # Local testing with polling
    import asyncio
    
    print("Starting bot in polling mode (local testing)...")
    
    async def main():
        app_bot = get_bot_app()
        app_bot.add_handler(CommandHandler("start", start_command))
        app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        await app_bot.initialize()
        await app_bot.start()
        await app_bot.updater.start_polling()
        
        print("Bot is running! Press Ctrl+C to stop.")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await app_bot.stop()
    
    asyncio.run(main())
