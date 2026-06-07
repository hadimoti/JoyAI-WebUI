"""JoyAI Manager — Main Application"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading, subprocess, os, sys, json, time, webbrowser
import pystray
from PIL import Image, ImageDraw, ImageTk

# ── Config ────────────────────────────────────────────────────────────────────

APP_DIR     = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

def load_config():
    for path in (CONFIG_PATH, os.path.join(APP_DIR, "config.json")):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

CFG = load_config()

# ── Colors ────────────────────────────────────────────────────────────────────

BG   = "#0f0f1a"
BG2  = "#1a1a2e"
BG3  = "#16213e"
ACC  = "#FF6B35"
FG   = "#e0e0e0"
FG2  = "#666688"
GRN  = "#00CC66"
RED  = "#CC3333"
YLW  = "#FFAA00"

# ── Tray icon ─────────────────────────────────────────────────────────────────

def make_tray_icon(color=ACC):
    try:
        for name in ("logo.ico", "logo.png"):
            p = os.path.join(APP_DIR, "assets", name)
            if os.path.exists(p):
                return Image.open(p).resize((64,64)).convert("RGBA")
    except Exception:
        pass
    img = Image.new("RGBA",(64,64),(0,0,0,0))
    d   = ImageDraw.Draw(img)
    d.ellipse([2,2,62,62], fill=color)
    return img

# ── Service manager ───────────────────────────────────────────────────────────

class Services:
    def __init__(self, log_fn):
        self._procs = {}
        self._log   = log_fn

    def start_all(self, on_done):
        threading.Thread(target=self._start_all_bg, args=(on_done,), daemon=True).start()

    def _start_all_bg(self, on_done):
        self._log("hermes", f"Starting Hermes Gateway...\n")
        hermes_dir = CFG.get("hermes_dir","")
        p1 = subprocess.Popen(
            ["hermes","gateway","run"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            encoding="utf-8", errors="replace",
            cwd=hermes_dir if os.path.isdir(hermes_dir) else None
        )
        self._procs["hermes"] = p1
        threading.Thread(target=self._pipe, args=(p1,"hermes"), daemon=True).start()
        time.sleep(5)

        self._log("backend", f"Starting JoyAI Backend...\n")
        bdir = CFG.get("backend_dir", APP_DIR)
        p2 = subprocess.Popen(
            [sys.executable, "hermes_api.py"],
            cwd=bdir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            encoding="utf-8", errors="replace"
        )
        self._procs["backend"] = p2
        threading.Thread(target=self._pipe, args=(p2,"backend"), daemon=True).start()
        time.sleep(5)

        self._log("tunnel", f"Starting Cloudflare Tunnel...\n")
        cf   = CFG.get("cloudflared_path", "cloudflared")
        push = os.path.join(APP_DIR, "push_url.py")
        p3 = subprocess.Popen(
            f'"{cf}" tunnel --url http://localhost:8000 2>&1 | "{sys.executable}" -u "{push}"',
            shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            encoding="utf-8", errors="replace"
        )
        self._procs["tunnel"] = p3
        threading.Thread(target=self._pipe, args=(p3,"tunnel"), daemon=True).start()

        on_done()

    def _pipe(self, proc, name):
        for line in proc.stdout:
            self._log(name, line)

    def stop_all(self):
        for p in self._procs.values():
            try: p.terminate()
            except: pass
        subprocess.run(["taskkill","/F","/IM","cloudflared.exe"], capture_output=True)
        subprocess.run(["taskkill","/F","/IM","hermes.exe"],      capture_output=True)
        self._procs.clear()

    def running(self):
        return bool(self._procs)


# ── Main App ──────────────────────────────────────────────────────────────────

class JoyAIApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JoyAI Manager")
        self.root.geometry("900x620")
        self.root.minsize(700, 480)
        self.root.configure(bg=BG)
        self._set_icon()

        self.svc  = Services(self._append_log)
        self._tray = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _set_icon(self):
        try:
            img = Image.open(os.path.join(APP_DIR,"assets","logo.png")).resize((32,32))
            self._wico = ImageTk.PhotoImage(img)
            self.root.iconphoto(True, self._wico)
        except Exception:
            pass

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_menu()
        self._build_toolbar()
        self._build_tabs()
        self._build_statusbar()
        self._start_tray()

    def _build_menu(self):
        mb = tk.Menu(self.root, bg=BG2, fg=FG, activebackground=ACC,
                     activeforeground="white", relief="flat", bd=0)
        self.root.config(menu=mb)

        # File
        fm = tk.Menu(mb, tearoff=0, bg=BG2, fg=FG,
                     activebackground=ACC, activeforeground="white")
        fm.add_command(label="Start Services",  command=self._start)
        fm.add_command(label="Stop Services",   command=self._stop)
        fm.add_separator()
        fm.add_command(label="Open App in Browser", command=self._open_browser)
        fm.add_separator()
        fm.add_command(label="Exit",            command=self._quit)
        mb.add_cascade(label="File", menu=fm)

        # Edit
        em = tk.Menu(mb, tearoff=0, bg=BG2, fg=FG,
                     activebackground=ACC, activeforeground="white")
        em.add_command(label="Clear Logs", command=self._clear_logs)
        mb.add_cascade(label="Edit", menu=em)

        # Options
        om = tk.Menu(mb, tearoff=0, bg=BG2, fg=FG,
                     activebackground=ACC, activeforeground="white")
        om.add_command(label="Settings",  command=self._open_settings)
        om.add_command(label="View Logs File", command=self._open_logfile)
        mb.add_cascade(label="Options", menu=om)

        # Help
        hm = tk.Menu(mb, tearoff=0, bg=BG2, fg=FG,
                     activebackground=ACC, activeforeground="white")
        hm.add_command(label="Open Team Link",
                       command=lambda: webbrowser.open(CFG.get("site_url","")))
        hm.add_command(label="About JoyAI Manager",
                       command=lambda: messagebox.showinfo("JoyAI Manager","v1.0\n🦊 Joy Team"))
        mb.add_cascade(label="Help", menu=hm)

    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=BG2, height=46)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        def btn(text, cmd, color=BG3):
            b = tk.Button(bar, text=text, command=cmd,
                          bg=color, fg=FG, activebackground=ACC,
                          activeforeground="white", relief="flat",
                          font=("Segoe UI", 9), cursor="hand2",
                          padx=14, pady=4, bd=0)
            b.pack(side="left", padx=4, pady=8)
            return b

        self.btn_start = btn("▶  Start All", self._start, ACC)
        self.btn_stop  = btn("■  Stop All",  self._stop)
        btn("🌐  Open App",  self._open_browser)
        btn("📋  View Logs", self._open_logfile)

        # Status dots
        dot_frame = tk.Frame(bar, bg=BG2)
        dot_frame.pack(side="right", padx=16)
        self._dots = {}
        for name, label in [("hermes","Hermes"),("backend","Backend"),("tunnel","Tunnel")]:
            f = tk.Frame(dot_frame, bg=BG2)
            f.pack(side="left", padx=8)
            dot = tk.Label(f, text="●", fg=FG2, bg=BG2, font=("Segoe UI",12))
            dot.pack(side="left")
            tk.Label(f, text=label, fg=FG2, bg=BG2,
                     font=("Segoe UI",8)).pack(side="left",padx=2)
            self._dots[name] = dot

    def _build_tabs(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",            background=BG,  borderwidth=0)
        style.configure("TNotebook.Tab",        background=BG2, foreground=FG2,
                         font=("Segoe UI",9),   padding=[14,6])
        style.map("TNotebook.Tab",
                  background=[("selected",BG3)],
                  foreground=[("selected",FG)])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        self._logs = {}
        tabs = [
            ("hermes",  "🔵  Hermes Gateway"),
            ("backend", "🟡  JoyAI Backend"),
            ("tunnel",  "🟣  Cloudflare Tunnel"),
        ]
        for key, title in tabs:
            frame = tk.Frame(nb, bg=BG)
            nb.add(frame, text=title)
            st = scrolledtext.ScrolledText(
                frame, bg="#050510", fg="#c8f0c8",
                font=("Consolas",8), relief="flat",
                insertbackground=FG, wrap="word",
                highlightthickness=0
            )
            st.pack(fill="both", expand=True)
            st.config(state="disabled")
            self._logs[key] = st

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=BG3, height=24)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self._status_var = tk.StringVar(value="Ready — click Start All to launch services")
        tk.Label(bar, textvariable=self._status_var,
                 font=("Segoe UI",8), fg=FG2, bg=BG3).pack(side="left", padx=10)
        link = CFG.get("permanent_cf_url") or CFG.get("site_url","")
        if link:
            lbl = tk.Label(bar, text=f"Team: {link}",
                           font=("Segoe UI",8), fg=ACC, bg=BG3, cursor="hand2")
            lbl.pack(side="right", padx=10)
            lbl.bind("<Button-1>", lambda e: webbrowser.open(link))

    # ── Tray ──────────────────────────────────────────────────────────────────

    def _start_tray(self):
        def _run():
            self._tray = pystray.Icon(
                "JoyAI", make_tray_icon(), "🦊 JoyAI Manager",
                menu=pystray.Menu(
                    pystray.MenuItem("Show",       self._show_window, default=True),
                    pystray.MenuItem("Open App",   lambda i,it: self._open_browser()),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Start All",  lambda i,it: self._start()),
                    pystray.MenuItem("Stop All",   lambda i,it: self._stop()),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Exit",       lambda i,it: self._quit()),
                )
            )
            self._tray.run_detached()
        threading.Thread(target=_run, daemon=True).start()

    def _show_window(self, icon=None, item=None):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def _on_close(self):
        self.root.withdraw()
        if self._tray:
            self._tray.notify("JoyAI still running in background", "🦊 JoyAI Manager")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _start(self):
        if self.svc.running():
            return
        self._status("Starting services...")
        self.btn_start.config(state="disabled")
        self._set_dots(YLW)
        self.svc.start_all(self._on_started)

    def _on_started(self):
        self.root.after(0, lambda: self._status("All services running"))
        self.root.after(0, lambda: self._set_dots(GRN))
        self.root.after(0, lambda: self.btn_start.config(state="normal"))

    def _stop(self):
        self.svc.stop_all()
        self._status("Services stopped")
        self._set_dots(FG2)

    def _open_browser(self):
        webbrowser.open("http://localhost:8000")

    def _open_logfile(self):
        log = os.path.join(APP_DIR,"joyai.log")
        if os.path.exists(log):
            os.startfile(log)

    def _clear_logs(self):
        for st in self._logs.values():
            st.config(state="normal")
            st.delete("1.0","end")
            st.config(state="disabled")

    def _quit(self):
        self.svc.stop_all()
        if self._tray:
            try: self._tray.stop()
            except: pass
        self.root.destroy()

    def _status(self, msg):
        self._status_var.set(msg)

    def _set_dots(self, color):
        for dot in self._dots.values():
            dot.config(fg=color)

    def _append_log(self, tab, text):
        st = self._logs.get(tab)
        if not st: return
        def _do():
            st.config(state="normal")
            st.insert("end", text)
            st.see("end")
            st.config(state="disabled")
        self.root.after(0, _do)

    # ── Settings dialog ───────────────────────────────────────────────────────

    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("500x520")
        win.configure(bg=BG)
        win.grab_set()

        tk.Label(win, text="Settings", font=("Segoe UI",13,"bold"),
                 fg=ACC, bg=BG).pack(pady=12)

        canvas = tk.Canvas(win, bg=BG, highlightthickness=0)
        sb     = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        frame  = tk.Frame(canvas, bg=BG)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=16)
        canvas.create_window((0,0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))

        fields = [
            ("Hermes Directory",          "hermes_dir",        False),
            ("JoyAI Backend Directory",   "backend_dir",       False),
            ("cloudflared.exe Path",      "cloudflared_path",  False),
            ("Hermes API URL",            "hermes_api_url",    False),
            ("Hermes API Key",            "hermes_api_key",    True),
            ("Telegram Bot Token",        "bot_token",         True),
            ("Team Site URL",             "site_url",          False),
            ("Permanent Cloudflare URL",  "permanent_cf_url",  False),
            ("Push Secret",               "push_secret",       False),
        ]

        sv = {}
        for label, key, secret in fields:
            tk.Label(frame, text=label, font=("Segoe UI",8),
                     fg=FG2, bg=BG).pack(anchor="w", pady=(8,1))
            v = tk.StringVar(value=CFG.get(key,""))
            sv[key] = v
            e = tk.Entry(frame, textvariable=v, show="*" if secret else "",
                        bg="#0a0a14", fg=FG, insertbackground=FG,
                        relief="flat", font=("Consolas",9), bd=4)
            e.pack(fill="x")

        def _save():
            for key, v in sv.items():
                CFG[key] = v.get()
            save_config(CFG)
            messagebox.showinfo("Saved","Settings saved. Restart services to apply.", parent=win)
            win.destroy()

        tk.Button(win, text="Save", command=_save,
                  bg=ACC, fg="white", relief="flat",
                  font=("Segoe UI",9,"bold"), padx=20, pady=6,
                  cursor="hand2").pack(pady=12)


if __name__ == "__main__":
    JoyAIApp()
