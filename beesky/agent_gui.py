"""BeeSky Agent config window — the face of the agent app.

    beesky-agent            (no arguments -> this window)
    python -m beesky.agent_app

One small tkinter form (stdlib only, same dark theme as the main
BeeSky GUI in beesky/gui.py — its colour constants, logo lookup and
ttk styles are reused, not forked): the farm operator fills in the
scan target, the cloud URL, the agent key from the cloud's Cài đặt
page and the site name once, presses "Chạy thử" to watch a real
ingest land, saves, and flips on auto-start. After that the agent
runs itself via the Windows Scheduled Task (or any other launcher)
with `beesky-agent run` — no window needed.

The key field is masked by default with a "Hiện key" toggle: the
key is shown ONCE by the cloud when the agent is created and is
stored only in this config file (see beesky/agent_config.py).
"""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from . import __version__
from . import gui as _gui_theme
from .agent_app import install_task, remove_task, task_installed, \
    test_ingest, _is_windows
from .agent_config import AgentConfig, default_config_path

BG = _gui_theme.BG
PANEL = _gui_theme.PANEL
FG = _gui_theme.FG
ACCENT = _gui_theme.ACCENT
DIM = _gui_theme.DIM


class AgentConfigApp:
    """The agent config window. Test work happens off the UI thread."""

    def __init__(self, root: tk.Tk,
                 config_path: str | Path | None = None):
        self.root = root
        self.config_path = Path(config_path) if config_path is not None \
            else default_config_path()
        self._queue: queue.Queue = queue.Queue()
        self._testing = False
        self._logo_image: tk.PhotoImage | None = None
        self._logo_image_small: tk.PhotoImage | None = None

        root.title(f"BeeSky Agent {__version__} — Cấu hình agent trại")
        root.configure(bg=BG)
        root.minsize(640, 560)
        self._load_logo_image()
        self._set_window_icon()
        self._build_style()
        self._build_widgets()
        self._load_into_fields()
        self.root.after(100, self._poll_queue)

    # -- construction ----------------------------------------------------

    def _build_style(self) -> None:
        # Same ttk style names as beesky.gui (clam theme, dark fields,
        # yellow accent button) so the two windows feel like one app.
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Accent.TButton", background=ACCENT,
                        foreground="#000000",
                        font=("TkDefaultFont", 10, "bold"),
                        padding=(14, 6))
        style.map("Accent.TButton",
                  background=[("active", "#ffe94d"),
                              ("disabled", "#6b6200")])
        style.configure("Dark.TButton", background="#2a2a2a",
                        foreground=FG, padding=(10, 6))
        style.map("Dark.TButton", background=[("active", "#3a3a3a")])
        style.configure("Dark.TEntry", fieldbackground="#000000",
                        foreground=FG, insertcolor=FG)
        style.configure("Dark.TLabel", background=BG, foreground=FG)
        style.configure("Dark.TCheckbutton", background=BG,
                        foreground=FG)

    # -- brand icon (same pattern as beesky.gui) --------------------------

    def _load_logo_image(self) -> None:
        png = _gui_theme._asset_path("beesky-logo-512.png")
        if png is None:
            return
        try:
            self._logo_image = tk.PhotoImage(file=str(png))
        except tk.TclError:
            self._logo_image = None

    def _set_window_icon(self) -> None:
        ico = _gui_theme._asset_path("beesky-logo.ico")
        if ico is not None:
            try:
                self.root.iconbitmap(str(ico))
                return
            except tk.TclError:
                pass
        if self._logo_image is not None:
            try:
                self.root.iconphoto(True, self._logo_image)
            except tk.TclError:
                pass

    def _build_widgets(self) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=16, pady=(14, 2))
        if self._logo_image is not None:
            self._logo_image_small = self._logo_image.subsample(13)
            tk.Label(header, image=self._logo_image_small, bg=BG).pack(
                side="left", padx=(0, 10))
        tk.Label(header, text="BeeSky Agent", bg=BG, fg=ACCENT,
                 font=("TkDefaultFont", 20, "bold")).pack(side="left")
        tk.Label(header, text="Cấu hình agent tại trại", bg=BG, fg=FG,
                 font=("TkDefaultFont", 12)).pack(side="left",
                                                   padx=(10, 0),
                                                   pady=(6, 0))
        tk.Label(header, text=f"v{__version__}", bg=BG, fg=DIM).pack(
            side="right", pady=(8, 0))

        form = tk.Frame(self.root, bg=BG)
        form.pack(fill="x", padx=16, pady=(10, 0))
        form.columnconfigure(1, weight=1)

        def row(idx: int, label: str) -> None:
            tk.Label(form, text=label, bg=BG, fg=FG).grid(
                row=idx, column=0, sticky="w", pady=5, padx=(0, 10))

        self.target_var = tk.StringVar()
        row(0, "Dải IP quét:")
        ttk.Entry(form, textvariable=self.target_var,
                  style="Dark.TEntry").grid(row=0, column=1,
                                            sticky="ew", pady=5)
        tk.Label(form, text="vd 192.168.1.10-192.168.1.60", bg=BG,
                 fg=DIM).grid(row=0, column=2, sticky="w", padx=(8, 0))

        self.cloud_var = tk.StringVar()
        row(1, "Cloud URL:")
        ttk.Entry(form, textvariable=self.cloud_var,
                  style="Dark.TEntry").grid(row=1, column=1,
                                            sticky="ew", pady=5)

        self.key_var = tk.StringVar()
        row(2, "Agent key:")
        self.key_entry = ttk.Entry(form, textvariable=self.key_var,
                                   show="*", style="Dark.TEntry")
        self.key_entry.grid(row=2, column=1, sticky="ew", pady=5)
        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text="Hiện key", variable=self.show_key_var,
                        style="Dark.TCheckbutton",
                        command=self._toggle_key_visibility).grid(
                            row=2, column=2, sticky="w", padx=(8, 0))

        self.site_var = tk.StringVar()
        row(3, "Tên trại:")
        ttk.Entry(form, textvariable=self.site_var,
                  style="Dark.TEntry").grid(row=3, column=1,
                                            sticky="ew", pady=5)
        tk.Label(form, text="vd Xưởng 1", bg=BG, fg=DIM).grid(
            row=3, column=2, sticky="w", padx=(8, 0))

        self.interval_var = tk.StringVar(value="30")
        row(4, "Chu kỳ quét (giây):")
        ttk.Entry(form, textvariable=self.interval_var, width=10,
                  style="Dark.TEntry").grid(row=4, column=1,
                                            sticky="w", pady=5)

        note = tk.Label(
            self.root, bg=BG, fg=DIM, justify="left", wraplength=600,
            text="Agent key do cloud cấp và chỉ hiện MỘT lần lúc tạo "
                 "agent (trang Cài đặt của cloud) — dán vào đây rồi "
                 "Lưu cấu hình. Key chỉ nằm trong file cấu hình này; "
                 "mất key thì thu hồi agent cũ trên cloud và tạo "
                 "agent mới.")
        note.pack(fill="x", padx=16, pady=(10, 0))

        buttons = tk.Frame(self.root, bg=BG)
        buttons.pack(fill="x", padx=16, pady=(12, 4))
        self.save_button = ttk.Button(buttons, text="Lưu cấu hình",
                                      style="Accent.TButton",
                                      command=self.save_config)
        self.save_button.pack(side="left")
        self.test_button = ttk.Button(buttons, text="Chạy thử",
                                      style="Dark.TButton",
                                      command=self.start_test)
        self.test_button.pack(side="left", padx=(10, 0))
        self.autostart_button = ttk.Button(
            buttons, text="Bật tự khởi động", style="Dark.TButton",
            command=self.toggle_autostart)
        self.autostart_button.pack(side="left", padx=(10, 0))
        self.autostart_hint = tk.Label(buttons, text="", bg=BG, fg=DIM)
        self.autostart_hint.pack(side="left", padx=(10, 0))
        self._refresh_autostart()

        self.status_var = tk.StringVar(
            value=f"File cấu hình: {self.config_path}")
        tk.Label(self.root, textvariable=self.status_var, bg=BG,
                 fg=DIM, justify="left", wraplength=600).pack(
                     fill="x", padx=16, pady=(8, 12))

    def _toggle_key_visibility(self) -> None:
        self.key_entry.configure(show="" if self.show_key_var.get()
                                 else "*")

    # -- config <-> fields -------------------------------------------------

    def _load_into_fields(self) -> None:
        if not self.config_path.exists():
            return
        try:
            cfg = AgentConfig.load(self.config_path)
        except ValueError as exc:
            self.status_var.set(f"Không đọc được cấu hình: {exc}")
            return
        self.target_var.set(cfg.target)
        self.cloud_var.set(cfg.cloud_url)
        self.key_var.set(cfg.key)
        self.site_var.set(cfg.site)
        self.interval_var.set(str(int(cfg.interval)
                                  if cfg.interval == int(cfg.interval)
                                  else cfg.interval))
        self.status_var.set(
            f"Đã nạp cấu hình từ {self.config_path} — sửa rồi Lưu, "
            "hoặc Chạy thử ngay.")

    def current_config(self) -> AgentConfig:
        """The form as an AgentConfig (ValueError on a bad interval)."""
        base = AgentConfig()
        if self.config_path.exists():
            try:
                base = AgentConfig.load(self.config_path)
            except ValueError:
                base = AgentConfig()
        data = base.to_dict()
        data.update({
            "target": self.target_var.get().strip(),
            "cloud_url": self.cloud_var.get().strip(),
            "key": self.key_var.get().strip(),
            "site": self.site_var.get().strip(),
        })
        raw_interval = self.interval_var.get().strip()
        try:
            data["interval"] = float(raw_interval)
        except ValueError:
            raise ValueError(
                f"chu kỳ quét {raw_interval!r} không phải số giây "
                "hợp lệ") from None
        if data["interval"] <= 0:
            raise ValueError("chu kỳ quét phải lớn hơn 0 giây")
        return AgentConfig.from_dict(data)

    def save_config(self) -> bool:
        try:
            cfg = self.current_config()
        except ValueError as exc:
            self.status_var.set(f"Chưa lưu được: {exc}")
            return False
        missing = cfg.missing_fields()
        if missing:
            self.status_var.set(
                "Chưa lưu được — còn thiếu: " + ", ".join(missing))
            return False
        try:
            path = cfg.save(self.config_path)
        except OSError as exc:
            self.status_var.set(f"Chưa lưu được: {exc}")
            return False
        self.status_var.set(
            f"Đã lưu cấu hình vào {path} "
            f"({time.strftime('%H:%M:%S')}). Agent chạy bằng: "
            "beesky-agent run")
        return True

    # -- test cycle --------------------------------------------------------

    def start_test(self) -> None:
        if self._testing:
            return
        try:
            cfg = self.current_config()
        except ValueError as exc:
            self.status_var.set(f"Chạy thử thất bại: {exc}")
            return
        self._testing = True
        self.test_button.configure(state="disabled")
        self.status_var.set("Đang chạy thử — quét và đẩy lên cloud …")

        def worker() -> None:
            ok, verdict = test_ingest(cfg)
            stamp = time.strftime("%H:%M:%S")
            self._queue.put(
                ("test", f"{'OK' if ok else 'FAIL'} [{stamp}]: "
                         f"{verdict}"))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "test":
                    self._testing = False
                    self.test_button.configure(state="normal")
                    self.status_var.set(payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    # -- auto-start --------------------------------------------------------

    def _refresh_autostart(self) -> None:
        if not _is_windows():
            self.autostart_button.configure(state="disabled")
            self.autostart_hint.configure(
                text="(Scheduled Task chỉ có trên Windows)")
            return
        installed = task_installed()
        self.autostart_button.configure(
            text="Tắt tự khởi động" if installed else "Bật tự khởi động")

    def toggle_autostart(self) -> None:
        if task_installed():
            _ok, message = remove_task()
        else:
            _ok, message = install_task(self.config_path)
        self.status_var.set(message)
        self._refresh_autostart()


def run_config_gui(config_path: str | Path | None = None) -> int:
    root = tk.Tk()
    AgentConfigApp(root, config_path=config_path)
    root.mainloop()
    return 0


def smoke_config_gui(config_path: str | Path) -> int:
    """Headless self-check for tests: build the window, fill the
    form, save, verify the JSON on disk. Prints AGENT GUI SMOKE
    lines; returns 0 on success."""
    root = tk.Tk()
    app = AgentConfigApp(root, config_path=config_path)
    app.target_var.set("192.168.1.10-192.168.1.60")
    app.cloud_var.set("http://127.0.0.1:8788")
    app.key_var.set("smoke-key")
    app.site_var.set("Xưởng khói")
    app.interval_var.set("45")
    saved = app.save_config()
    root.update()
    root.destroy()
    ok = bool(saved) and Path(config_path).exists()
    if ok:
        cfg = AgentConfig.load(config_path)
        ok = (cfg.site == "Xưởng khói" and cfg.interval == 45.0
              and cfg.key == "smoke-key")
    print("AGENT GUI SMOKE: config window built, form fields present, "
          f"save {'wrote' if ok else 'FAILED to write'} {config_path}")
    return 0 if ok else 1
