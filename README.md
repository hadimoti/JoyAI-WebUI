# Joy AI 🦊

Responsive phone WebUI + Hermes backend. Gmail/Telegram verification, single **default** model, per-user cached histories.

## Members

| Name   | Username      | Role            |
|--------|---------------|-----------------|
| Hadi   | @hadimoti     | Creator · Admin |
| Yoones | @yoonesbz     | JOY Manager     |
| Nadia  | @naad_ya      | JOY Manager     |
| Zohre  | @fatemi9696   | JOY Artist      |

## Quick Start

### Frontend (test now, demo mode)

Open `frontend/index.html` in your browser.

- Gmail code in demo: `123456`
- Telegram: auto-confirms in demo

### Backend (go live)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # fill BOT_TOKEN, Gmail SMTP, HERMES_API_KEY
python hermes_api.py
```

**Requires Hermes desktop (or `hermes gateway`) running on port 8642.**

Then in `frontend/index.html` set:

```js
const DEMO_MODE = false;
const HERMES_API = "http://YOUR-PC-IP:8000";
```

## Auth Flow

1. Pick name → choose **Gmail** or **Telegram**.
2. **Gmail**: email must be admin-approved (`data/approved_emails.json`) → 6-digit code sent.
3. **Telegram**: shows `JOY-XXXX` code → send it to `@differentjoy_bot` → auto-verified (no admin step).
4. Verified users are cached → skip straight to chat next time.

## Models

All models route through the local **Hermes gateway** → AvalAI:

| ID | Name |
|----|------|
| `deepseek-v4-pro` | Joy AI Pro (default) |
| `deepseek-v4-flash` | Joy AI Flash |
| `claude-sonnet-4-6` | Claude Sonnet |
| `gemini-3.1-flash-lite-preview` | Gemini Flash Lite |
| `qwen3.6-flash` | Qwen Flash (Persian) |

## Architecture

```
Browser → JoyAI backend (port 8000) → Hermes gateway (port 8642) → AvalAI
```
