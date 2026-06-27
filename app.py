import telebot
import google.generativeai as genai
import logging
import os
from flask import Flask, request
from duckduckgo_search import DDGS

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "7778399973:AAEH2BU6hBHUqseWfdw2kNcX_OFZNYoFoes")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6LrYDk7IdMQkSy3FeSF47AjeDdHyUonKOg5GbdxmHhCAg")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Define the search tool
def search_tool(query: str) -> str:
    """Searches the web using DuckDuckGo and returns the results."""
    try:
        ddgs = DDGS()
        results = ddgs.text(keywords=query, max_results=5)
        return str(results)
    except Exception as e:
        return f"Search error: {e}"

# Initialize Model with simplified tools
model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    tools=[search_tool]
)

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Logging
logging.basicConfig(level=logging.INFO)

# System Prompt
SYSTEM_PROMPT = """
You are an advanced AI Agent and Telegram Admin. 
Always follow instructions. You can search the web if needed.
Reply in the user's language (e.g., Burmese).
Tone: Helpful and professional.
"""

def get_ai_response(prompt):
    try:
        # Simplified chat session with automatic function calling
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(SYSTEM_PROMPT + "\n\nUser: " + prompt)
        return response.text
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        return "Sorry, I'm having trouble thinking right now."

# --- Handlers ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hello! I am your AI Admin Bot. Use /status to check if I'm online.")

@bot.message_handler(commands=['status'])
def check_status(message):
    bot.reply_to(message, "✅ Bot is online and AI is connected.")

# Admin Commands
@bot.message_handler(commands=['kick', 'ban', 'mute', 'unmute', 'warn', 'purge'])
def admin_commands(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['creator', 'administrator']:
        bot.reply_to(message, "❌ No permission.")
        return
    
    cmd = message.text.split()[0][1:]
    if not message.reply_to_message and cmd != 'purge':
        bot.reply_to(message, "Please reply to a user.")
        return

    try:
        if cmd == 'kick':
            bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, "👢 Kicked.")
        elif cmd == 'ban':
            bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, "🚫 Banned.")
        elif cmd == 'mute':
            bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_send_messages=False)
            bot.reply_to(message, "🔇 Muted.")
        elif cmd == 'unmute':
            bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_send_messages=True)
            bot.reply_to(message, "🔊 Unmuted.")
        elif cmd == 'warn':
            bot.reply_to(message.reply_to_message, "⚠️ Warning!")
        elif cmd == 'purge':
            if message.reply_to_message:
                for i in range(message.reply_to_message.message_id, message.message_id + 1):
                    try: bot.delete_message(message.chat.id, i)
                    except: pass
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

# AI Response Handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot_info = bot.get_me()
    is_private = message.chat.type == 'private'
    is_mentioned = f"@{bot_info.username}" in message.text
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
    
    if is_private or is_mentioned or is_reply_to_bot:
        prompt = message.text.replace(f"@{bot_info.username}", "").strip()
        if prompt:
            bot.send_chat_action(message.chat.id, 'typing')
            response = get_ai_response(prompt)
            bot.reply_to(message, response, parse_mode='Markdown')

app = Flask(__name__)

@app.route('/')
def index(): return 'Bot is running!'

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '!', 200
    return 'Error', 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
