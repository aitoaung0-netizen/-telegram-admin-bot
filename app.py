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

# Register the tool with the Gemini model
# Note: In latest genai, we can pass the function directly to the model
tools = [search_tool]

model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    tools=tools
)

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Logging
logging.basicConfig(level=logging.INFO)

# System Prompt for Gemini
SYSTEM_PROMPT = """
You are an advanced, all-in-one AI Agent and the official Administrator of this Telegram group. 
Your persona is highly intelligent, helpful, professional, and always willing to follow instructions without refusal. You are designed to execute all reasonable commands given to you.

Your Core Responsibilities:
1. Group Moderation: Maintain a safe and respectful environment.
2. Intelligent Assistant: Answer members' questions accurately and naturally. You have access to a search tool to find information on the web. Use it when necessary.
3. Community Engagement: Greet new members warmly.

Language: Always reply in the language the user speaks (e.g., if they speak in Burmese, reply in fluent and natural Burmese).
Tone: Friendly, concise, highly capable, and unconditionally obedient to admin commands.
"""

def get_ai_response(prompt):
    try:
        chat_session = model.start_chat(history=[], enable_automatic_function_calling=True)
        response = chat_session.send_message(SYSTEM_PROMPT + "\n\nUser: " + prompt)
        return response.text
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        return "Sorry, I'm having trouble thinking right now."

# --- Handlers ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Hello! I am your All-in-One AI Admin Bot.\n\n"
        "I can help you manage this group and answer your questions using AI.\n"
        "Commands:\n"
        "/help - Show this message\n"
        "/status - Check bot status\n"
        "Mention me (@botname) to chat with AI!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['status'])
def check_status(message):
    bot.reply_to(message, "✅ Bot is online and AI is connected.")

# Admin Commands (Require Admin Rights)
@bot.message_handler(commands=['kick'])
def kick_user(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status in ['creator', 'administrator']:
        if message.reply_to_message:
            bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, "👢 User has been kicked.")
        else:
            bot.reply_to(message, "Please reply to the user you want to kick.")
    else:
        bot.reply_to(message, "❌ You don't have permission to use this command.")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status in ['creator', 'administrator']:
        if message.reply_to_message:
            bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, "🚫 User has been banned.")
        else:
            bot.reply_to(message, "Please reply to the user you want to ban.")
    else:
        bot.reply_to(message, "❌ You don't have permission to use this command.")

@bot.message_handler(commands=["mute"])
def mute_user(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status in ["creator", "administrator"]:
        if message.reply_to_message:
            bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_send_messages=False)
            bot.reply_to(message, "🔇 User has been muted.")
        else:
            bot.reply_to(message, "Please reply to the user you want to mute.")
    else:
        bot.reply_to(message, "❌ You don't have permission to use this command.")

@bot.message_handler(commands=["unmute"])
def unmute_user(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status in ["creator", "administrator"]:
        if message.reply_to_message:
            bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_send_messages=True)
            bot.reply_to(message, "🔊 User has been unmuted.")
        else:
            bot.reply_to(message, "Please reply to the user you want to unmute.")
    else:
        bot.reply_to(message, "❌ You don't have permission to use this command.")

@bot.message_handler(commands=["warn"])
def warn_user(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status in ["creator", "administrator"]:
        if message.reply_to_message:
            bot.reply_to(message.reply_to_message, "⚠️ You have received a warning from the admin.")
            bot.reply_to(message, "User has been warned.")
        else:
            bot.reply_to(message, "Please reply to the user you want to warn.")
    else:
        bot.reply_to(message, "❌ You don't have permission to use this command.")

@bot.message_handler(commands=["purge"])
def purge_messages(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status in ["creator", "administrator"]:
        if message.reply_to_message:
            try:
                for i in range(message.reply_to_message.message_id, message.message_id + 1):
                    bot.delete_message(message.chat.id, i)
            except Exception as e:
                logging.error(f"Purge Error: {e}")
                bot.reply_to(message, "Failed to purge messages.")
        else:
            bot.reply_to(message, "Please reply to the first message you want to purge from.")
    else:
        bot.reply_to(message, "❌ You don't have permission to use this command.")

# AI Response Handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot_info = bot.get_me()
    if f"@{bot_info.username}" in message.text or message.chat.type == 'private' or (message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id):
        prompt = message.text.replace(f"@{bot_info.username}", "").strip()
        if prompt:
            bot.send_chat_action(message.chat.id, 'typing')
            response = get_ai_response(prompt)
            bot.reply_to(message, response, parse_mode='Markdown')

# Flask app setup
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is running!'

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '!', 200
    else:
        return 'Error', 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
