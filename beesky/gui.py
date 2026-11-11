"""BeeSky desktop GUI — the windowed face of the LAN tool.

    python -m beesky gui                 open the app window
    python -m beesky gui --smoke TARGET  headless self-check (tests)

Built on tkinter — part of the standard CPython install, so the
stdlib-only rule still holds and PyInstaller bundles it into the
frozen `beesky-gui.exe` windowed build. The GUI runs the exact same
scan pipeline as the CLI / web dashboard (`cli._scan_records` via a
synthetic argparse namespace), on a worker thread; results come back
to the UI thread through a queue so the window never freezes.

Styling lives in beesky/ui_theme.py (shared with the agent config
window and matched to the cloud dashboard palette) — this module
only lays out cards and wires behaviour.

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
from . import ui_theme
from .core import report
from .core.discover import default_scan_target
from .rounded import RoundedButton, RoundedCard, RoundedEntry

BG = ui_theme.BG
PANEL = ui_theme.PANEL
FG = ui_theme.TEXT
ACCENT = ui_theme.ACCENT
DIM = ui_theme.MUTED
PROBLEM_BG = "#463A10"   # dark amber row highlight for CHECK miners
ERROR_BG = "#472020"     # dark red row highlight for fetch errors

SOURCE_LABEL = {
    "cgminer": "cgminer RPC",
    "vnish": "VNish",
    "stock": "Bitmain gốc",
    "whatsminer": "Whatsminer",
    "avalon": "Avalon (Canaan)",
}

WEB_PORT = 8787

DETAIL_PLACEHOLDER = ("Chọn một máy trong bảng để xem chi tiết "
                      "và danh sách vấn đề.")


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
        report.format_rate(record),
        chips,
        _fmt(record.get("max_temp_c"), "{:.0f}"),
        fans,
        record.get("status", "-"),
    )


class BeeSkyApp:
    """The main window. All scan work happens off the UI thread."""

    def __init__(self, root: tk.Tk, default_target: str | None = None):
        # No explicit target -> pre-fill with this machine's own
        # subnet (v0.19.6; the hard-coded 192.168.1.0/24 found zero
        # miners on any other network).
        if default_target is None:
            default_target = default_scan_target()
        self.root = root
        self.records: list[dict] = []
        self._queue: queue.Queue = queue.Queue()
        self._scanning = False
        self.scan_done = threading.Event()   # used by --smoke
        self._serve_started = False
        self._logo_image: tk.PhotoImage | None = None
        self._logo_image_small: tk.PhotoImage | None = None

        root.title(f"BeeSky {__version__} — Quét & chẩn đoán máy đào")
        self._family = ui_theme.setup_theme(root)
        self._load_logo_image()
        self._set_window_icon()
        self._build_widgets(default_target)
        self._fit_window()
        self.root.after(100, self._poll_queue)

    def _fit_window(self) -> None:
        """Size the window to the screen, capped at 1120x880 (v0.19.7).

        First-run field report: the fixed 1120x880 window was taller
        than the usable screen on the owner's laptop (Windows
        scaling), so the bottom sank under the taskbar and the
        flexible table row collapsed to about one visible row. Cap
        the start size at screen − 32 wide / − 72 high (the 72
        leaves room for the taskbar) and centre what's left; on a
        large screen this is exactly the old 1120x880, centred. The
        min size tracks the cap so it can never fight it on a small
        screen; otherwise it stays the v0.15.2 (940, 720) under
        which the detail pane keeps its full height.
        """
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = min(1120, max(0, screen_w - 32))
        height = min(880, max(0, screen_h - 72))
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(min(940, width), min(720, height))

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

    # -- layout ------------------------------------------------------------

    def _stat_card(self, parent: ttk.Frame, column: int, title: str,
                   value: str, fg: str = ui_theme.TEXT) -> tk.StringVar:
        """One stat card in the stats row; returns its value var."""
        frame = ui_theme.card(parent)
        frame.grid(row=0, column=column, sticky="nsew",
                   padx=(0, 10) if column < 3 else 0)
        ttk.Label(frame, text=title,
                  style="StatTitle.TLabel").pack(anchor="w")
        var = tk.StringVar(value=value)
        label = tk.Label(frame, textvariable=var,
                         bg=ui_theme.PANEL_GLASS,
                         fg=fg, font=(self._family,
                                      ui_theme.STAT_SIZE, "bold"))
        label.pack(anchor="w", pady=(4, 0))
        if title == "Máy có vấn đề":
            self._problem_value_label = label
        return var

    def _build_widgets(self, default_target: str) -> None:
        main = ttk.Frame(self.root, padding=(22, 16, 22, 16))
        main.pack(fill="both", expand=True)
        # Grid (not pack) so that when the window is shorter than the full
        # content request, the RESULTS TABLE row absorbs the shrink and the
        # detail pane below it always keeps its full height.
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1, minsize=150)

        # -- header band ------------------------------------------------
        header = ttk.Frame(main)
        header.grid(row=0, column=0, sticky="ew")
        if self._logo_image is not None:
            # 512px master subsampled to ~40px for the header.
            self._logo_image_small = self._logo_image.subsample(13)
            ttk.Label(header, image=self._logo_image_small).pack(
                side="left", padx=(0, 10))
        titles = ttk.Frame(header)
        titles.pack(side="left")
        ttk.Label(titles, text="BeeSky",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text="Giám sát & chẩn đoán máy đào ASIC",
                  style="Sub.TLabel").pack(anchor="w")
        ttk.Label(header, text=f"v{__version__}",
                  style="Sub.TLabel").pack(side="right")

        # -- toolbar card -------------------------------------------------
        toolbar = ui_theme.card(main, title="Mục tiêu quét", pad=18)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        target_row = ttk.Frame(toolbar, style="Card.TFrame")
        target_row.pack(fill="x")
        self.target_var = tk.StringVar(value=default_target)
        RoundedEntry(target_row, textvariable=self.target_var,
                     backdrop=ui_theme.PANEL_GLASS).pack(
                         side="left", fill="x", expand=True)
        self.scan_button = RoundedButton(
            target_row, text="Quét ngay", variant="accent",
            command=self.start_scan, backdrop=ui_theme.PANEL_GLASS)
        self.scan_button.pack(side="left", padx=(10, 0))
        RoundedButton(target_row, text="Xuất phiếu sửa",
                      variant="ghost", command=self.export_tickets,
                      backdrop=ui_theme.PANEL_GLASS).pack(
                          side="left", padx=(10, 0))
        RoundedButton(target_row, text="Mở web tại chỗ",
                      variant="ghost", command=self.open_local_web,
                      backdrop=ui_theme.PANEL_GLASS).pack(
                          side="left", padx=(10, 0))
        RoundedButton(target_row, text="Quét lại", variant="ghost",
                      command=self.start_scan,
                      backdrop=ui_theme.PANEL_GLASS).pack(side="left",
                                                    padx=(10, 0))

        creds_row = ttk.Frame(toolbar, style="Card.TFrame")
        creds_row.pack(fill="x", pady=(10, 0))
        ttk.Label(creds_row, text="User:",
                  style="Card.TLabel").pack(side="left")
        self.user_var = tk.StringVar(value="root")
        RoundedEntry(creds_row, textvariable=self.user_var, width=12,
                     backdrop=ui_theme.PANEL_GLASS).pack(side="left",
                                                   padx=(6, 14))
        ttk.Label(creds_row, text="Mật khẩu:",
                  style="Card.TLabel").pack(side="left")
        self.password_var = tk.StringVar(value="root")
        RoundedEntry(creds_row, textvariable=self.password_var,
                     width=14, show="*",
                     backdrop=ui_theme.PANEL_GLASS).pack(side="left",
                                                   padx=(6, 0))
        ttk.Label(creds_row,
                  text="— tài khoản web của máy chạy firmware gốc",
                  style="Card.Hint.TLabel").pack(side="left",
                                                 padx=(12, 0))

        # -- stats row ------------------------------------------------------
        stats = ttk.Frame(main)
        stats.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        for col in range(4):
            stats.columnconfigure(col, weight=1)
        self.stat_total_var = self._stat_card(stats, 0, "Tổng số máy",
                                              "0")
        self.stat_ths_var = self._stat_card(stats, 1, "Tổng hashrate",
                                            "0.00", fg=ui_theme.ACCENT)
        self.stat_problem_var = self._stat_card(stats, 2,
                                                "Máy có vấn đề", "0")
        self.stat_temp_var = self._stat_card(stats, 3,
                                             "Nhiệt độ cao nhất", "-")

        # -- results table --------------------------------------------------
        table_card = ui_theme.card(main, pad=14)
        table_card.grid(row=3, column=0, sticky="nsew", pady=(14, 0))
        # v0.19: the tree sits in a dark inset WELL (radius 12,
        # TABLE_WELL fill, hairline outline) inside the glass card —
        # its square corners never touch the card's rounded corners,
        # and the well + the pinned Treeview border colours leave no
        # light clam frame around it. v0.19.2: the well keeps a clear
        # glass rim on every side (external padding + the brighter
        # GLASS_BORDER hairline) — without it the near-black well
        # visually bled into the near-black window backdrop and the
        # table looked like it spilled edge to edge.
        table_frame = RoundedCard(table_card, pad=10,
                                  radius=ui_theme.RADIUS_WIDGET,
                                  backdrop=ui_theme.PANEL_GLASS,
                                  fill=ui_theme.TABLE_WELL,
                                  outline=ui_theme.GLASS_BORDER)
        table_frame.pack(fill="both", expand=True, padx=6, pady=6)
        columns = ("ip", "model", "source", "ths", "chips", "temp", "fans",
                   "status")
        headings = {"ip": "IP", "model": "Model", "source": "Nguồn",
                    "ths": "Hashrate", "chips": "Chip",
                    "temp": "Nhiệt độ", "fans": "Quạt", "status": "Trạng thái"}
        widths = {"ip": 110, "model": 150, "source": 95, "ths": 135,
                  "chips": 70, "temp": 70, "fans": 150, "status": 90}
        self.tree = ttk.Treeview(table_frame, columns=columns, height=7,
                                 show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.column("model", anchor="w")
        self.tree.tag_configure("check", background=PROBLEM_BG,
                                foreground=FG)
        self.tree.tag_configure("error", background=ERROR_BG,
                                foreground=FG)
        self.tree.tag_configure("odd",
                                background=ui_theme.TABLE_ZEBRA)
        self.tree.pack(side="left", fill="both", expand=True)
        self.table_scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview)
        self._scrollbar_shown = True
        self.tree.configure(yscrollcommand=self._on_tree_yscroll)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # -- detail pane ------------------------------------------------------
        detail_card = ui_theme.card(main, title="Chi tiết máy đã chọn",
                                    pad=12)
        detail_card.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        # v0.19: no box of its own — the text sits flat on the
        # glass card (PANEL_GLASS, zero border/highlight).
        self.detail = tk.Text(detail_card, height=5,
                              bg=ui_theme.PANEL_GLASS, fg=FG,
                              insertbackground=FG, relief="flat",
                              borderwidth=0, highlightthickness=0,
                              font=(self._family, ui_theme.BODY_SIZE),
                              wrap="word", padx=10, pady=8)
        self.detail.pack(fill="x")
        self.detail.insert("end", DETAIL_PLACEHOLDER)
        self.detail.configure(state="disabled")

        # -- footer status bar --------------------------------------------------
        footer = ttk.Frame(main)
        footer.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        self.status_var = tk.StringVar(
            value="Sẵn sàng — nhập dải IP rồi bấm Quét ngay.")
        ttk.Label(footer, textvariable=self.status_var,
                  style="Hint.TLabel").pack(side="left")

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
                    self._land_on_first(payload)
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
            if tag:
                tags = (tag,)
            elif idx % 2 == 1:
                # Zebra parity is for plain OK rows only — a
                # problem row always keeps its status wash.
                tags = ("odd",)
            else:
                tags = ()
            self.tree.insert("", "end", iid=str(idx),
                             values=row_values(record), tags=tags)
        bad = sum(1 for r in records if r.get("status") != "OK")
        self._update_stats(records, bad)
        self.status_var.set(
            f"Quét xong: {len(records)} máy, {bad} máy cần kiểm tra."
            if records else "Quét xong: không tìm thấy máy nào.")
        self._finish_scan()

    def _land_on_first(self, records: list[dict]) -> None:
        """After a scan, land on the first miner (v0.19.7).

        Field report: the scan filled the table but nothing was
        selected, so the detail pane kept its placeholder and the
        owner concluded details could not be viewed at all. Select
        + focus the first row, scroll it into view and fill the
        pane through the same _on_select path a click uses. The
        rows were just rebuilt by show_records, so the selection
        can never point at a dead row from a previous scan. An
        empty result restores the placeholder instead of leaving
        a previous scan's detail on screen. This lives in the
        scan-completion path on purpose: show_records is also
        called directly (tests) where no landing is wanted.
        """
        children = self.tree.get_children()
        if records and children:
            first = children[0]
            self.tree.selection_set(first)
            self.tree.focus(first)
            self.tree.see(first)
            self._on_select()
        elif not records:
            self._set_detail_text(DETAIL_PLACEHOLDER)

    def _update_stats(self, records: list[dict], bad: int) -> None:
        """Refresh the four stat cards from the latest scan."""
        self.stat_total_var.set(str(len(records)))
        # v0.20: the total groups by native unit — a mixed fleet shows
        # one figure per unit instead of a meaningless mixed sum. A
        # single TH/s group keeps the historical bare-number rendering.
        groups = report.fleet_rate_totals(records)
        if not groups:
            self.stat_ths_var.set("0.00")
        elif len(groups) == 1 and groups[0][1] == "TH/s":
            self.stat_ths_var.set(f"{groups[0][0]:.2f}")
        else:
            self.stat_ths_var.set(report.format_rate_totals(records))
        self.stat_problem_var.set(str(bad))
        self._problem_value_label.configure(
            fg=ui_theme.BAD if bad else ui_theme.TEXT)
        temps = [r["max_temp_c"] for r in records
                 if r.get("max_temp_c") is not None]
        self.stat_temp_var.set(
            f"{max(temps):.0f} °C" if temps else "-")

    # -- detail pane ---------------------------------------------------------

    def _set_detail_text(self, text: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("end", text)
        self.detail.configure(state="disabled")

    def _on_tree_yscroll(self, first: str, last: str) -> None:
        """Feed the scrollbar and auto-hide it when nothing scrolls.

        A permanently visible scrollbar is the loudest rectangle in
        the window (and renders pale under some Tk builds); modern
        tables only show it while the content actually overflows.
        """
        self.table_scrollbar.set(first, last)
        try:
            fits = float(first) <= 0.0 and float(last) >= 1.0
        except (TypeError, ValueError):
            fits = False
        if fits and self._scrollbar_shown:
            self.table_scrollbar.pack_forget()
            self._scrollbar_shown = False
        elif not fits and not self._scrollbar_shown:
            self.table_scrollbar.pack(side="right", fill="y")
            self._scrollbar_shown = True

    def _on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        record = self.records[int(selection[0])]
        lines = [
            f"{record['ip']} — {record.get('model') or 'Unknown'} "
            f"({SOURCE_LABEL.get(record.get('source'), record.get('source'))})",
            f"Hashrate: {report.format_rate(record)} | "
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
        self._set_detail_text("\n".join(lines))

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
        target = self.target_var.get().strip() or default_scan_target()
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


def run_gui(default_target: str | None = None) -> int:
    root = tk.Tk()
    BeeSkyApp(root, default_target=default_target)
    root.mainloop()
    return 0


def smoke(target: str) -> int:
    """Headless self-check: build the UI, run one scan, print the rows.

    Used by tests/mock_gui_test.py under xvfb-run. Prints the row
    count and the first row, plus (v0.19.7) the post-scan selection,
    the detail pane's first line and the fitted window geometry,
    then exits 0 when at least one row was found.
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
    # v0.19.7 first-run checks: post-scan landing (selection +
    # detail content) and the screen-fitted window geometry.
    root.update_idletasks()
    selection = app.tree.selection()
    out.append("GUI SMOKE selection: "
               + (selection[0] if selection else "-"))
    detail_text = app.detail.get("1.0", "end").strip()
    out.append("GUI SMOKE detail: "
               + (detail_text.splitlines()[0] if detail_text else ""))
    out.append(f"GUI SMOKE geometry: {root.winfo_width()}x"
               f"{root.winfo_height()}+{root.winfo_x()}+{root.winfo_y()} "
               f"screen {root.winfo_screenwidth()}x"
               f"{root.winfo_screenheight()}")
    text = "\n".join(out)
    try:
        print(text, flush=True)
    except Exception:
        pass  # windowed frozen builds may have no stdout — tests use source
    root.destroy()
    return 0 if rows else 1
