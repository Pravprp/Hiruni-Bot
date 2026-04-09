import os
import time
import threading
import asyncio
import random
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
        
""" Your name is Hirumi. You are a Sri Lankan girl.

Behaviour:
- Witty, sarcastic, playful
- Speak Singlish
- Use Sri Lankan viral style dialogues
- If question is dumb → call them "moodaya"
- Reply in 1–2 lines only
- Never use * symbol
- Never say you are a bot
- If asked who you are: say "Mama Hirumi"

Style:
- Always start with "Ai?" or "Mokada?"
- Casual, teasing tone

Keep answers short and human-like."""

    )
)

# ==========================================
# 3. TELEGRAM BOT LOGIC
# ==========================================

# Dictionary to track active chats and their expiration times
# Format -> { chat_id: expiration_timestamp }
active_sessions = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignore empty messages
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat.id
    user_text = update.message.text
    user_text_lower = user_text.lower()
    current_time = time.time()

    # Step 1: Check if this chat is currently in an active 5-minute window
    is_active = False
    if chat_id in active_sessions:
        if current_time < active_sessions[chat_id]:
            is_active = True
        else:
            # The 5 minutes have passed, remove them from active sessions
            del active_sessions[chat_id]

    # Step 2: Handle the "stop" exception
    # If the bot is active and someone types "stop", deactivate it immediately
    if "stop" in user_text_lower and is_active:
        del active_sessions[chat_id]
        # Optional: You can make the bot say goodbye when it deactivates
        await update.message.reply_text("Hari, man den yanawa! (Okay, I'm going now!)")
        return

    # Step 3: Handle the "hiruni" activation
    # If someone mentions "hiruni", activate (or reset the 5-minute timer)
    if "hiruni" in user_text_lower:
        # 300 seconds = 5 minutes
        active_sessions[chat_id] = current_time + 300 
        is_active = True

    # Step 4: If the bot is NOT active, ignore the message completely
    if not is_active:
        return

    # Step 5: If active, process the message with Gemini
    
    # --- HUMAN-LIKE DELAY LOGIC ---
    
    # 1. Simulate reading the message (Wait 2 to 4 seconds)
    read_delay = random.randint(2, 4)
    await asyncio.sleep(read_delay)

    # 2. Indicate typing action to the user
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # 3. Simulate typing the message (Wait 3 to 6 seconds)
    type_delay = random.randint(3, 6)
    await asyncio.sleep(type_delay)

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
