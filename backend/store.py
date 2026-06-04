"""Simple JSON-file based storage for approved emails, codes, and tokens."""
import json, os, secrets, time
from config import APPROVED_EMAILS_FILE, DATA_DIR

os.makedirs(DATA_DIR, exist_ok=True)

# In-memory stores (reset on restart — fine for verification codes)
email_codes    = {}   # user -> {"code": "123456", "email": "..", "exp": ts}
telegram_codes = {}   # user -> {"code": "JOY-1234", "verified": False}
tokens         = {}   # token -> user

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
