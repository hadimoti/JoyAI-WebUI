"""Main FastAPI server for Joy AI.

Routes all AI calls through the local Hermes gateway (OpenAI-compatible API server).

Run:  python hermes_api.py
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
import uvicorn

from config import (
    HOST, PORT,
    AVAILABLE_MODELS, DEFAULT_MODEL,
    HERMES_API_URL, HERMES_API_KEY,
)
import auth, store
from telegram_bot import start_bot

app = FastAPI(title="Joy AI — Hermes Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single client pointing at local Hermes API server
_hermes_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _hermes_client
    if not _hermes_client:
        _hermes_client = OpenAI(
            api_key=HERMES_API_KEY,
            base_url=HERMES_API_URL,
        )
    return _hermes_client


# ---------- AUTH: EMAIL ----------
@app.post("/auth/email/request")
async def email_request(req: Request):
    d = await req.json()
    return auth.request_email(d["user"], d["email"])

@app.post("/auth/email/verify")
async def email_verify(req: Request):
    d = await req.json()
    return auth.verify_email(d["user"], d["code"])

# ---------- AUTH: TELEGRAM ----------
@app.post("/auth/telegram/code")
async def tg_code(req: Request):
    d = await req.json()
    return auth.request_telegram_code(d["user"])

@app.get("/auth/telegram/check")
async def tg_check(user: str, code: str):
    return auth.check_telegram(user, code)

# ---------- MODELS ----------
@app.get("/models")
async def models():
    """Return all available models for the UI dropdown."""
    return {"models": [{"id": m["id"], "name": m["name"]} for m in AVAILABLE_MODELS]}

# ---------- HEALTH ----------
@app.get("/health")
async def health():
    return {"status": "ok", "gateway": HERMES_API_URL}

# ---------- CHAT ----------
@app.post("/chat")
async def chat(req: Request):
    d = await req.json()

    token = d.get("token")
    if token not in store.tokens:
        return JSONResponse({"reply": "⚠️ Session expired. Please log in again."}, status_code=401)

    message = d.get("message", "")
    model   = d.get("model", DEFAULT_MODEL)
    history = d.get("history", [])

    try:
        reply = call_model(model, message, history)
    except Exception as e:
        reply = f"⚠️ Model error: {e}"

    return {"reply": reply}


def call_model(model_id: str, message: str, history: list) -> str:
    """Send the message to Hermes gateway and return the reply."""
    client = _get_client()

    messages = [{"role": "system", "content": (
        "You are Joy AI, an assistant for a restaurant team. "
        "Help with operations, marketing, Instagram content, and automation. "
        "Be concise and practical."
    )}]

    for h in history[-20:]:
        role = "user" if h.get("role") == "me" else "assistant"
        messages.append({"role": role, "content": h.get("text", "")})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    start_bot()
    uvicorn.run(app, host=HOST, port=PORT)
