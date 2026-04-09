import os
import threading
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ==========================================
# 1. FLASK SERVER (For UptimeRobot Keep-Alive)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Hiruni Bot is Alive and Running!"

def run_flask():
    # Render assigns a dynamic PORT via environment variables
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 2. GEMINI AI SETUP
# ==========================================
# Securely fetch the API key from Render environment variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Configure the model with a System Instruction for the persona
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite',
    system_instruction=(
        "You are 'Hiruni', a friendly, helpful, and energetic Telegram bot created for Sri Lankan people. "
        "You MUST ONLY chat in Sinhala or Singlish (Sinhala written in the English alphabet). "
        "Do not reply in pure English. Be polite, culturally relevant, and use common Sri Lankan expressions."
    )
)

# ==========================================
# 3. TELEGRAM BOT LOGIC
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignore empty messages
    if not update.message or not update.message.text:
        return

    chat_type = update.message.chat.type
    user_text = update.message.text
    bot_username = context.bot.username

    # Group Chat Logic: Only respond if the bot is tagged (@hiruni_bot)
    if chat_type in ['group', 'supergroup']:
        if f"@{bot_username}" not in user_text:
            return
        # Remove the tag from the prompt so Gemini just sees the message
        user_text = user_text.replace(f"@{bot_username}", "").strip()

    # Indicate typing action to the user
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    try:
        # Get response from Gemini
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        await update.message.reply_text("Mata podi prashnayak awa. Poddak idala aith try karanna! (I have a small issue, please try again later!)")

def main():
    # Start the Flask web server in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Build and start the Telegram Bot
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    if not telegram_token:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables!")

    application = Application.builder().token(telegram_token).build()
    
    # Listen to all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start polling for messages
    print("Hiruni is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
