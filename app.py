import telebot
import google.generativeai as genai
import logging
import os
import sys
import io
import collections
import random
from flask import Flask, request
from duckduckgo_search import DDGS
from PIL import Image
from gtts import gTTS

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "7778399973:AAEH2BU6hBHUqseWfdw2kNcX_OFZNYoFoes")
BOSS_ID = 6780671216

# Gemini API Keys for Rotation
GEMINI_KEYS = [
    "AQ.Ab8RN6LrYDk7IdMQkSy3FeSF47AjeDdHyUonKOg5GbdxmHhCAg", "AIzaSyBVxmMoGMUMHGWAuWkWLYYSfxTAt78l8MA", 
    "AIzaSyDLuno7IDzYi7r5jJJ_Gtg3WMk7OiwbikA", "AIzaSyCMhTzhZE40xG9RHKsGvfCPPRzeSfJOZAI", 
    "AIzaSyCCQXOCj8g0hPIdhfwjxXrLKulzNWcgJc4", "AIzaSyDR1pqYK6-mVkBpbEwJ1FN5xYs-JzN1yl4", 
    "AIzaSyA5k0k5QpdPla8jFkRfWzESqXxus46hdCo", "AIzaSyAKopjylbpEZw-XjcyShkIo5ivvabJYeFs", 
    "AIzaSyDZguqnyAxgLRvIIlEtU6UgpJef23-ZuEA", "AIzaSyDNd5l2uNHa0WQwgblNlX-pdXplHnHLC-U", 
    "AIzaSyDkznXJVOQHaCEWjt3BD3tyGdLNIXXaWoA", "AIzaSyAy6Hzd8s3UaFXe_BV5mQQ0iGvU7HjJJZA", 
    "AIzaSyBGqwA0coCkZxPk9QzEbkLXKHvC6FeZeLw", "AIzaSyAbGsTxqwtCnO6_qJSdn8H4u1jOWZMtd1o", 
    "AIzaSyDPVInWX51SKRPvyYYC_sKOMgbUNPO2FDg", "AIzaSyBVNnfsDRWluJ3taWDCrdrYnPFvHSgQHow", 
    "AIzaSyBMQkuijLk2Xrmg7kxmngNCmbZBWuuMIG4", "AIzaSyBRWnI66hm5o-SdraFvSUmRPmXWdV69ESo", 
    "AIzaSyCV5xWKk7kOKlKaVpGc8JydtNqrIsyJtjY", "AIzaSyB6QWhz3bZ6H9beWKOPwSg3gxUO478OYGU", 
    "AIzaSyAl5ae8aW48riv85MLbJ3K0ZSy0KvxAmcg", "AIzaSyAn973WZULRzpegCil0WQ6xc1Yld1R67kI", 
    "AIzaSyAKEvl9yTsElK_M7Gk5THpDrfk3ownGVZs", "AIzaSyAPcHJkro9YBmtxQsxcl2Zd4n1vJFTbMCM", 
    "AIzaSyBr6p6WbkLQllfYpnBaZDmKfM-aGt9Atd8", "AIzaSyDiNdMxpM01nC9dcMAjjQ8NK_lIYRaPoTc", 
    "AIzaSyC77gy3Lyt4Bs3RDlXslwT9r_4jaQAirqs", "AIzaSyCphtgJVapLYjCL510ScgHXitUKqo4YbEE", 
    "AIzaSyAPklbG0zT53bmgC7-EmPnrqIzuoM6qZrw", "AIzaSyANzUUBm_y6WDz9UuMenaFwrt3d4uim23k", 
    "AIzaSyCzHY7kBaepmAUOP043aAYlOLszMF3J51M", "AIzaSyDkxmG6F2JwVa6buI-U3wYg7-vGyv6VZ70", 
    "AIzaSyDHRlj-rMVoRt0ciwRceQG274yiUafv_Ek"
]

chat_memories = collections.defaultdict(lambda: collections.deque(maxlen=10))

def search_tool(query: str) -> str:
    try:
        with DDGS() as ddgs:
            return str([r for r in ddgs.text(query, max_results=3)])
    except: return "Search failed."

def get_ai_response(chat_id, user_id, prompt, image=None):
    keys = list(GEMINI_KEYS)
    random.shuffle(keys)
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-flash-latest', tools=[search_tool])
            is_boss = (user_id == BOSS_ID)
            instr = "You are speaking to your BOSS. Be extremely obedient." if is_boss else "You are an AI Admin. Be helpful."
            instr += " Always reply in natural Burmese."
            
            chat = model.start_chat(enable_automatic_function_calling=True)
            content = [f"{instr}\n\nContext:\n" + "\n".join(list(chat_memories[chat_id])) + f"\n\nUser: {prompt}"]
            if image: content.append(image)
                
            response = chat.send_message(content)
            chat_memories[chat_id].append(f"User: {prompt}")
            chat_memories[chat_id].append(f"AI: {response.text}")
            return response.text
        except: continue
    return "အဆင်မပြေဖြစ်နေပါတယ် Boss။"

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

def send_voice_response(chat_id, text, reply_to_id=None):
    try:
        tts = gTTS(text=text, lang='my', slow=False) # slow=False for faster speech
        voice_io = io.BytesIO()
        tts.write_to_fp(voice_io)
        voice_io.seek(0)
        bot.send_voice(chat_id, voice_io, reply_to_message_id=reply_to_id)
    except Exception as e:
        logger.error(f"TTS Error: {e}")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    bot.send_chat_action(message.chat.id, 'record_audio')
    response_text = get_ai_response(message.chat.id, message.from_user.id, "User sent a voice message. Please respond.")
    send_voice_response(message.chat.id, response_text, message.message_id)

@bot.message_handler(content_types=['photo', 'text'])
def handle_all(message):
    bot_info = bot.get_me()
    text = message.text or message.caption or ""
    if message.chat.type == 'private' or f"@{bot_info.username}" in text or (message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id):
        prompt = text.replace(f"@{bot_info.username}", "").strip()
        bot.send_chat_action(message.chat.id, 'typing')
        img = None
        if message.photo:
            file_info = bot.get_file(message.photo[-1].file_id)
            img = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
        
        response = get_ai_response(message.chat.id, message.from_user.id, prompt or "Describe this image", img)
        
        # Voice Command Logic
        voice_keywords = ["အသံနဲ့ဖြေ", "စကားပြော", "voice", "audio", "ပြောပြပါ"]
        should_voice = any(kw in text.lower() for kw in voice_keywords)
        
        if should_voice:
            send_voice_response(message.chat.id, response, message.message_id)
        else:
            bot.reply_to(message, response, parse_mode='Markdown')

# Admin handlers
@bot.message_handler(commands=['kick', 'ban', 'mute', 'unmute', 'warn', 'purge'])
def admin_cmds(message):
    if message.from_user.id != BOSS_ID and bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['creator', 'administrator']: return
    cmd = message.text.split()[0][1:]
    try:
        target = message.reply_to_message.from_user.id if message.reply_to_message else None
        if cmd == 'kick' and target: bot.kick_chat_member(message.chat.id, target)
        elif cmd == 'ban' and target: bot.ban_chat_member(message.chat.id, target)
        elif cmd == 'mute' and target: bot.restrict_chat_member(message.chat.id, target, can_send_messages=False)
        elif cmd == 'unmute' and target: bot.restrict_chat_member(message.chat.id, target, can_send_messages=True)
        elif cmd == 'purge' and message.reply_to_message:
            for i in range(message.reply_to_message.message_id, message.message_id + 1):
                try: bot.delete_message(message.chat.id, i)
                except: pass
        bot.reply_to(message, "✅ Done!")
    except: pass

app = Flask(__name__)
@app.route('/')
def index(): return 'Smart Voice AI Bot is Active!'
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return 'OK', 200
    return 'Error', 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
