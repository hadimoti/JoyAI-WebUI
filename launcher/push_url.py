"""Reads cloudflared output from stdin, finds the tunnel URL, pushes it to joypizza.ir."""
import sys, re, requests

PUSH_URL = "https://joypizza.ir/joytest/joyai/"
SECRET   = "joyai-tunnel-2026"

for line in sys.stdin:
    sys.stdout.write(line)
    sys.stdout.flush()
    m = re.search(r"https://[a-z]+-[a-z]+-[a-z0-9-]+\.trycloudflare\.com", line)
    if m:
        url = m.group(0)
        print(f"\n{'='*55}")
        print(f"  PUBLIC URL: {url}")
        print(f"  TEAM LINK:  https://joypizza.ir/joytest/joyai/")
        print(f"{'='*55}\n", flush=True)
        try:
            r = requests.post(PUSH_URL, json={"secret": SECRET, "url": url}, timeout=10)
            print("Pushed to joypizza.ir OK" if r.status_code == 200 else f"Push failed: {r.status_code}", flush=True)
        except Exception as e:
            print(f"Push error: {e}", flush=True)
