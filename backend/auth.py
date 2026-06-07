"""Email + Telegram verification logic."""
import smtplib, time, requests as _req
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, BOT_TOKEN, USERS
import store

CODE_TTL = 300  # seconds

def send_email_code(email, code):
    """Send the 6-digit code via Gmail SMTP."""
    if not SMTP_USER or not SMTP_PASS:
        print(f"[DEV] Email code for {email}: {code}")  # fallback if SMTP not set
        return True
    body = f"Your Joy AI verification code is: {code}\n\nIt expires in 5 minutes."
    msg = MIMEText(body)
    msg["Subject"] = "Joy AI verification code 🦊"
    msg["From"]    = SMTP_USER
    msg["To"]      = email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print("SMTP error:", e)
        return False

def request_email(user, email):
    if not store.is_email_approved(user, email):
        return {"approved": False}
    code = store.gen_email_code()
    store.email_codes[user] = {"code": code, "email": email, "exp": time.time() + CODE_TTL}
    send_email_code(email, code)
    return {"approved": True}

def verify_email(user, code):
    rec = store.email_codes.get(user)
    if not rec or rec["exp"] < time.time():
        return {"ok": False}
    if rec["code"] == code:
        del store.email_codes[user]
        return {"ok": True, "token": store.new_token(user)}
    return {"ok": False}

def _send_telegram(tg_id: str, text: str) -> bool:
    try:
        _req.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": tg_id, "text": text},
            timeout=10,
        )
        return True
    except Exception as e:
        print("Telegram send error:", e)
        return False

def request_telegram_code(user):
    info = USERS.get(user)
    if not info:
        return {"sent": False}
    code = store.gen_telegram_code()
    store.telegram_codes[user] = {"code": code, "exp": time.time() + CODE_TTL}
    ok = _send_telegram(
        info["id"],
        f"🦊 Joy AI\nVerification code: {code}\n\nکد تأیید جوی ای: {code}\n\n(expires in 5 min)"
    )
    return {"sent": ok}

def check_telegram(user, code):
    rec = store.telegram_codes.get(user)
    if rec and rec.get("exp", 0) > time.time() and rec["code"] == code:
        del store.telegram_codes[user]
        return {"ok": True, "token": store.new_token(user)}
    return {"ok": False}
