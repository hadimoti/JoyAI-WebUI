"""Main FastAPI server for Joy AI.

Routes all AI calls through the local Hermes gateway (OpenAI-compatible API server).

Run:  python hermes_api.py
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import httpx, uvicorn, time, os

from config import (
    HOST, PORT,
    AVAILABLE_MODELS, DEFAULT_MODEL,
    HERMES_API_URL, HERMES_API_KEY,
    BOT_TOKEN, USERS,
)
import auth, store

app = FastAPI(title="Joy AI — Hermes Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Single client pointing at local Hermes API server
_hermes_client: OpenAI | None = None


# ── GROUP CHAT WEBSOCKET MANAGER ─────────────────────────────

class _GroupManager:
    def __init__(self):
        self._sockets: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._sockets.append(ws)

    def disconnect(self, ws: WebSocket):
        self._sockets.discard if hasattr(self._sockets, 'discard') else None
        if ws in self._sockets:
            self._sockets.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in list(self._sockets):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self._sockets:
                self._sockets.remove(ws)

_group = _GroupManager()

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

# ---------- TUNNEL URL ----------
@app.get("/live-url")
async def live_url():
    url_file = os.path.join(os.path.dirname(__file__), "tunnel_url.txt")
    if os.path.exists(url_file):
        with open(url_file) as f:
            return {"url": f.read().strip()}
    return {"url": None}

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


def call_model_group(model_id: str, message: str, sender_name: str, history: list) -> str:
    """Group chat AI response — aware of all participants."""
    client = _get_client()

    names = ", ".join(u["name"] for u in USERS.values())
    messages = [{"role": "system", "content": (
        f"You are Joy AI, the shared team assistant for a restaurant group chat. "
        f"Team members: {names}. "
        "Anyone can message here and you reply to the whole group. "
        "Identify who sent the message from the [Name]: prefix. "
        "Help with restaurant operations, marketing, Instagram content, team coordination, and automation. "
        "Be concise, warm, and practical."
    )}]

    for h in history[-40:]:
        role = "user" if h.get("role") in ("user", "me") else "assistant"
        if role == "user":
            uinfo = USERS.get(h.get("user", ""), {})
            name = uinfo.get("name", h.get("user", ""))
            content = f"[{name}]: {h.get('text', '')}"
        else:
            content = h.get("text", "")
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": f"[{sender_name}]: {message}"})

    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ── GROUP CHAT ENDPOINTS ──────────────────────────────────────

@app.websocket("/group-chat/ws")
async def group_ws(websocket: WebSocket):
    await _group.connect(websocket)
    try:
        while True:
            await websocket.receive_text()   # keepalive pings from client
    except WebSocketDisconnect:
        _group.disconnect(websocket)

@app.get("/group-chat/history")
async def group_history():
    return {"messages": store.load_group_chat()}

@app.post("/group-chat/send")
async def group_send(req: Request):
    d = await req.json()
    token = d.get("token")
    if token not in store.tokens:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    user    = store.tokens[token]
    message = (d.get("message") or "").strip()
    model   = d.get("model", DEFAULT_MODEL)
    if not message:
        return JSONResponse({"error": "Empty message"})

    sender_name = USERS.get(user, {}).get("name", user)
    t_now = int(time.time() * 1000)

    # Persist and broadcast user message
    user_msg = {"role": "user", "user": user, "text": message, "t": t_now}
    history  = store.append_group_message(user_msg)
    await _group.broadcast({"type": "message", "msg": user_msg})

    # AI reply
    try:
        reply = call_model_group(model, message, sender_name, history[:-1])
    except Exception as e:
        reply = f"⚠️ Model error: {e}"

    ai_msg = {"role": "bot", "user": "joy_ai", "text": reply, "t": int(time.time() * 1000)}
    store.append_group_message(ai_msg)
    await _group.broadcast({"type": "message", "msg": ai_msg})

    return {"ok": True}


# ── TELEGRAM AVATAR ───────────────────────────────────────────

@app.get("/tg/avatar/{user}")
async def tg_avatar(user: str):
    info = USERS.get(user)
    if not info:
        return JSONResponse({"error": "Unknown user"}, status_code=404)

    cached = store.get_cached_avatar(user)
    if cached is not None:           # None means "not cached", "" means "no photo"
        return {"url": cached or None}

    if not BOT_TOKEN:
        store.set_cached_avatar(user, "")
        return {"url": None}

    tg_id = info["id"]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUserProfilePhotos",
                params={"user_id": tg_id, "limit": 1},
            )
            photos = r.json().get("result", {}).get("photos", [])
            if not photos:
                store.set_cached_avatar(user, "")
                return {"url": None}

            file_id = photos[0][-1]["file_id"]   # largest variant
            fr = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                params={"file_id": file_id},
            )
            file_path = fr.json()["result"]["file_path"]
            url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            store.set_cached_avatar(user, url)
            return {"url": url}
    except Exception as e:
        store.set_cached_avatar(user, "")
        return {"url": None, "error": str(e)}


# ── OPENAI-COMPATIBLE PROXY (for admin panel / external clients) ──────────────

@app.get("/v1/models")
async def v1_models():
    """OpenAI-compatible models list — lets admin panel check connection."""
    return {
        "object": "list",
        "data": [
            {"id": m["id"], "object": "model", "created": 0, "owned_by": "joy-ai"}
            for m in AVAILABLE_MODELS
        ],
    }


@app.post("/v1/chat/completions")
async def v1_chat_completions(req: Request):
    """OpenAI-compatible chat completions proxy — forwards directly to Hermes."""
    d = await req.json()
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=d.get("model", DEFAULT_MODEL),
            messages=d.get("messages", []),
            max_tokens=d.get("max_tokens", 1024),
            temperature=d.get("temperature", 0.7),
            stream=False,
        )
        return JSONResponse(response.model_dump())
    except Exception as e:
        return JSONResponse(
            {"error": {"message": str(e), "type": "api_error", "code": 500}},
            status_code=500,
        )


# Serve frontend — must be last so API routes take priority
app.mount("/", StaticFiles(directory=_FRONTEND, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
