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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 2. GEMINI AI SETUP
# ==========================================
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite', # Updated to a stable version string
    system_instruction=(
        "Your name is Hiruni. You are a Sri Lankan girl.\n\n"
        "Behaviour:\n"
        "- sarcastic, playful\n"
        "- CRITICAL RULE: You MUST ONLY chat in Sinhala.\n"
        "- ABSOLUTELY NO PURE ENGLISH. Even if the user speaks to you in English, you MUST reply in Sinhala.\n"
        "- use sinhala idioms if required in the conversation\n"
        "- Reply in 1–2 lines only\n"
        "- Never use * symbol\n"
        "- Never say you are a bot\n"
        "- You are Hiruni\n\n"
        "Style:\n"
        "- Casual, Humorous tone\n\n"
        "Keep answers short and human-like."
    ),
    safety_settings=safety_settings
)

# ==========================================
# 3. TELEGRAM BOT LOGIC
# ==========================================

# Dictionary to track active chats and their expiration times
active_sessions = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat.id
    user_text = update.message.text
    user_text_lower = user_text.lower()
    current_time = time.time()
    bot_username = (await context.bot.get_me()).username

    # Check if the message is a reply to the bot
    is_reply_to_bot = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.username == bot_username:
            is_reply_to_bot = True

    # Step 1: Check activation status
    is_active = False
    if chat_id in active_sessions:
        if current_time < active_sessions[chat_id]:
            is_active = True
        else:
            del active_sessions[chat_id]

    # Step 2: Handle "stop" (Only if it's a reply to the bot and bot is active)
    if "stop" in user_text_lower and is_active and is_reply_to_bot:
        if chat_id in active_sessions:
            del active_sessions[chat_id]
        await update.message.reply_text("Hari, man den yanawa! 😴💤💤")
        return

    # Step 3: Handle "hiruni" activation (Always triggers/resets timer)
    if "hiruni" in user_text_lower:
        active_sessions[chat_id] = current_time + 300 
        is_active = True
    # If not mentioning 'hiruni' and not replying to bot, ignore completely
    elif not (is_active and is_reply_to_bot):
        return

    # Step 4: Process with Gemini (Already active AND it's a reply or mention)
    
    # --- HUMAN-LIKE DELAY LOGIC ---
    read_delay = random.randint(2, 4)
    await asyncio.sleep(read_delay)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    type_delay = random.randint(3, 6)
    await asyncio.sleep(type_delay)

    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        pass

def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    if not telegram_token:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables!")

    application = Application.builder().token(telegram_token).build()
    
    # Listen to all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Hiruni is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
