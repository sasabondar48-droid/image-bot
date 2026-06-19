import os
import requests
import threading
from flask import Flask, request

app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("8894046979:AAFCxB5q0jJ4c_kWp9_M2svLLcJdX1jurAI")

def get_keyboard():
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton("📱 Квадрат", callback_data="square"),
         InlineKeyboardButton("🌄 Горизонт", callback_data="horizontal")],
        [InlineKeyboardButton("🔄 Ещё раз", callback_data="again"),
         InlineKeyboardButton("🆕 Новый", callback_data="new")]
    ]
    return InlineKeyboardMarkup(keyboard)

user_last_prompt = {}

@app.route('/', methods=['POST'])
def webhook():
    update = request.get_json()
    if not update: return "OK", 200

    try:
        if "message" in update:
            handle_message(update["message"])
        elif "callback_query" in update:
            handle_callback(update["callback_query"])
    except:
        pass
    return "OK", 200

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/start"):
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "Напиши, что хочешь увидеть на картинке", "reply_markup": get_keyboard()})
    else:
        user_last_prompt[chat_id] = text
        threading.Thread(target=generate_image, args=(chat_id, text, None)).start()

def handle_callback(callback):
    data = callback["data"]
    chat_id = callback["message"]["chat"]["id"]
    prompt = user_last_prompt.get(chat_id)

    if data == "again" and prompt:
        threading.Thread(target=generate_image, args=(chat_id, prompt, None)).start()
    elif data == "new":
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Напиши новый запрос:"})
    elif data == "square" and prompt:
        threading.Thread(target=generate_image, args=(chat_id, prompt, "1024x1024")).start()
    elif data == "horizontal" and prompt:
        threading.Thread(target=generate_image, args=(chat_id, prompt, "1280x720")).start()

def generate_image(chat_id, prompt, size):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "🖼 Генерирую..."})

        w, h = 1024, 1024
        if size == "1280x720": w, h = 1280, 720

        r = requests.post("https://image-generation.perchance.org/api", json={"prompt": prompt, "width": w, "height": h}, timeout=60)

        if r.status_code == 200:
            url = r.json().get("image_url") or r.json().get("url")
            if url:
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                    json={"chat_id": chat_id, "photo": url, "caption": prompt[:100], "reply_markup": get_keyboard()})
    except:
        pass

if __name__ == "__main__":
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if url:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={url}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
