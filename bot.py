import requests
import json
import os
from flask import Flask, request

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not set!")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

app = Flask(__name__)

# ================ DATABASE ================
SERIES_DB = {
    "rick_and_morty": {
        "title": "Rick and Morty",
        "episodes": {
            "1": "PLACEHOLDER_EP1",
            "2": "PLACEHOLDER_EP2",
        }
    }
}

# ================ HELPERS =================
def send_message(chat_id, text, buttons=None):
    data = {"chat_id": chat_id, "text": text}
    if buttons:
        data["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    response = requests.post(BASE_URL + "sendMessage", data=data)
    print("📤 Send message response:", response.text)  # Debug log

def generate_series_buttons():
    buttons = []
    for code, data in SERIES_DB.items():
        buttons.append([{
            "text": data["title"],
            "callback_data": f"series:{code}"
        }])
    return buttons

# ================ WEBHOOK =================
@app.route("/webhook", methods=["POST"])
def webhook():
    print("🔥 Webhook triggered!")  # Debug log

    update = request.get_json()
    print("📥 Incoming update:", update)  # Debug log

    if not update:
        return "no update"

    message = update.get("message")

    if message:
        chat_id = message["chat"]["id"]
        text = message.get("text", "").lower()

        print(f"📩 Message received: {text}")

        if text == "/start":
            buttons = generate_series_buttons()
            send_message(chat_id, "✅ Welcome! Select a series:", buttons)

    return "ok"

@app.route("/")
def home():
    return "Bot is running!"

# ================= RUN SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
