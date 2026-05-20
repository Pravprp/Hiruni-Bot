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

system_instruction = (
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
)

# Define models in the exact fallback order requested
FALLBACK_MODELS = [
    'gemini-3.5-flash',
    'gemini-2.5-flash',
    'gemini-3.1-flash-lite',
    'gemini-2.5-flash-lite',
    'gemini-3-flash'
]

# Pre-initialize all models to save overhead during chat processing
ai_models = [
    genai.GenerativeModel(
        model_name=name,
        system_instruction=system_instruction,
        safety_settings=safety_settings
    ) for name in FALLBACK_MODELS
]

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

    # Identify if the message contains one of the special trigger words
    is_trigger_word = "joke" in user_text_lower or "poem" in user_text_lower or "quote" in user_text_lower

    # Step 1: Check activation status
    is_active = False
    if chat_id in active_sessions:
        if current_time < active_sessions[chat_id]:
            is_active = True
        else:
            del active_sessions[chat_id]

    # Step 2: Handle "stop" 
    if "stop" in user_text_lower and is_active and is_reply_to_bot:
        if chat_id in active_sessions:
            del active_sessions[chat_id]
        await update.message.reply_text("Hari, man den yanawa! 😴💤💤")
        return

    # Step 3: Handle "hiruni" activation and message filtering
    if "hiruni" in user_text_lower:
        active_sessions[chat_id] = current_time + 300 
        is_active = True
    elif not is_active:
        # If the bot isn't active, ignore everything
        return
    elif not is_reply_to_bot and not is_trigger_word:
        # If active, ignore messages UNLESS it's a reply to the bot OR contains a trigger word
        return

    # Step 4: Handle Jokes, Poems, and Quotes 
    custom_reply = None
    if is_active:
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
        active_sessions[chat_id] = time.time() + 300 
        return

    # Step 5: Process with Gemini Fallback Logic
    read_delay = random.randint(2, 4)
    await asyncio.sleep(read_delay)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    type_delay = random.randint(3, 6)
    await asyncio.sleep(type_delay)

    success = False
    
    # Iterate through the pre-initialized models
    for i, current_model in enumerate(ai_models):
        try:
            # Switched to generate_content_async to prevent blocking the event loop
            response = await current_model.generate_content_async(user_text)
            await update.message.reply_text(response.text)
            
            # Reset the 5-minute timer on a successful AI chat
            active_sessions[chat_id] = time.time() + 300
            success = True
            
            # Print to console for monitoring which model is currently succeeding
            print(f"Request succeeded using: {FALLBACK_MODELS[i]}")
            break # Exit the loop immediately upon a successful response
            
        except Exception as e:
            # Log the failure and continue to the next model in the list
            print(f"[Warning] Model {FALLBACK_MODELS[i]} failed: {e}")
            continue 

    # If all models in the fallback list fail
    if not success:
        print("[Error] All Gemini models failed to generate a response.")
        # Optionally, notify the user that the bot is experiencing issues gracefully
        # await update.message.reply_text("Mata dan poddak mahansiy, passe katha karamu! 🤕")

def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    if not telegram_token:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables!")

    application = Application.builder().token(telegram_token).build()
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Hiruni is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
