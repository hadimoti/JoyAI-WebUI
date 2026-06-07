"""
Runs cloudflared, captures the public URL, saves it locally,
and pushes it to joypizza.ir so the team always has a fixed link.
"""
import subprocess, sys, re, os, requests, time

CLOUDFLARED  = r"C:\Users\HadiMoti\cloudflared.exe"
URL_FILE     = os.path.join(os.path.dirname(__file__), "tunnel_url.txt")
PUSH_URL     = "https://joypizza.ir/joytest/joyai/"
PUSH_SECRET  = "joyai-tunnel-2026"
LOCAL_PORT   = 8000

def _save(url: str):
    with open(URL_FILE, "w") as f:
        f.write(url)
    print(f"[tunnel] URL saved: {url}")

def _push(url: str):
    try:
        r = requests.post(PUSH_URL, json={"secret": PUSH_SECRET, "url": url}, timeout=10)
        if r.status_code == 200:
            print(f"[tunnel] Pushed to joypizza.ir OK")
        else:
            print(f"[tunnel] Push failed: {r.status_code}")
    except Exception as e:
        print(f"[tunnel] Push error: {e}")

def run():
    cmd = [CLOUDFLARED, "tunnel", "--url", f"http://localhost:{LOCAL_PORT}"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    url_found = False
    print("[tunnel] Starting cloudflared...")

    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        if not url_found:
            m = re.search(r"https://[a-z]+-[a-z]+-[a-z0-9-]+\.trycloudflare\.com", line)
            if m:
                url = m.group(0)
                url_found = True
                _save(url)
                _push(url)
                print(f"\n{'='*55}")
                print(f"  PUBLIC URL: {url}")
                print(f"  TEAM LINK:  https://joypizza.ir/joyai/")
                print(f"{'='*55}\n")

    proc.wait()

if __name__ == "__main__":
    run()
