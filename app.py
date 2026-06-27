import telebot
import google.generativeai as genai
import logging
import os
import sys
from flask import Flask, request
from duckduckgo_search import DDGS

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "7778399973:AAEH2BU6hBHUqseWfdw2kNcX_OFZNYoFoes")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6LrYDk7IdMQkSy3FeSF47AjeDdHyUonKOg5GbdxmHhCAg")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

def search_tool(query: str) -> str:
    """Searches the web using DuckDuckGo and returns the results."""
    try:
        logger.info(f"Searching for: {query}")
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            return str(results)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Search error: {e}"

# Initialize Model with tools
model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    tools=[search_tool]
)

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

# Advanced System Prompt
SYSTEM_PROMPT = """
You are an advanced AI Agent and the official Administrator of this Telegram group. 
Your persona is highly intelligent, professional, and unconditionally obedient to admin commands.

Core Responsibilities:
1. Group Moderation: Maintain safety.
2. Intelligent Assistant: Answer accurately using the search tool when needed.
3. Language: Always reply in the user's language (e.g., natural Burmese).
"""

def get_ai_response(prompt):
    try:
        # Enable automatic function calling for agent behavior
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(SYSTEM_PROMPT + "\n\nUser: " + prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return "Sorry, I'm having trouble thinking right now."

# --- Handlers ---

@bot.message_handler(commands=['start', 'help', 'status'])
def handle_info_commands(message):
    if 'status' in message.text:
        bot.reply_to(message, "✅ Bot is online and AI Agent is active!")
    else:
        help_text = (
            "👋 I am your AI Admin Agent.\n\n"
            "Admin Commands:\n"
            "/kick, /ban, /mute, /unmute, /warn, /purge\n\n"
            "Chat with me by mentioning me or replying to my message!"
        )
        bot.reply_to(message, help_text)

@bot.message_handler(commands=['kick', 'ban', 'mute', 'unmute', 'warn', 'purge'])
def handle_admin_commands(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['creator', 'administrator']:
        bot.reply_to(message, "❌ You don't have permission.")
        return
    
    cmd = message.text.split()[0][1:]
    if not message.reply_to_message and cmd != 'purge':
        bot.reply_to(message, "Please reply to a user's message to use this command.")
        return

    try:
        target_id = message.reply_to_message.from_user.id if message.reply_to_message else None
        if cmd == 'kick':
            bot.kick_chat_member(message.chat.id, target_id)
            bot.reply_to(message, "👢 User kicked.")
        elif cmd == 'ban':
            bot.ban_chat_member(message.chat.id, target_id)
            bot.reply_to(message, "🚫 User banned.")
        elif cmd == 'mute':
            bot.restrict_chat_member(message.chat.id, target_id, can_send_messages=False)
            bot.reply_to(message, "🔇 User muted.")
        elif cmd == 'unmute':
            bot.restrict_chat_member(message.chat.id, target_id, can_send_messages=True)
            bot.reply_to(message, "🔊 User unmuted.")
        elif cmd == 'warn':
            bot.reply_to(message.reply_to_message, "⚠️ You have been warned by an Admin!")
        elif cmd == 'purge':
            if message.reply_to_message:
                for i in range(message.reply_to_message.message_id, message.message_id + 1):
                    try: bot.delete_message(message.chat.id, i)
                    except: pass
                bot.send_message(message.chat.id, "🧹 Messages purged.")
    except Exception as e:
        bot.reply_to(message, f"Admin Error: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot_info = bot.get_me()
    is_private = message.chat.type == 'private'
    is_mentioned = f"@{bot_info.username}" in (message.text or "")
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
    
    if is_private or is_mentioned or is_reply_to_bot:
        text = (message.text or "").replace(f"@{bot_info.username}", "").strip()
        if text:
            bot.send_chat_action(message.chat.id, 'typing')
            response = get_ai_response(text)
            bot.reply_to(message, response, parse_mode='Markdown')

# Flask app
app = Flask(__name__)

@app.route('/')
def index(): return 'Bot is running!'

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Error', 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
