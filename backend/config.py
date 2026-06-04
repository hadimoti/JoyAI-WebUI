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

# --- API Keys ---
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
AVAL_API_KEY   = os.getenv("AVAL_API_KEY", "")

# --- Provider base URLs ---
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
AVAL_BASE_URL   = "https://api.avalai.ir/v1"

# --- Available models (shown in UI dropdown) ---
# Format: {"id": "<model-id>", "name": "<display name>", "provider": "nvidia"|"aval"}
AVAILABLE_MODELS = [
    # NVIDIA NIM
    {"id": "meta/llama-3.1-70b-instruct",         "name": "Llama 3.1 70B (NVIDIA)",    "provider": "nvidia"},
    {"id": "meta/llama-3.1-8b-instruct",          "name": "Llama 3.1 8B (NVIDIA)",     "provider": "nvidia"},
    {"id": "mistralai/mistral-7b-instruct-v0.3",  "name": "Mistral 7B (NVIDIA)",       "provider": "nvidia"},
    {"id": "nvidia/nemotron-4-340b-instruct",      "name": "Nemotron 340B (NVIDIA)",    "provider": "nvidia"},
    # Aval AI
    {"id": "gpt-4o",                              "name": "GPT-4o (Aval)",             "provider": "aval"},
    {"id": "gpt-4o-mini",                         "name": "GPT-4o Mini (Aval)",        "provider": "aval"},
    {"id": "claude-3-5-sonnet-20241022",          "name": "Claude 3.5 Sonnet (Aval)",  "provider": "aval"},
    {"id": "claude-3-haiku-20240307",             "name": "Claude 3 Haiku (Aval)",     "provider": "aval"},
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
