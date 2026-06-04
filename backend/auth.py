"""Email + Telegram verification logic."""
import smtplib, time
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
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

def request_telegram_code(user):
    code = store.gen_telegram_code()
    store.telegram_codes[user] = {"code": code, "verified": False}
    return {"code": code}

def check_telegram(user, code):
    rec = store.telegram_codes.get(user)
    if rec and rec["code"] == code and rec["verified"]:
        return {"ok": True, "token": store.new_token(user)}
    return {"ok": False}
