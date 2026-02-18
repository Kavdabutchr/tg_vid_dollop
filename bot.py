import requests
import time
import json
import os

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # Must be @channelusername
CHECK_INTERVAL = 1  # seconds between polling updates

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set! Add it in Render Environment Variables.")

print("🤖 Bot starting...")
print(f"BOT_TOKEN: {'Set' if BOT_TOKEN else 'Not Set'}")
print(f"CHANNEL_USERNAME: {CHANNEL_USERNAME if CHANNEL_USERNAME else 'Not Set'}")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# ================ DATABASE ================
SERIES_DB = {
    "rick_and_morty": {
        "title": "Rick and Morty",
        "episodes": {
            "1": "PLACEHOLDER_EP1",
            "2": "PLACEHOLDER_EP2",
            "3": "PLACEHOLDER_EP3",
        }
    },
    "american_dad": {
        "title": "American Dad",
        "episodes": {
            "1": "PLACEHOLDER_EP1",
            "2": "PLACEHOLDER_EP2",
        }
    }
}

# ================ HELPERS =================
def get_updates(offset=None):
    url = BASE_URL + "getUpdates"
    params = {"timeout": 100, "offset": offset}
    r = requests.get(url, params=params)
    return r.json()

def send_message(chat_id, text, buttons=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if buttons:
        data["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    requests.post(BASE_URL + "sendMessage", data=data)

def send_video(chat_id, file_id, caption=None):
    data = {"chat_id": chat_id, "video": file_id}
    if caption:
        data["caption"] = caption
    requests.post(BASE_URL + "sendVideo", data=data)

def is_user_joined(user_id):
    if not CHANNEL_USERNAME:
        return True  # Skip check if no channel set (testing)
    try:
        status = requests.get(BASE_URL + "getChatMember", params={
            "chat_id": CHANNEL_USERNAME,
            "user_id": user_id
        }).json()
        valid_status = ["member", "administrator", "creator"]
        return status["result"]["status"] in valid_status
    except:
        return False

def generate_series_buttons():
    buttons = []
    for code, data in SERIES_DB.items():
        buttons.append([{"text": data["title"], "callback_data": f"series:{code}"}])
    return buttons

def generate_episode_buttons(series_code):
    buttons = []
    episodes = SERIES_DB[series_code]["episodes"]
    for ep in episodes:
        buttons.append([{"text": f"Episode {ep}", "callback_data": f"episode:{series_code}:{ep}"}])
    return buttons

# ================ MAIN LOOP =================
last_update_id = None
print("🤖 Bot is running...")

while True:
    updates = get_updates(last_update_id)
    for item in updates.get("result", []):
        last_update_id = item["update_id"] + 1
        message = item.get("message")
        callback = item.get("callback_query")

        # --------- MESSAGE HANDLER ---------
        if message:
            chat_id = message["chat"]["id"]
            text = message.get("text", "").lower()
            user_id = message["from"]["id"]

            # /start command
            if text == "/start":
                if not is_user_joined(user_id):
                    buttons = [[{"text": "✅ Join Channel", "url": f"https://t.me/{CHANNEL_USERNAME[1:]}"}]]
                    send_message(chat_id, "🚫 You must join our channel first!", buttons)
                else:
                    buttons = generate_series_buttons()
                    send_message(chat_id, "✅ Welcome! Select a series below:", buttons)

            # /series command
            elif text == "/series":
                if not is_user_joined(user_id):
                    send_message(chat_id, "🚫 Join our channel first!")
                else:
                    buttons = generate_series_buttons()
                    send_message(chat_id, "🎬 Available Series:", buttons)

        # --------- CALLBACK HANDLER ---------
        elif callback:
            chat_id = callback["message"]["chat"]["id"]
            user_id = callback["from"]["id"]
            data = callback["data"]

            if not is_user_joined(user_id):
                buttons = [[{"text": "✅ Join Channel", "url": f"https://t.me/{CHANNEL_USERNAME[1:]}"}]]
                send_message(chat_id, "🚫 You must join our channel first!", buttons)
                continue

            # Series selected
            if data.startswith("series:"):
                series_code = data.split(":")[1]
                buttons = generate_episode_buttons(series_code)
                send_message(chat_id, f"🎬 {SERIES_DB[series_code]['title']} Episodes:", buttons)

            # Episode selected
            elif data.startswith("episode:"):
                _, series_code, ep = data.split(":")
                file_id = SERIES_DB[series_code]["episodes"][ep]

                if file_id.startswith("PLACEHOLDER"):
                    send_message(chat_id, f"🚧 {SERIES_DB[series_code]['title']} - Episode {ep} is coming soon!")
                else:
                    caption = f"✅ {SERIES_DB[series_code]['title']} - Episode {ep}"
                    send_video(chat_id, file_id, caption)

    time.sleep(CHECK_INTERVAL)
