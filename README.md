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
cp .env.example .env      # fill BOT_TOKEN + Gmail SMTP
python hermes_api.py
```

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

- WebUI dropdown, CLI: `hermes model`, Telegram: `/model` → all return **default**.
- Models fetched once then cached with user + histories.

## Plug Your AI

Edit `run_default_model()` in `backend/hermes_api.py`.
