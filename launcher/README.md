# JoyAI Manager — Windows Launcher

A native Windows app that manages the full JoyAI stack:
- **Hermes Gateway** (AI agent backend)
- **JoyAI WebUI Backend** (FastAPI)
- **Cloudflare Tunnel** (public access)

Lives in the system tray. Right-click → Stop to kill everything.

## Requirements

- Python 3.8+
- [Hermes Agent](https://github.com/nousresearch/hermes-agent)
- [cloudflared](https://github.com/cloudflare/cloudflared/releases)
- JoyAI WebUI backend (this repo)

## Install

```bash
pip install pystray pillow requests
python installer.py
```

The installer wizard lets you configure:
- Hermes directory & API connection
- JoyAI backend path
- Cloudflared executable path
- Telegram bot token
- Team site URL (for auto-redirect)
- Permanent Cloudflare URL (optional)

After setup, launch with:
```bash
pythonw joyai.py
```
Or use the desktop shortcut created by the installer.

## Build .exe

```bash
build.bat
```
Produces `dist/JoyAI-Setup.exe` and `dist/JoyAI.exe`.

## Host-side PHP redirect

Upload `../backend/joyai_cpanel/index.php` to your web host.  
Every restart automatically pushes the new tunnel URL there.  
Your team always uses your fixed domain — the tunnel URL changes invisibly.
