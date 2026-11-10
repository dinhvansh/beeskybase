"""BeeSky Agent config window — the face of the agent app.

    beesky-agent            (no arguments -> this window)
    python -m beesky.agent_app

One small tkinter form (stdlib only, styled by the shared design
system in beesky/ui_theme.py — the same palette as the main BeeSky
GUI and the cloud dashboard): the farm operator fills in the scan
target, the cloud URL, the agent key from the cloud's Cài đặt page
and the site name once, presses "Chạy thử" to watch a real ingest
land, saves, and flips on auto-start. After that the agent runs
itself via the Windows Scheduled Task (or any other launcher) with
`beesky-agent run` — no window needed.

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
from . import ui_theme
from .agent_app import install_task, remove_task, task_installed, \
    test_ingest, _is_windows
from .agent_config import AgentConfig, default_config_path

BG = ui_theme.BG
PANEL = ui_theme.PANEL
FG = ui_theme.TEXT
ACCENT = ui_theme.ACCENT
DIM = ui_theme.MUTED

_KEY_NOTE = (
    "Agent key do cloud cấp và chỉ hiện MỘT lần lúc tạo agent "
    "(trang Cài đặt của cloud) — dán vào đây rồi Lưu cấu hình. "
    "Key chỉ nằm trong file cấu hình này; mất key thì thu hồi "
    "agent cũ trên cloud và tạo agent mới.")


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
        ui_theme.setup_theme(root)
        self._load_logo_image()
        self._set_window_icon()
        self._build_widgets()
        self._load_into_fields()
        self.root.after(100, self._poll_queue)

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
        main = ttk.Frame(self.root, padding=(18, 14, 18, 14))
        main.pack(fill="both", expand=True)

        # -- header: logo + title + version chip -----------------------
        header = ttk.Frame(main)
        header.pack(fill="x")
        if self._logo_image is not None:
            # 512px master subsampled to ~40px for the header.
            self._logo_image_small = self._logo_image.subsample(13)
            ttk.Label(header, image=self._logo_image_small).pack(
                side="left", padx=(0, 10))
        titles = ttk.Frame(header)
        titles.pack(side="left")
        ttk.Label(titles, text="BeeSky Agent",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text="Cấu hình agent tại trại",
                  style="Sub.TLabel").pack(anchor="w")
        tk.Label(header, text=f"v{__version__}", bg=ui_theme.PANEL2,
                 fg=ui_theme.MUTED, padx=8, pady=2,
                 font=(ui_theme.font_family(self.root),
                       ui_theme.SMALL_SIZE, "bold")).pack(side="right")

        # -- card 1: cloud connection ----------------------------------
        self.cloud_var = tk.StringVar()
        self.key_var = tk.StringVar()
        self.site_var = tk.StringVar()
        self.show_key_var = tk.BooleanVar(value=False)

        connect = ui_theme.card(main, title="Kết nối cloud")
        connect.pack(fill="x", pady=(14, 0))
        body = ttk.Frame(connect, style="Card.TFrame")
        body.pack(fill="x")
        body.columnconfigure(0, weight=1)

        cloud_entry = ttk.Entry(body, textvariable=self.cloud_var)
        ui_theme.labeled_field(body, 0, "Cloud URL:", cloud_entry)

        key_box = ttk.Frame(body, style="Card.TFrame")
        self.key_entry = ttk.Entry(key_box, textvariable=self.key_var,
                                   show="*")
        self.key_entry.pack(side="left", fill="x", expand=True)
        ttk.Checkbutton(key_box, text="Hiện key",
                        variable=self.show_key_var,
                        style="Card.TCheckbutton",
                        command=self._toggle_key_visibility).pack(
                            side="left", padx=(8, 0))
        ui_theme.labeled_field(body, 1, "Agent key:", key_box)

        site_entry = ttk.Entry(body, textvariable=self.site_var)
        ui_theme.labeled_field(body, 2, "Tên trại:", site_entry,
                               hint="vd Xưởng 1")

        ttk.Label(connect, text=_KEY_NOTE, style="Card.Hint.TLabel",
                  wraplength=600, justify="left").pack(
                      anchor="w", pady=(12, 0))

        # -- card 2: farm scan ------------------------------------------
        self.target_var = tk.StringVar()
        self.interval_var = tk.StringVar(value="30")

        scan = ui_theme.card(main, title="Quét tại trại")
        scan.pack(fill="x", pady=(12, 0))
        sbody = ttk.Frame(scan, style="Card.TFrame")
        sbody.pack(fill="x")
        sbody.columnconfigure(0, weight=1)

        target_entry = ttk.Entry(sbody, textvariable=self.target_var)
        ui_theme.labeled_field(sbody, 0, "Dải IP quét:", target_entry,
                               hint="vd 192.168.1.10-192.168.1.60")

        interval_entry = ttk.Entry(sbody,
                                   textvariable=self.interval_var,
                                   width=10)
        ui_theme.labeled_field(sbody, 1, "Chu kỳ quét (giây):",
                               interval_entry)
        interval_entry.grid_configure(sticky="w")

        # -- actions + status pill ---------------------------------------
        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=(14, 0))
        self.save_button = ttk.Button(actions, text="Lưu cấu hình",
                                      style="Accent.TButton",
                                      command=self.save_config)
        self.save_button.pack(side="left")
        self.test_button = ttk.Button(actions, text="Chạy thử",
                                      style="Ghost.TButton",
                                      command=self.start_test)
        self.test_button.pack(side="left", padx=(10, 0))
        self.autostart_button = ttk.Button(
            actions, text="Bật tự khởi động", style="Ghost.TButton",
            command=self.toggle_autostart)
        self.autostart_button.pack(side="left", padx=(10, 0))
        self.test_pill = ui_theme.status_pill(
            actions, text="Chưa chạy thử", state="dim")
        self.test_pill.pack(side="right")
        self.autostart_hint = ttk.Label(main, text="",
                                        style="Hint.TLabel")
        self.autostart_hint.pack(anchor="w", pady=(6, 0))
        self._refresh_autostart()

        # -- footer status line ------------------------------------------
        self.status_var = tk.StringVar(
            value=f"File cấu hình: {self.config_path}")
        ttk.Label(main, textvariable=self.status_var,
                  style="Hint.TLabel", justify="left",
                  wraplength=620).pack(fill="x", pady=(8, 0))

        ui_theme.center_window(self.root)

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
            ui_theme.set_pill(self.test_pill, "bad", "Chạy thử: FAIL")
            return
        self._testing = True
        self.test_button.configure(state="disabled")
        self.status_var.set("Đang chạy thử — quét và đẩy lên cloud …")
        ui_theme.set_pill(self.test_pill, "warn", "Đang chạy thử…")

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
                    if payload.startswith("OK"):
                        ui_theme.set_pill(self.test_pill, "ok",
                                          "Chạy thử: OK")
                    else:
                        ui_theme.set_pill(self.test_pill, "bad",
                                          "Chạy thử: FAIL")
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
