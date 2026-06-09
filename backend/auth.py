"""Email + Telegram + SMS verification logic."""
import smtplib, ssl, time, requests as _req
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, BOT_TOKEN, USERS, SMS_API_KEY, SMS_SENDER
import store

CODE_TTL = 300  # seconds

# ── EMAIL ────────────────────────────────────────────────────────────────────

def send_email_code(email, code):
    """Send the 6-digit code via Gmail SMTP (port 465 implicit SSL)."""
    if not SMTP_USER or not SMTP_PASS:
        print(f"[DEV] Email code for {email}: {code}")
        return True
    body = f"Your Joy AI verification code is: {code}\n\nIt expires in 5 minutes."
    msg = MIMEText(body)
    msg["Subject"] = "Joy AI verification code 🦊"
    msg["From"]    = SMTP_USER
    msg["To"]      = email
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
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


# ── SMS (Kavenegar) ──────────────────────────────────────────────────────────

def _send_kavenegar(phone: str, message: str) -> bool:
    """Send SMS via Kavenegar REST API. Returns True on success."""
    if not SMS_API_KEY:
        print(f"[DEV] SMS to {phone}: {message}")
        return True
    try:
        params = {"receptor": phone, "message": message}
        if SMS_SENDER:
            params["sender"] = SMS_SENDER
        r = _req.post(
            f"https://api.kavenegar.com/v1/{SMS_API_KEY}/sms/send.json",
            data=params,
            timeout=10,
        )
        result = r.json()
        if result.get("return", {}).get("status") == 200:
            return True
        print("Kavenegar error:", result)
        return False
    except Exception as e:
        print("SMS send error:", e)
        return False

def request_sms(user: str):
    """Send a 6-digit OTP to the user's registered phone number."""
    info = USERS.get(user)
    if not info:
        return {"sent": False, "error": "unknown_user"}
    phone = info.get("phone", "").strip()
    if not phone:
        return {"sent": False, "error": "no_phone"}
    code = store.gen_sms_code()
    store.sms_codes[user] = {"code": code, "exp": time.time() + CODE_TTL}
    msg = f"کد تأیید Joy AI شما: {code}\nExpires in 5 min."
    ok = _send_kavenegar(phone, msg)
    return {"sent": ok}

def verify_sms(user: str, code: str):
    """Verify the 6-digit SMS OTP and return a session token on success."""
    rec = store.sms_codes.get(user)
    if rec and rec.get("exp", 0) > time.time() and rec["code"] == code:
        del store.sms_codes[user]
        return {"ok": True, "token": store.new_token(user)}
    return {"ok": False}
