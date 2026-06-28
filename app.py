import telebot
import google.generativeai as genai
import logging
import os
import sys
import io
import collections
import random
import time
from flask import Flask, request
from duckduckgo_search import DDGS
from PIL import Image
from gtts import gTTS
from datetime import datetime, timedelta, timezone

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
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

# Gemini Keys Handling (Support both GEMINI_KEYS and GEMINI_API_KEYS)
raw_keys = os.environ.get("GEMINI_KEYS") or os.environ.get("GEMINI_API_KEYS") or ""
GEMINI_KEYS = [k.strip().strip("'").strip('"') for k in raw_keys.split(",") if k.strip()]

logger.info(f"DEBUG: Found {len(GEMINI_KEYS)} Gemini keys.")

chat_memories = collections.defaultdict(lambda: collections.deque(maxlen=10))

def get_myanmar_time():
    mm_tz = timezone(timedelta(hours=6, minutes=30))
    return datetime.now(mm_tz).strftime("%Y-%m-%d %I:%M:%S %p")

def search_tool(query: str) -> str:
    try:
        with DDGS() as ddgs:
            return str([r for r in ddgs.text(query, max_results=3)])
    except: return "Search failed."

def get_ai_response(chat_id, user_id, prompt, image=None):
    if not GEMINI_KEYS:
        return "Boss ရေ... Render ရဲ့ Environment Variables မှာ GEMINI_KEYS ဒါမှမဟုတ် GEMINI_API_KEYS ထည့်ဖို့ လိုအပ်နေပါတယ်ခင်ဗျာ။"
        
    keys = list(GEMINI_KEYS)
    random.shuffle(keys)
    current_time = get_myanmar_time()
    
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash', tools=[search_tool])
            
            is_boss = (user_id == BOSS_ID)
            instr = "You are speaking to your BOSS. Be extremely obedient." if is_boss else "You are an AI Admin. Be helpful."
            instr += f" Always reply in natural Burmese. The current Myanmar time is {current_time}."
            
            chat = model.start_chat(enable_automatic_function_calling=True)
            content = [f"{instr}\n\nContext:\n" + "\n".join(list(chat_memories[chat_id])) + f"\n\nUser: {prompt}"]
            if image: content.append(image)
                
            response = chat.send_message(content)
            chat_memories[chat_id].append(f"User: {prompt}")
            chat_memories[chat_id].append(f"AI: {response.text}")
            return response.text
        except Exception as e:
            logger.error(f"Gemini Key Error with key {key[:10]}...: {str(e)}")
            continue
    return "အဆင်မပြေဖြစ်နေပါတယ် Boss။ Key အားလုံး Quota ပြည့်နေတာ ဒါမှမဟုတ် ပိတ်ခံထားရပုံရပါတယ်။ Render Logs ကို စစ်ဆေးပေးပါဦး။"

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

def send_voice_response(chat_id, text, reply_to_id=None):
    try:
        tts = gTTS(text=text, lang='my', slow=False)
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
    try:
        bot_info = bot.get_me()
        text = message.text or message.caption or ""
        
        is_private = message.chat.type == 'private'
        is_mentioned = f"@{bot_info.username}" in text
        is_reply_to_bot = (message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id)
        
        if is_private or is_mentioned or is_reply_to_bot:
            prompt = text.replace(f"@{bot_info.username}", "").strip()
            bot.send_chat_action(message.chat.id, 'typing')
            img = None
            if message.photo:
                file_info = bot.get_file(message.photo[-1].file_id)
                img = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
            
            response = get_ai_response(message.chat.id, message.from_user.id, prompt or "Describe this image", img)
            
            voice_keywords = ["အသံနဲ့ဖြေ", "စကားပြော", "voice", "audio", "ပြောပြပါ"]
            should_voice = any(kw in text.lower() for kw in voice_keywords)
            
            if should_voice:
                send_voice_response(message.chat.id, response, message.message_id)
            else:
                try:
                    bot.reply_to(message, response, parse_mode='Markdown')
                except:
                    bot.reply_to(message, response)
    except Exception as e:
        logger.error(f"Bot Handle Error: {e}")

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
def index():
    return 'Smart Voice AI Bot is Active and Healthy!', 200

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Error', 403

if __name__ == '__main__':
    # Webhook ကို အော်တို ချိတ်ဆက်ခြင်း
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TELEGRAM_TOKEN}"
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    else:
        logger.warning("RENDER_EXTERNAL_URL not found. Webhook not set automatically.")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
