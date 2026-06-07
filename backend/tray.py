"""
JoyAI Tray App — starts all services silently, lives in system tray.
Right-click → Open App / View Logs / Exit
"""
import os, sys, time, threading, subprocess, webbrowser
import pystray
from pystray import MenuItem as Item
from PIL import Image, ImageDraw

BACKEND_DIR  = r"C:\Users\HadiMoti\JoyAI-WebUI\backend"
CLOUDFLARED  = r"C:\Users\HadiMoti\cloudflared.exe"
LOG_FILE     = os.path.join(BACKEND_DIR, "joyai.log")
PUSH_SCRIPT  = os.path.join(BACKEND_DIR, "push_url.py")

_procs = []

# ── Icon ────────────────────────────────────────────────────────────────────

def make_icon(color="#FF6B35"):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 62, 62], fill=color)
    d.ellipse([16, 16, 48, 48], fill="white")
    d.ellipse([24, 24, 40, 40], fill=color)
    return img

# ── Logging ──────────────────────────────────────────────────────────────────

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

# ── Toast notification ────────────────────────────────────────────────────────

def toast(title, message):
    try:
        import ctypes
        ps = (
            f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]|Out-Null;"
            f"$x=[Windows.Data.Xml.Dom.XmlDocument]::new();"
            f"$x.LoadXml('<toast><visual><binding template=\"ToastGeneric\"><text>{title}</text><text>{message}</text></binding></visual></toast>');"
            f"$t=[Windows.UI.Notifications.ToastNotification]::new($x);"
            f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('JoyAI').Show($t)"
        )
        subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command", ps])
    except Exception as e:
        log(f"Toast error: {e}")

# ── Services ─────────────────────────────────────────────────────────────────

def start_services(icon):
    log("=== JoyAI starting ===")
    icon.icon = make_icon("#FFA500")  # orange = starting
    icon.title = "🦊 Joy AI — Starting..."

    try:
        lf = open(LOG_FILE, "a", encoding="utf-8")

        # 1. Hermes Gateway
        log("Starting Hermes Gateway...")
        p1 = subprocess.Popen(["hermes", "gateway", "run"], stdout=lf, stderr=lf)
        _procs.append(p1)
        time.sleep(5)

        # 2. JoyAI Backend
        log("Starting JoyAI Backend...")
        p2 = subprocess.Popen(
            [sys.executable, "hermes_api.py"],
            cwd=BACKEND_DIR, stdout=lf, stderr=lf
        )
        _procs.append(p2)
        time.sleep(5)

        # 3. Cloudflare Tunnel
        log("Starting Cloudflare Tunnel...")
        p3 = subprocess.Popen(
            f'"{CLOUDFLARED}" tunnel --url http://localhost:8000 2>&1 | "{sys.executable}" -u "{PUSH_SCRIPT}"',
            shell=True, stdout=lf, stderr=lf
        )
        _procs.append(p3)
        time.sleep(8)

        # Health check
        import urllib.request
        try:
            urllib.request.urlopen("http://localhost:8000/health", timeout=5)
            log("All services up!")
            icon.icon  = make_icon("#00CC44")  # green = running
            icon.title = "🦊 Joy AI — Running"
            toast("🦊 Joy is running!", "Team: joypizza.ir/joytest/joyai")
        except Exception:
            raise RuntimeError("JoyAI Backend health check failed (port 8000)")

    except Exception as e:
        log(f"STARTUP FAILED: {e}")
        icon.icon  = make_icon("#CC0000")  # red = failed
        icon.title = "🦊 Joy AI — Failed"
        toast("❌ Joy AI Failed", str(e))
        stop_all(icon, None)

# ── Tray actions ─────────────────────────────────────────────────────────────

def open_app(icon, item):
    webbrowser.open("http://localhost:8000")

def view_logs(icon, item):
    os.startfile(LOG_FILE)

def stop_all(icon, item):
    log("Stopping all services...")
    for p in _procs:
        try: p.terminate()
        except: pass
    subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "hermes.exe"],      capture_output=True)
    log("=== JoyAI stopped ===")
    if icon:
        icon.stop()

# ── Main ──────────────────────────────────────────────────────────────────────

icon = pystray.Icon(
    "JoyAI",
    make_icon("#FFA500"),
    "🦊 Joy AI — Starting...",
    menu=pystray.Menu(
        Item("🦊 Joy AI", lambda i, it: None, enabled=False),
        pystray.Menu.SEPARATOR,
        Item("Open App",  open_app),
        Item("View Logs", view_logs),
        pystray.Menu.SEPARATOR,
        Item("Exit", stop_all),
    )
)

threading.Thread(target=start_services, args=(icon,), daemon=True).start()
icon.run()
