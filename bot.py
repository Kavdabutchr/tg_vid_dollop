import requests
import time
import json
import os

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set this in Railway Variables
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # Set this in Railway Variables

if not BOT_TOKEN or not CHANNEL_USERNAME:
    print("❌ ERROR: BOT_TOKEN or CHANNEL_USERNAME not set in Railway Variables.")
    exit()

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# ================ DATABASE ================
# Replace placeholders with your real Telegram file_ids later
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
    try:
        channel_status = requests.get(BASE_URL + "getChatMember", params={
            "chat_id": CHANNEL_USERNAME,
            "user_id": user_id
        }).json()

        valid = ["member", "administrator", "creator"]
        return channel_status["result"]["status"] in valid
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

    for item in updates["result"]:
        last_update_id = item["update_id"] + 1
        message = item.get("message")
        callback = item.get("callback_query")

        # --------- MESSAGE HANDLER ---------
        if message:
            chat_id = message["chat"]["id"]
            text = message.get("text", "").lower()
            user_id = message["from"]["id"]

            # START COMMAND
            if text == "/start":
                if not is_user_joined(user_id):
                    buttons = [
                        [{"text": "✅ Join Channel", "url": f"https://t.me/{CHANNEL_USERNAME[1:]}"}]
                    ]
                    send_message(chat_id, "🚫 You must join our channel first!", buttons)
                else:
                    buttons = generate_series_buttons()
                    send_message(chat_id, "✅ Welcome! Select a series below:", buttons)

            # LIST SERIES COMMAND
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

            # Check join again
            if not is_user_joined(user_id):
                buttons = [
                    [{"text": "✅ Join Channel", "url": f"https://t.me/{CHANNEL_USERNAME[1:]}"}]
                ]
                send_message(chat_id, "🚫 You must join our channel first!", buttons)
                continue

            # SERIES CLICKED
            if data.startswith("series:"):
                series_code = data.split(":")[1]
                buttons = generate_episode_buttons(series_code)
                send_message(chat_id, f"🎬 {SERIES_DB[series_code]['title']} Episodes:", buttons)

            # EPISODE CLICKED
            elif data.startswith("episode:"):
                parts = data.split(":")
                series_code = parts[1]
                ep = parts[2]

                file_id = SERIES_DB[series_code]["episodes"][ep]

                # Placeholder check
                if file_id.startswith("PLACEHOLDER"):
                    send_message(chat_id, f"🚧 {SERIES_DB[series_code]['title']} - Episode {ep} is coming soon!")
                else:
                    caption = f"✅ {SERIES_DB[series_code]['title']} - Episode {ep}"
                    send_video(chat_id, file_id, caption)

    time.sleep(1)
