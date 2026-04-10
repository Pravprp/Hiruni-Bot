import os
import time
import threading
import asyncio
import random
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Import the new features
from joke import get_random_joke
from poem import get_random_poem
from quote import get_random_quote

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
    model_name='gemini-2.5-flash-lite', # Make sure this works in your region/account!
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

active_sessions = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat.id
    user_text = update.message.text
    user_text_lower = user_text.lower()
    current_time = time.time()
    bot_username = (await context.bot.get_me()).username

    is_reply_to_bot = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.username == bot_username:
            is_reply_to_bot = True

    # Step 1: Check activation status
    is_active = False
    if chat_id in active_sessions:
        if current_time < active_sessions:
            is_active = True
        else:
            del active_sessions

    # Step 2: Handle "stop" 
    if "stop" in user_text_lower and is_active and is_reply_to_bot:
        if chat_id in active_sessions:
            del active_sessions
        await update.message.reply_text("Hari, man den yanawa! 😴💤💤")
        return

    # Step 3: Handle "hiruni" activation
    if "hiruni" in user_text_lower:
        active_sessions = current_time + 300 
        is_active = True
    elif not (is_active and is_reply_to_bot):
        return

    # Step 4: Handle Jokes, Poems, and Quotes (Only if replying & active)
    custom_reply = None
    if is_active and is_reply_to_bot:
        if "joke" in user_text_lower:
            custom_reply = get_random_joke()
        elif "poem" in user_text_lower:
            custom_reply = get_random_poem()
        elif "quote" in user_text_lower:
            custom_reply = get_random_quote()

    # If it's a custom command, send the predefined text and skip AI
    if custom_reply:
        read_delay = random.randint(1, 2)
        await asyncio.sleep(read_delay)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        type_delay = random.randint(2, 4)
        await asyncio.sleep(type_delay)
        
        await update.message.reply_text(custom_reply)
        
        # Reset the 5-minute timer since the user interacted
        active_sessions = time.time() + 300 
        return

    # Step 5: Process with Gemini (If no custom triggers were hit)
    read_delay = random.randint(2, 4)
    await asyncio.sleep(read_delay)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    type_delay = random.randint(3, 6)
    await asyncio.sleep(type_delay)

    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
        
        # Reset the 5-minute timer on a successful AI chat too
        active_sessions = time.time() + 300
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
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Hiruni is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
