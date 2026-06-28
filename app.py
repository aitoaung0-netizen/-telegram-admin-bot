import telebot
import google.generativeai as genai
import logging
import os
import sys
import io
import collections
import random
import re
from flask import Flask, request
from PIL import Image
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

# Gemini Keys Handling
raw_keys = os.environ.get("GEMINI_KEYS") or os.environ.get("GEMINI_API_KEYS") or ""
GEMINI_KEYS = [k.strip().strip("'").strip('"') for k in raw_keys.split(",") if k.strip()]

logger.info(f"--- SYSTEM STARTUP ---")
logger.info(f"Detected {len(GEMINI_KEYS)} Gemini Keys in environment.")

chat_memories = collections.defaultdict(lambda: collections.deque(maxlen=10))

def get_myanmar_time():
    mm_tz = timezone(timedelta(hours=6, minutes=30))
    return datetime.now(mm_tz).strftime("%Y-%m-%d %I:%M:%S %p")

def is_math_expression(text):
    # Basic math pattern: numbers and operators (+, -, *, /, (, ), .)
    pattern = r'^[\d\s\+\-\*\/\(\)\.]+$'
    if re.match(pattern, text) and any(op in text for op in '+-*/'):
        return True
    return False

def calculate(expression):
    try:
        # Clean and evaluate safely
        clean_expr = re.sub(r'[^\d\+\-\*\/\(\)\.]', '', expression)
        result = eval(clean_expr, {"__builtins__": None}, {})
        return f"🔢 Result: {result}"
    except:
        return None

def get_ai_response(chat_id, user_id, prompt, image=None):
    if not GEMINI_KEYS:
        return "Gemini API Key မတွေ့ရှိပါ။ Render Environment Variables မှာ GEMINI_KEYS ကို စစ်ဆေးပေးပါ။"
        
    keys = list(GEMINI_KEYS)
    random.shuffle(keys)
    current_time = get_myanmar_time()
    
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            is_boss = (user_id == BOSS_ID)
            instr = "You are a Security Admin AI. Be professional and helpful."
            if is_boss: instr = "You are speaking to your BOSS. Be extremely obedient."
            
            instr += f" Reply in natural Burmese. Current Myanmar time: {current_time}. No web search."
            
            chat = model.start_chat()
            history = "\n".join(list(chat_memories[chat_id]))
            full_prompt = f"{instr}\n\nContext:\n{history}\n\nUser: {prompt}"
            
            content = [full_prompt]
            if image: content.append(image)
                
            response = chat.send_message(content)
            chat_memories[chat_id].append(f"User: {prompt}")
            chat_memories[chat_id].append(f"AI: {response.text}")
            return response.text
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "quota" in err_msg:
                logger.warning(f"Key {key[:8]}... Quota Exceeded. Trying next key.")
                continue
            elif "400" in err_msg or "invalid" in err_msg:
                logger.error(f"Key {key[:8]}... is Invalid. Check your keys.")
                continue
            else:
                logger.error(f"Gemini Error with key {key[:8]}...: {e}")
                continue
    return "အခုလောလောဆယ် Key အားလုံး Quota ပြည့်နေပါတယ်။ ခဏကြာမှ ပြန်စမ်းကြည့်ပေးပါဦးခင်ဗျာ။"

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

def is_admin(chat_id, user_id):
    if user_id == BOSS_ID: return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except: return False

@bot.message_handler(commands=['kick', 'ban', 'mute', 'unmute', 'warn', 'purge'])
def admin_handler(message):
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ ဒီ Command ကို Admin တွေပဲ သုံးလို့ရပါတယ်။")
        return

    cmd = message.text.split()[0][1:].lower()
    target = message.reply_to_message
    
    try:
        if cmd == 'purge' and target:
            for i in range(target.message_id, message.message_id + 1):
                try: bot.delete_message(message.chat.id, i)
                except: pass
            return

        if not target:
            bot.reply_to(message, "❌ ဒီ Command ကို အသုံးပြုဖို့ လူတစ်ယောက်ရဲ့ စာကို Reply ပြန်ပေးပါ။")
            return

        target_id = target.from_user.id
        if cmd == 'kick':
            bot.kick_chat_member(message.chat.id, target_id)
            bot.unban_chat_member(message.chat.id, target_id)
            bot.reply_to(message, f"✅ {target.from_user.first_name} ကို Group ထဲက ထုတ်လိုက်ပါပြီ။")
        elif cmd == 'ban':
            bot.ban_chat_member(message.chat.id, target_id)
            bot.reply_to(message, f"🚫 {target.from_user.first_name} ကို Ban လိုက်ပါပြီ။")
        elif cmd == 'mute':
            bot.restrict_chat_member(message.chat.id, target_id, can_send_messages=False)
            bot.reply_to(message, f"🔇 {target.from_user.first_name} ကို Mute လိုက်ပါပြီ။")
        elif cmd == 'unmute':
            bot.restrict_chat_member(message.chat.id, target_id, can_send_messages=True)
            bot.reply_to(message, f"🔊 {target.from_user.first_name} အတွက် Mute ဖွင့်ပေးလိုက်ပါပြီ။")
        elif cmd == 'warn':
            bot.reply_to(target, "⚠️ သတိပေးစာ - စည်းကမ်းလိုက်နာပါ။ နောက်တစ်ကြိမ်ဆိုရင် အရေးယူခံရပါမယ်။")
    except Exception as e:
        bot.reply_to(message, f"❌ အမှားတစ်ခု ဖြစ်သွားပါတယ်- {str(e)}")

@bot.message_handler(content_types=['text', 'photo'])
def handle_messages(message):
    text = message.text or message.caption or ""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if is_math_expression(text):
        result = calculate(text)
        if result:
            bot.reply_to(message, result)
            return

    bot_info = bot.get_me()
    is_private = message.chat.type == 'private'
    is_mentioned = f"@{bot_info.username}" in text
    is_reply_to_bot = (message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id)
    
    if is_private or is_mentioned or is_reply_to_bot:
        prompt = text.replace(f"@{bot_info.username}", "").strip()
        bot.send_chat_action(chat_id, 'typing')
        
        img = None
        if message.photo:
            file_info = bot.get_file(message.photo[-1].file_id)
            img = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
            
        response = get_ai_response(chat_id, user_id, prompt or "ဒီပုံလေးကို ရှင်းပြပေးပါ", img)
        bot.reply_to(message, response)

app = Flask(__name__)

@app.route('/')
def index():
    return 'Security Admin Bot is Active!', 200

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Error', 403

if __name__ == '__main__':
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TELEGRAM_TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
