"""JoyAI Manager — Setup Wizard"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, shutil, os, sys, json, threading

APP_DIR     = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "JoyAI")
CONFIG_PATH = os.path.join(INSTALL_DIR, "config.json")

DEFAULTS = {
    "hermes_dir":        os.path.join(os.path.expanduser("~"), "hermes"),
    "hermes_api_url":    "http://127.0.0.1:8642/v1",
    "hermes_api_key":    "",
    "backend_dir":       os.path.join(os.path.expanduser("~"), "JoyAI-WebUI", "backend"),
    "cloudflared_path":  os.path.join(os.path.expanduser("~"), "cloudflared.exe"),
    "site_url":          "https://yourdomain.com/joyai/",
    "push_secret":       "",
    "bot_token":         "",
    "permanent_cf_url":  "",
    "install_dir":       INSTALL_DIR,
}

BG   = "#2b2b2b"
BG2  = "#222222"
ACC  = "#FF8000"
FG   = "#e0e0e0"
FG2  = "#999999"
GRN  = "#00CC66"
RED  = "#CC3333"

def styled_btn(parent, text, cmd, accent=False, **kw):
    bg = ACC if accent else "#2a2a4a"
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg="white",
                  activebackground="#ff8555" if accent else "#3a3a5a",
                  activeforeground="white", relief="flat",
                  font=("Segoe UI", 9, "bold" if accent else "normal"),
                  cursor="hand2", bd=0, padx=14, pady=6, **kw)
    return b

def styled_entry(parent, var, show=None):
    e = tk.Entry(parent, textvariable=var, show=show or "",
                 bg="#0f0f1a", fg=FG, insertbackground=FG,
                 relief="flat", font=("Consolas", 9),
                 highlightthickness=1, highlightcolor=ACC,
                 highlightbackground="#2a2a4a", bd=4)
    return e


class Wizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JoyAI Manager — Setup")
        self.root.geometry("560x580")
        self.root.minsize(560, 520)
        self.root.resizable(True, True)
        self.root.configure(bg=BG)
        self._set_icon()

        self.cfg  = dict(DEFAULTS)
        self._vars = {}
        self.page  = 0
        self.pages = [
            self._pg_welcome,
            self._pg_requirements,
            self._pg_paths,
            self._pg_connections,
            self._pg_install,
        ]
        self._build_shell()
        self._show(0)
        self.root.mainloop()

    def _set_icon(self):
        try:
            from PIL import Image, ImageTk
            img = Image.open(os.path.join(APP_DIR, "assets", "logo.png")).resize((32,32))
            self._ico = ImageTk.PhotoImage(img)
            self.root.iconphoto(True, self._ico)
        except Exception:
            pass

    def _build_shell(self):
        # Header
        hdr = tk.Frame(self.root, bg=ACC, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  🦊  JoyAI Manager Setup",
                 font=("Segoe UI", 15, "bold"), fg="white", bg=ACC).pack(side="left", padx=10)
        self.step_lbl = tk.Label(hdr, text="", font=("Segoe UI", 8),
                                  fg="#ffe0d0", bg=ACC)
        self.step_lbl.pack(side="right", padx=16)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=560, mode="determinate")
        self.progress.pack(fill="x")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", background=ACC, troughcolor=BG2, thickness=4)

        # Scrollable content area
        self._canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self._sb     = ttk.Scrollbar(self.root, orient="vertical",
                                     command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side="right", fill="y")
        self._canvas.pack(fill="both", expand=True)
        self.content = tk.Frame(self._canvas, bg=BG)
        self._cwin = self._canvas.create_window(
            (0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._on_content_resize)
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Footer buttons
        foot = tk.Frame(self.root, bg=BG2, height=52)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)
        self.btn_back = styled_btn(foot, "← Back", self._prev)
        self.btn_back.pack(side="left", padx=14, pady=10)
        self.btn_next = styled_btn(foot, "Next →", self._next, accent=True)
        self.btn_next.pack(side="right", padx=14, pady=10)

    def _on_content_resize(self, e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, e):
        self._canvas.itemconfig(self._cwin, width=e.width - 4)

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()
        self._canvas.yview_moveto(0)

    def _h(self, text, size=11, color=ACC):
        tk.Label(self.content, text=text, font=("Segoe UI", size, "bold"),
                 fg=color, bg=BG).pack(anchor="w", pady=(0,4))

    def _p(self, text, color=FG2):
        tk.Label(self.content, text=text, font=("Segoe UI", 9),
                 fg=color, bg=BG, wraplength=480, justify="left").pack(anchor="w")

    def _field(self, label, key, secret=False, browse=None):
        tk.Label(self.content, text=label, font=("Segoe UI", 8),
                 fg=FG2, bg=BG).pack(anchor="w", pady=(8,1))
        var = tk.StringVar(value=self.cfg.get(key, ""))
        self._vars[key] = var
        row = tk.Frame(self.content, bg=BG)
        row.pack(fill="x")
        e = styled_entry(row, var, show="*" if secret else None)
        e.pack(side="left", fill="x", expand=True)
        if browse:
            def _browse(is_file=browse):
                p = filedialog.askopenfilename() if is_file else filedialog.askdirectory()
                if p: var.set(p)
            tk.Button(row, text="…", command=_browse, bg="#2a2a4a", fg=FG,
                     relief="flat", padx=8, cursor="hand2").pack(side="left", padx=(3,0))

    def _sep(self):
        tk.Frame(self.content, bg="#2a2a4a", height=1).pack(fill="x", pady=10)

    # ── Pages ─────────────────────────────────────────────────────────────────

    def _pg_welcome(self):
        self._h("Welcome!", 13)
        self._p("This wizard will configure and install JoyAI Manager on your PC.")
        self._sep()
        self._h("What gets set up:", 9, FG)
        for item in [
            "  ✦  Hermes Gateway connection",
            "  ✦  JoyAI WebUI Backend",
            "  ✦  Cloudflare Tunnel (temporary or permanent)",
            "  ✦  Team site auto-update",
            "  ✦  System tray app with Start / Stop controls",
        ]:
            tk.Label(self.content, text=item, font=("Segoe UI", 9),
                     fg=FG, bg=BG).pack(anchor="w")
        self._sep()
        self._p("Click Next to begin.", FG2)

    def _pg_requirements(self):
        self._h("Checking Requirements", 11)
        self._p("Verifying all dependencies are installed...")
        self._sep()

        checks = [
            ("Python 3.8+",     self._chk_python),
            ("pip",             self._chk_pip),
            ("pystray",         lambda: self._chk_pkg("pystray")),
            ("Pillow",          lambda: self._chk_pkg("PIL")),
            ("requests",        lambda: self._chk_pkg("requests")),
            ("cloudflared.exe", self._chk_cf),
        ]

        self._req_rows = []
        for name, fn in checks:
            row = tk.Frame(self.content, bg=BG2, pady=4)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"  {name}", font=("Segoe UI", 9),
                     fg=FG, bg=BG2, width=22, anchor="w").pack(side="left")
            sv = tk.StringVar(value="…")
            lbl = tk.Label(row, textvariable=sv, font=("Consolas", 9),
                           fg=FG2, bg=BG2)
            lbl.pack(side="left")
            self._req_rows.append((sv, lbl, fn))

        def run():
            missing = []
            for sv, lbl, fn in self._req_rows:
                ok, msg = fn()
                sv.set(("✓  " if ok else "✗  ") + msg)
                lbl.config(fg=GRN if ok else RED)
                if not ok:
                    missing.append(msg)
            if missing:
                styled_btn(self.content, "Install missing Python packages",
                           self._fix_pkgs).pack(pady=10)

        threading.Thread(target=run, daemon=True).start()

    def _chk_python(self):
        v = sys.version_info
        return v >= (3,8), f"{v.major}.{v.minor}.{v.micro}"

    def _chk_pip(self):
        try:
            subprocess.run([sys.executable,"-m","pip","--version"],
                           capture_output=True, check=True)
            return True, "Available"
        except: return False, "Not found"

    def _chk_pkg(self, name):
        try: __import__(name); return True, "Installed"
        except ImportError: return False, "Not installed"

    def _chk_cf(self):
        p = self.cfg.get("cloudflared_path","")
        if os.path.exists(p): return True, "Found"
        r = subprocess.run(["where","cloudflared"], capture_output=True, text=True)
        return (True,"In PATH") if r.returncode==0 else (False,"Not found")

    def _fix_pkgs(self):
        subprocess.Popen([sys.executable,"-m","pip","install",
                          "pystray","Pillow","requests","pywin32"])
        messagebox.showinfo("Installing","Installing packages in background.\n"
                            "Please wait ~30s then click Back and Next to re-check.")

    def _pg_paths(self):
        self._h("Paths & Locations", 11)
        self._p("Tell JoyAI where to find everything on your PC.")
        self._sep()
        self._field("Hermes Directory",       "hermes_dir",       browse=False)
        self._field("JoyAI Backend Directory","backend_dir",       browse=False)
        self._field("cloudflared.exe Path",   "cloudflared_path", browse=True)
        self._field("Install Directory",      "install_dir",      browse=False)

    def _pg_connections(self):
        self._h("Connections & Tokens", 11)
        self._p("API keys, tokens, and your team site URL.")
        self._sep()
        self._field("Hermes API URL",            "hermes_api_url")
        self._field("Hermes API Key",            "hermes_api_key",   secret=True)
        self._field("Telegram Bot Token",        "bot_token",        secret=True)
        self._field("Team Site URL (temporary)", "site_url")
        self._field("Permanent Cloudflare URL",  "permanent_cf_url",
                    )
        tk.Label(self.content, text="  ↑ Leave blank to use temporary trycloudflare.com URLs",
                 font=("Segoe UI", 7, "italic"), fg=FG2, bg=BG).pack(anchor="w")
        self._field("Site Push Secret",          "push_secret")

    def _pg_install(self):
        self._h("Installing...", 11)
        self.log_box = tk.Text(self.content, bg="#0a0a0a", fg=GRN,
                               font=("Consolas", 8), relief="flat",
                               highlightthickness=1, highlightbackground="#2a2a4a")
        self.log_box.pack(fill="both", expand=True)
        self.btn_next.config(state="disabled", text="Finish")
        threading.Thread(target=self._do_install, daemon=True).start()

    def _ilog(self, msg):
        self.log_box.insert("end", msg+"\n")
        self.log_box.see("end")
        self.root.update_idletasks()

    def _do_install(self):
        for key, var in self._vars.items():
            self.cfg[key] = var.get()

        idir = self.cfg["install_dir"]
        try:
            self._ilog(f"Creating: {idir}")
            os.makedirs(idir, exist_ok=True)
            os.makedirs(os.path.join(idir,"assets"), exist_ok=True)

            self._ilog("Saving config.json...")
            with open(os.path.join(idir,"config.json"),"w") as f:
                json.dump(self.cfg, f, indent=2)

            self._ilog("Copying application files...")
            for fname in ["joyai.py","services.py","push_url.py"]:
                src = os.path.join(APP_DIR, fname)
                if os.path.exists(src):
                    shutil.copy2(src, idir)
                    self._ilog(f"  ✓ {fname}")

            logo_src = os.path.join(APP_DIR,"assets","logo.png")
            if os.path.exists(logo_src):
                shutil.copy2(logo_src, os.path.join(idir,"assets","logo.png"))
                self._ilog("  ✓ logo.png")

            self._ilog("Creating desktop shortcut...")
            self._make_shortcut(idir)

            self._ilog("\n✓ Installation complete!")
            self._ilog(f"✓ Installed to: {idir}")
            self._ilog("\nClick Finish — JoyAI Manager is ready.")
            self.btn_next.config(state="normal")

        except Exception as e:
            self._ilog(f"\n✗ Error: {e}")

    def _make_shortcut(self, idir):
        try:
            ico_path = os.path.join(idir, "assets", "logo.ico")
            png_path = os.path.join(idir, "assets", "logo.png")
            if not os.path.exists(ico_path) and os.path.exists(png_path):
                from PIL import Image
                img = Image.open(png_path)
                img.save(ico_path, format="ICO",
                         sizes=[(16,16),(32,32),(48,48),(64,64),(256,256)])

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            lnk     = os.path.join(desktop, "JoyAI Manager.lnk")
            target  = os.path.join(idir, "joyai.py")
            icon    = ico_path if os.path.exists(ico_path) else ""

            ps = "\n".join([
                '$s=(New-Object -COM WScript.Shell).CreateShortcut(' + f'"{lnk}")',
                '$s.TargetPath="pythonw.exe"',
                f'$s.Arguments=\'"{target}"\'',
                f'$s.WorkingDirectory="{idir}"',
                f'$s.IconLocation="{icon},0"' if icon else "",
                '$s.Save()',
            ])
            subprocess.run(["powershell","-Command", ps], capture_output=True)
            self._ilog("  ✓ Desktop shortcut created")
        except Exception as e:
            self._ilog(f"  (shortcut skipped: {e})")

    # ── Navigation ────────────────────────────────────────────────────────────

    def _show(self, idx):
        self._clear()
        self.page = idx
        n = len(self.pages)
        self.pages[idx]()
        self.step_lbl.config(text=f"Step {idx+1} of {n}")
        self.progress["value"] = ((idx) / (n-1)) * 100
        self.btn_back.config(state="normal" if idx>0 else "disabled")
        self.btn_next.config(text="Finish" if idx==n-1 else "Next →",
                             state="normal")

    def _next(self):
        if self.page < len(self.pages)-1:
            self._show(self.page+1)
        else:
            self.root.destroy()

    def _prev(self):
        if self.page > 0:
            self._show(self.page-1)


if __name__ == "__main__":
    Wizard()
