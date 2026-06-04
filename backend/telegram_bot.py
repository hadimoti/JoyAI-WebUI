"""Telegram bot: catches verification codes users send to @differentjoy_bot.
Also handles /model command. Runs in a background thread."""
import threading, requests, time
from config import BOT_TOKEN, USERS, AVAILABLE_MODELS
import store

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def _username_from_tg(tg_user):
    uname = (tg_user.get("username") or "").lower()
    return uname if uname in USERS else None

def _send(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print("send error:", e)

def _handle_message(msg):
    text    = (msg.get("text") or "").strip()
    chat_id = msg["chat"]["id"]
    user    = _username_from_tg(msg.get("from", {}))

    # /model command -> list available models
    if text.startswith("/model"):
        names = ", ".join(m["name"] for m in AVAILABLE_MODELS)
        _send(chat_id, f"Available model(s): {names}")
        return

    # verification code (matches JOY-XXXX)
    if user and text.startswith("JOY-"):
        rec = store.telegram_codes.get(user)
        if rec and rec["code"] == text:
            rec["verified"] = True
            _send(chat_id, "✅ Account verified! Return to Joy AI in your browser. 🦊")
        else:
            _send(chat_id, "⚠️ Code not found or expired. Generate a new one in the WebUI.")
        return

    _send(chat_id, "Hi! 🦊 Send your JOY-XXXX code to verify, or /model to list models.")

def _poll_loop():
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{API}/getUpdates", params=params, timeout=40)
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                if "message" in upd:
                    _handle_message(upd["message"])
        except Exception as e:
            print("poll error:", e)
            time.sleep(3)

def start_bot():
    threading.Thread(target=_poll_loop, daemon=True).start()
    print("Telegram bot polling started.")
