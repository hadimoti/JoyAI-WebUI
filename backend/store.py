"""Simple JSON-file based storage for approved emails, codes, tokens, and group chat."""
import json, os, secrets, time
from config import APPROVED_EMAILS_FILE, DATA_DIR

os.makedirs(DATA_DIR, exist_ok=True)

# In-memory stores (reset on restart — fine for verification codes)
email_codes    = {}   # user -> {"code": "123456", "email": "..", "exp": ts}
telegram_codes = {}   # user -> {"code": "JOY-1234", "verified": False}
sms_codes      = {}   # user -> {"code": "123456", "exp": ts}
tokens         = {}   # token -> user

# Telegram avatar cache (in-memory, 5-min TTL)
_avatar_cache  = {}   # username -> {"url": str|None, "exp": float}

# Group chat file
GROUP_CHAT_FILE = os.path.join(DATA_DIR, "group_chat.json")
_GROUP_MAX_MSGS = 300

def load_approved_emails():
    if not os.path.exists(APPROVED_EMAILS_FILE):
        return {}
    with open(APPROVED_EMAILS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_approved_emails(data):
    with open(APPROVED_EMAILS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_email_approved(user, email):
    approved = load_approved_emails()
    return approved.get(user, "").lower() == email.lower()

def approve_email(user, email):
    approved = load_approved_emails()
    approved[user] = email
    save_approved_emails(approved)

def new_token(user):
    t = secrets.token_urlsafe(24)
    tokens[t] = user
    return t

def gen_email_code():
    return f"{secrets.randbelow(900000) + 100000}"

def gen_telegram_code():
    return f"JOY-{secrets.randbelow(9000) + 1000}"

def gen_sms_code():
    return f"{secrets.randbelow(900000) + 100000}"


# ── GROUP CHAT ──────────────────────────────────────────────

def load_group_chat() -> list:
    if not os.path.exists(GROUP_CHAT_FILE):
        return []
    try:
        with open(GROUP_CHAT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_group_chat(msgs: list):
    with open(GROUP_CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

def append_group_message(msg: dict) -> list:
    msgs = load_group_chat()
    msgs.append(msg)
    if len(msgs) > _GROUP_MAX_MSGS:
        msgs = msgs[-_GROUP_MAX_MSGS:]
    _save_group_chat(msgs)
    return msgs


# ── TELEGRAM AVATAR CACHE ───────────────────────────────────

AVATAR_TTL = 300  # seconds

def get_cached_avatar(user: str):
    entry = _avatar_cache.get(user)
    if entry and entry["exp"] > time.time():
        return entry["url"]
    return None   # None means "not cached / expired"

def set_cached_avatar(user: str, url):
    _avatar_cache[user] = {"url": url, "exp": time.time() + AVATAR_TTL}
