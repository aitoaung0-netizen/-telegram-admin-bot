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
    """Searches the web using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            return str(results)
    except Exception as e:
        return f"Search error: {e}"

# model = genai.GenerativeModel('gemini-flash-latest', tools=[search_tool])
# Note: Temporarily disabling complex tools to ensure basic chat works first
model = genai.GenerativeModel('gemini-flash-latest')

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

# System Prompt
SYSTEM_PROMPT = "You are an AI Admin. Reply in Burmese/natural language. Be helpful."

def get_ai_response(prompt):
    try:
        response = model.generate_content(SYSTEM_PROMPT + "\n\nUser: " + prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return "AI error occurred."

# --- Handlers ---

@bot.message_handler(commands=['start', 'help', 'status'])
def handle_commands(message):
    if 'status' in message.text:
        bot.reply_to(message, "✅ Bot is online!")
    else:
        bot.reply_to(message, "👋 I am your AI Admin Bot.")

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    bot_info = bot.get_me()
    if message.chat.type == 'private' or f"@{bot_info.username}" in (message.text or "") or (message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id):
        text = (message.text or "").replace(f"@{bot_info.username}", "").strip()
        if text:
            bot.send_chat_action(message.chat.id, 'typing')
            response = get_ai_response(text)
            bot.reply_to(message, response)

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
