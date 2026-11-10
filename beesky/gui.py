"""BeeSky desktop GUI — the windowed face of the LAN tool.

    python -m beesky gui                 open the app window
    python -m beesky gui --smoke TARGET  headless self-check (tests)

Built on tkinter — part of the standard CPython install, so the
stdlib-only rule still holds and PyInstaller bundles it into the
frozen `beesky-gui.exe` windowed build. The GUI runs the exact same
scan pipeline as the CLI / web dashboard (`cli._scan_records` via a
synthetic argparse namespace), on a worker thread; results come back
to the UI thread through a queue so the window never freezes.

The console CLI stays for power users — this window is for people
who just want to double-click, type an IP range and press
"Quét ngay".
"""

from __future__ import annotations

import argparse
import queue
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, ttk

from . import __version__
from .core import report

BG = "#111111"
PANEL = "#1b1b1b"
FG = "#ffffff"
ACCENT = "#F5D800"
DIM = "#9a9a9a"
PROBLEM_BG = "#4a3400"   # dark amber row highlight for CHECK miners
ERROR_BG = "#4a1616"     # dark red row highlight for fetch errors

SOURCE_LABEL = {
    "cgminer": "cgminer RPC",
    "vnish": "VNish",
    "stock": "Bitmain gốc",
}

WEB_PORT = 8787


def _asset_path(name: str) -> Path | None:
    """Where a bundled brand asset may live: frozen bundle first, source.

    In the PyInstaller one-file exe the logo files ship as data under
    ``sys._MEIPASS/beesky/assets/`` (see packaging/beesky.spec); in a
    source checkout they sit in ``packaging/assets/``. Same lookup
    pattern as the dashboard HTML in beesky/web/server.py.
    """
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "beesky" / "assets" / name)
    candidates.append(Path(__file__).resolve().parent.parent
                      / "packaging" / "assets" / name)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def make_scan_args(target: str, user: str = "root",
                   password: str = "root") -> argparse.Namespace:
    """Argparse namespace with the CLI's own defaults for one scan."""
    return argparse.Namespace(
        target=target, timeout=1.5, workers=64,
        user=user or "root", password=password or "root",
        api_key=None, token=None, http_port=80, cgminer_port=4028,
    )


def _scan(target: str, user: str, password: str) -> list[dict]:
    """One scan pass through the shared CLI pipeline."""
    from .cli import _scan_records  # deferred: cli imports are heavier
    return _scan_records(make_scan_args(target, user, password))


def _fmt(value, fmt="{:.2f}", fallback="-"):
    return fmt.format(value) if value is not None else fallback


def row_values(record: dict) -> tuple[str, ...]:
    """The Treeview row for one normalised status record."""
    chips = (f"{record['chips_alive']}/{record['chips_total']}"
             if record.get("chips_total") else "-")
    fans = "/".join(str(f) for f in record.get("fans_rpm") or []) or "-"
    return (
        record["ip"],
        str(record.get("model") or "Unknown"),
        SOURCE_LABEL.get(record.get("source"), str(record.get("source", "-"))),
        _fmt(record.get("ths")),
        chips,
        _fmt(record.get("max_temp_c"), "{:.0f}"),
        fans,
        record.get("status", "-"),
    )


class BeeSkyApp:
    """The main window. All scan work happens off the UI thread."""

    def __init__(self, root: tk.Tk, default_target: str = "192.168.1.0/24"):
        self.root = root
        self.records: list[dict] = []
        self._queue: queue.Queue = queue.Queue()
        self._scanning = False
        self.scan_done = threading.Event()   # used by --smoke
        self._serve_started = False
        self._logo_image: tk.PhotoImage | None = None
        self._logo_image_small: tk.PhotoImage | None = None

        root.title(f"BeeSky {__version__} — Quét & chẩn đoán máy đào")
        root.configure(bg=BG)
        root.minsize(880, 540)
        self._load_logo_image()
        self._set_window_icon()
        self._build_style()
        self._build_widgets(default_target)
        self.root.after(100, self._poll_queue)

    # -- construction ----------------------------------------------------

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=FG, rowheight=24, font=("TkDefaultFont", 10))
        style.configure("Treeview.Heading", background="#000000",
                        foreground=ACCENT, font=("TkDefaultFont", 10, "bold"))
        style.map("Treeview", background=[("selected", "#333300")],
                  foreground=[("selected", FG)])
        style.configure("Accent.TButton", background=ACCENT, foreground="#000000",
                        font=("TkDefaultFont", 10, "bold"), padding=(14, 6))
        style.map("Accent.TButton", background=[("active", "#ffe94d"),
                                                ("disabled", "#6b6200")])
        style.configure("Dark.TButton", background="#2a2a2a", foreground=FG,
                        padding=(10, 6))
        style.map("Dark.TButton", background=[("active", "#3a3a3a")])
        style.configure("Dark.TEntry", fieldbackground="#000000",
                        foreground=FG, insertcolor=FG)
        style.configure("Dark.TLabel", background=BG, foreground=FG)

    # -- brand icon ------------------------------------------------------

    def _load_logo_image(self) -> None:
        """Load the official logo PNG once (window icon + header).

        The PhotoImage must stay referenced on self — tkinter images
        are garbage-collected with their last Python reference.
        Best effort: a missing/unreadable asset leaves the GUI plain.
        """
        png = _asset_path("beesky-logo-512.png")
        if png is None:
            return
        try:
            self._logo_image = tk.PhotoImage(file=str(png))
        except tk.TclError:
            self._logo_image = None

    def _set_window_icon(self) -> None:
        """Window icon: the .ico where supported, else the PNG.

        iconbitmap with a .ico is the Windows path; on X11 it raises
        TclError, so fall back to iconphoto with the PNG. Guarded —
        an icon must never stop the app from opening (headless and
        source runs included).
        """
        ico = _asset_path("beesky-logo.ico")
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

    def _build_widgets(self, default_target: str) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=14, pady=(12, 2))
        if self._logo_image is not None:
            # 512px master subsampled to ~40px for the header.
            self._logo_image_small = self._logo_image.subsample(13)
            tk.Label(header, image=self._logo_image_small, bg=BG).pack(
                side="left", padx=(0, 10))
        tk.Label(header, text="BeeSky", bg=BG, fg=ACCENT,
                 font=("TkDefaultFont", 22, "bold")).pack(side="left")
        tk.Label(header, text="Quét & chẩn đoán máy đào", bg=BG, fg=FG,
                 font=("TkDefaultFont", 12)).pack(side="left", padx=(10, 0),
                                                  pady=(8, 0))
        tk.Label(header, text=f"v{__version__}", bg=BG, fg=DIM).pack(
            side="right", pady=(10, 0))

        controls = tk.Frame(self.root, bg=BG)
        controls.pack(fill="x", padx=14, pady=(8, 4))
        tk.Label(controls, text="Dải IP / máy:", bg=BG, fg=FG).pack(side="left")
        self.target_var = tk.StringVar(value=default_target)
        ttk.Entry(controls, textvariable=self.target_var, width=24,
                  style="Dark.TEntry").pack(side="left", padx=(6, 14))
        tk.Label(controls, text="User:", bg=BG, fg=FG).pack(side="left")
        self.user_var = tk.StringVar(value="root")
        ttk.Entry(controls, textvariable=self.user_var, width=10,
                  style="Dark.TEntry").pack(side="left", padx=(6, 10))
        tk.Label(controls, text="Mật khẩu:", bg=BG, fg=FG).pack(side="left")
        self.password_var = tk.StringVar(value="root")
        ttk.Entry(controls, textvariable=self.password_var, width=12,
                  show="*", style="Dark.TEntry").pack(side="left", padx=(6, 14))
        self.scan_button = ttk.Button(controls, text="Quét ngay",
                                      style="Accent.TButton",
                                      command=self.start_scan)
        self.scan_button.pack(side="left")
        self.status_var = tk.StringVar(value="Sẵn sàng — nhập dải IP rồi bấm Quét ngay.")
        tk.Label(controls, textvariable=self.status_var, bg=BG, fg=DIM).pack(
            side="left", padx=(14, 0))

        table_frame = tk.Frame(self.root, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=14, pady=(6, 4))
        columns = ("ip", "model", "source", "ths", "chips", "temp", "fans",
                   "status")
        headings = {"ip": "IP", "model": "Model", "source": "Nguồn",
                    "ths": "Hashrate (TH/s)", "chips": "Chip",
                    "temp": "Nhiệt độ", "fans": "Quạt", "status": "Trạng thái"}
        widths = {"ip": 110, "model": 170, "source": 100, "ths": 110,
                  "chips": 70, "temp": 70, "fans": 130, "status": 90}
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.column("model", anchor="w")
        self.tree.tag_configure("check", background=PROBLEM_BG)
        self.tree.tag_configure("error", background=ERROR_BG)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        detail_frame = tk.LabelFrame(self.root, text="Chi tiết máy đã chọn",
                                     bg=BG, fg=ACCENT, padx=8, pady=6)
        detail_frame.pack(fill="x", padx=14, pady=(2, 6))
        self.detail = tk.Text(detail_frame, height=6, bg=PANEL, fg=FG,
                              insertbackground=FG, relief="flat",
                              font=("TkDefaultFont", 10), wrap="word")
        self.detail.pack(fill="x")
        self.detail.insert("end", "Chọn một máy trong bảng để xem chi tiết "
                                  "và danh sách vấn đề.")
        self.detail.configure(state="disabled")

        buttons = tk.Frame(self.root, bg=BG)
        buttons.pack(fill="x", padx=14, pady=(0, 12))
        ttk.Button(buttons, text="Xuất phiếu sửa", style="Dark.TButton",
                   command=self.export_tickets).pack(side="left")
        ttk.Button(buttons, text="Mở web tại chỗ", style="Dark.TButton",
                   command=self.open_local_web).pack(side="left", padx=(10, 0))
        ttk.Button(buttons, text="Quét lại", style="Dark.TButton",
                   command=self.start_scan).pack(side="left", padx=(10, 0))

    # -- scanning ----------------------------------------------------------

    def start_scan(self) -> None:
        if self._scanning:
            return
        target = self.target_var.get().strip()
        if not target:
            self.status_var.set("Chưa nhập dải IP / địa chỉ máy.")
            return
        self._scanning = True
        self.scan_button.configure(state="disabled")
        self.status_var.set(f"Đang quét {target} …")
        user, password = self.user_var.get(), self.password_var.get()

        def worker() -> None:
            try:
                records = _scan(target, user, password)
                self._queue.put(("records", records))
            except Exception as exc:  # surfaced in the status line
                self._queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "records":
                    self.show_records(payload)
                else:
                    self.status_var.set(f"Lỗi khi quét: {payload}")
                    self._finish_scan()
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _finish_scan(self) -> None:
        self._scanning = False
        self.scan_button.configure(state="normal")
        self.scan_done.set()

    def show_records(self, records: list[dict]) -> None:
        self.records = records
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, record in enumerate(records):
            tag = ""
            if any(p.get("code") == "FETCH_ERROR"
                   for p in record.get("problems") or []):
                tag = "error"
            elif record.get("status") != "OK":
                tag = "check"
            self.tree.insert("", "end", iid=str(idx),
                             values=row_values(record),
                             tags=(tag,) if tag else ())
        bad = sum(1 for r in records if r.get("status") != "OK")
        self.status_var.set(
            f"Quét xong: {len(records)} máy, {bad} máy cần kiểm tra."
            if records else "Quét xong: không tìm thấy máy nào.")
        self._finish_scan()

    # -- detail pane ---------------------------------------------------------

    def _on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        record = self.records[int(selection[0])]
        lines = [
            f"{record['ip']} — {record.get('model') or 'Unknown'} "
            f"({SOURCE_LABEL.get(record.get('source'), record.get('source'))})",
            f"Hashrate: {_fmt(record.get('ths'))} TH/s | "
            f"Chip: {record.get('chips_alive', 0)}/{record.get('chips_total', 0)} | "
            f"Nhiệt độ cao nhất: {_fmt(record.get('max_temp_c'), '{:.0f}')} °C | "
            f"Quạt: {'/'.join(str(f) for f in record.get('fans_rpm') or []) or '-'} RPM",
            f"Trạng thái: {record.get('status', '-')}",
        ]
        problems = record.get("problems") or []
        if problems:
            lines.append("Vấn đề:")
            lines += [f"  • [{p.get('code', '?')}] {p.get('detail', '')}"
                      for p in problems]
        else:
            lines.append("Không phát hiện vấn đề.")
        for chain in record.get("chains") or []:
            temp = _fmt(chain.get("temp_c"), "{:.0f}")
            lines.append(
                f"  Board {chain['index']}: {chain['chips_alive']}/"
                f"{chain['chips_total']} chip, nhiệt {temp} °C")
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("end", "\n".join(lines))
        self.detail.configure(state="disabled")

    # -- actions -------------------------------------------------------

    def export_tickets(self) -> None:
        if not self.records:
            self.status_var.set("Chưa có kết quả quét để xuất phiếu.")
            return
        folder = filedialog.askdirectory(title="Chọn thư mục lưu phiếu sửa")
        if not folder:
            return
        written = report.write_tickets(self.records, Path(folder))
        if written:
            self.status_var.set(
                f"Đã xuất {len(written)} phiếu sửa vào: {folder}")
        else:
            self.status_var.set(
                "Không có máy nào có vấn đề — không phiếu nào được xuất.")

    def open_local_web(self) -> None:
        target = self.target_var.get().strip() or "192.168.1.0/24"
        if not self._serve_started:
            from .web.server import MonitorService, run_server
            args = make_scan_args(target, self.user_var.get(),
                                  self.password_var.get())

            def scan_fn():
                from .cli import _scan_records
                return _scan_records(args)

            service = MonitorService(scan_fn, target=target, interval=30.0,
                                     notify_config={})
            thread = threading.Thread(
                target=lambda: run_server(service, host="127.0.0.1",
                                          port=WEB_PORT),
                daemon=True)
            thread.start()
            self._serve_started = True
        webbrowser.open(f"http://127.0.0.1:{WEB_PORT}/")
        self.status_var.set(
            f"Đã mở web tại chỗ: http://127.0.0.1:{WEB_PORT}/ "
            f"(quét {target} mỗi 30 giây)")


def run_gui(default_target: str = "192.168.1.0/24") -> int:
    root = tk.Tk()
    BeeSkyApp(root, default_target=default_target)
    root.mainloop()
    return 0


def smoke(target: str) -> int:
    """Headless self-check: build the UI, run one scan, print the rows.

    Used by tests/mock_gui_test.py under xvfb-run. Prints the row
    count and the first row, then exits 0 on success.
    """
    root = tk.Tk()
    app = BeeSkyApp(root, default_target=target)
    app.target_var.set(target)
    app.start_scan()
    waited = 0.0
    while not app.scan_done.is_set() and waited < 120.0:
        root.update()
        app.scan_done.wait(0.05)
        waited += 0.05
    rows = [app.tree.item(iid, "values") for iid in app.tree.get_children()]
    out = [f"GUI SMOKE: {len(rows)} row(s) for target {target}"]
    if rows:
        out.append("GUI SMOKE first row: " + " | ".join(str(v) for v in rows[0]))
    text = "\n".join(out)
    try:
        print(text, flush=True)
    except Exception:
        pass  # windowed frozen builds may have no stdout — tests use source
    root.destroy()
    return 0 if rows else 1
