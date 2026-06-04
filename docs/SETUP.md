# Joy AI — Setup Guide

## Prerequisites

- Python 3.10+
- A Telegram Bot token from [@BotFather](https://t.me/BotFather)
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords) (16 chars)

## Backend setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and fill in:

| Variable   | Value                                      |
|------------|--------------------------------------------|
| BOT_TOKEN  | Your Telegram bot token from BotFather     |
| SMTP_USER  | Your Gmail address                         |
| SMTP_PASS  | Your 16-character Gmail App Password       |

Then start the server:

```bash
python hermes_api.py
```

The API runs at `http://0.0.0.0:8000`.

## Frontend setup

Open `frontend/index.html` in any browser.

To connect to the live backend, edit these two lines at the top of the `<script>` block:

```js
const DEMO_MODE = false;
const HERMES_API = "http://YOUR-PC-IP:8000";
```

Replace `YOUR-PC-IP` with the local IP of the machine running `hermes_api.py`.

## Admin: approve emails

Edit `data/approved_emails.json` to map each username to their Gmail:

```json
{
  "hadimoti": "hadi@yourdomain.com",
  "yoonesbz": "yoones@yourdomain.com"
}
```

## Plug your AI model

Open `backend/hermes_api.py` and replace the body of `run_default_model()`:

```python
def run_default_model(message: str, history: list) -> str:
    # Call your Hermes / OpenAI / local model here
    return your_model.chat(message, history)
```
