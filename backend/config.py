import os
from dotenv import load_dotenv
load_dotenv()

# --- Server ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# --- Telegram ---
BOT_TOKEN    = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = "differentjoy_bot"

# --- Admin ---
ADMIN_USER        = "hadimoti"
ADMIN_TELEGRAM_ID = "68238523"

# --- Email (Gmail SMTP) ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# --- Hermes API server (local gateway) ---
HERMES_API_URL = os.getenv("HERMES_API_URL", "http://127.0.0.1:8642/v1")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "")

# --- Available models (routed through Hermes → AvalAI) ---
AVAILABLE_MODELS = [
    {"id": "deepseek-v4-pro",              "name": "Joy AI Pro"},
    {"id": "deepseek-v4-flash",            "name": "Joy AI Flash"},
    {"id": "claude-sonnet-4-6",            "name": "Claude Sonnet"},
    {"id": "gemini-3.1-flash-lite-preview","name": "Gemini Flash Lite"},
    {"id": "qwen3.6-flash",               "name": "Qwen Flash (Persian)"},
]

DEFAULT_MODEL = AVAILABLE_MODELS[0]["id"]

# --- Known users ---
USERS = {
    "hadimoti":   {"id": "68238523",  "name": "Hadi",   "role": "Creator · Admin"},
    "yoonesbz":   {"id": "72826135",  "name": "Yoones", "role": "JOY Manager"},
    "naad_ya":    {"id": "97638568",  "name": "Nadia",  "role": "JOY Manager"},
    "fatemi9696": {"id": "106685881", "name": "Zohre",  "role": "JOY Artist"},
}

# --- Paths ---
DATA_DIR             = os.path.join(os.path.dirname(__file__), "..", "data")
APPROVED_EMAILS_FILE = os.path.join(DATA_DIR, "approved_emails.json")
