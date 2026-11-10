#!/usr/bin/env python3
"""v0.15 test — the shared desktop design system (beesky/ui_theme.py).

Runs under xvfb-run (see run_mock_test_v15.sh). Asserts:

  * ui_theme.setup_theme actually applies the cloud-dashboard
    palette to the ttk styles both windows are built from (TEntry
    field background, accent button, treeview, card frame, root
    background, focus border mapping);
  * the agent config window constructs on the theme with its two
    cards ("Kết nối cloud", "Quét tại trại") and the status pill in
    its default "Chưa chạy thử" state;
  * the main window constructs on the theme with the toolbar card
    ("Mục tiêu quét"), the four stat cards, the detail card
    ("Chi tiết máy đã chọn"), and that show_records() drives the
    stat cards (totals, hashrate sum, problem count + colour,
    max temperature).

Prints PASS lines; exit 1 on failure.
"""

import sys
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import ttk

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from beesky import ui_theme  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label} {extra}")
        FAILURES.append(label)


def widget_texts(widget) -> list[str]:
    """Every static text in the widget tree (labels, buttons…)."""
    texts: list[str] = []
    stack = [widget]
    while stack:
        current = stack.pop()
        try:
            text = current.cget("text")
        except tk.TclError:
            text = ""
        if text:
            texts.append(str(text))
        stack.extend(current.winfo_children())
    return texts


def test_theme_applies() -> None:
    root = tk.Tk()
    try:
        family = ui_theme.setup_theme(root)
        check("theme: a font family is chosen", bool(family), family)
        style = ttk.Style(root)
        check("theme: root background is the dashboard bg",
              str(root.cget("bg")).casefold()
              == ui_theme.BG.casefold(),
              str(root.cget("bg")))
        check("theme: TEntry fieldbackground is panel2",
              style.lookup("TEntry", "fieldbackground")
              == ui_theme.PANEL2,
              style.lookup("TEntry", "fieldbackground"))
        check("theme: TEntry padding is (10, 7)",
              style.lookup("TEntry", "padding") == "10 7",
              style.lookup("TEntry", "padding"))
        check("theme: Accent.TButton background is the BeeSky yellow",
              style.lookup("Accent.TButton", "background")
              == ui_theme.ACCENT)
        check("theme: Ghost.TButton background is panel2",
              style.lookup("Ghost.TButton", "background")
              == ui_theme.PANEL2)
        check("theme: Treeview background is the card panel",
              style.lookup("Treeview", "background") == ui_theme.PANEL)
        check("theme: Treeview rowheight is 30",
              str(style.lookup("Treeview", "rowheight")) == "30",
              style.lookup("Treeview", "rowheight"))
        check("theme: Card.TFrame background is the glass panel (v0.18)",
              style.lookup("Card.TFrame", "background")
              == ui_theme.PANEL_GLASS)
        check("theme: palette constants match the spec hex values",
              (ui_theme.BG, ui_theme.PANEL, ui_theme.PANEL2,
               ui_theme.BORDER, ui_theme.TEXT, ui_theme.MUTED,
               ui_theme.ACCENT)
              == ("#0B0B0D", "#15151A", "#1C1C22", "#26262E",
                  "#F2F2F3", "#9CA3AF", "#F5D800"))
        check("theme: glass tokens match the v0.18 spec hex values",
              (ui_theme.PANEL_GLASS, ui_theme.GLASS_BORDER,
               ui_theme.RIM_LIGHT, ui_theme.GHOST_FILL,
               ui_theme.ENTRY_FILL, ui_theme.ENTRY_BORDER)
              == ("#191920", "#34343E", "#3D3D4A",
                  "#22222B", "#1E1E26", "#30303C"))
    finally:
        root.destroy()


def test_agent_window(tmp: Path) -> None:
    from beesky import agent_gui

    root = tk.Tk()
    try:
        app = agent_gui.AgentConfigApp(
            root, config_path=tmp / "agent-config.json")
        texts = widget_texts(root)
        check("agent gui: 'Kết nối cloud' card is present",
              "Kết nối cloud" in texts, str(texts))
        check("agent gui: 'Quét tại trại' card is present",
              "Quét tại trại" in texts)
        check("agent gui: the three action buttons keep their labels",
              all(label in texts for label in
                  ("Lưu cấu hình", "Chạy thử", "Bật tự khởi động")),
              str(texts))
        check("agent gui: status pill starts at 'Chưa chạy thử'",
              str(app.test_pill.cget("text")) == "Chưa chạy thử")
        ui_theme.set_pill(app.test_pill, "ok", "Chạy thử: OK")
        check("agent gui: pill recolours to the ok colour",
              str(app.test_pill.cget("bg")).casefold()
              == ui_theme.OK.casefold())
        root.update_idletasks()
    finally:
        root.destroy()


def test_main_window() -> None:
    from beesky import gui

    root = tk.Tk()
    try:
        app = gui.BeeSkyApp(root)
        texts = widget_texts(root)
        for title in ("Mục tiêu quét", "Tổng số máy", "Tổng hashrate",
                      "Máy có vấn đề", "Nhiệt độ cao nhất",
                      "Chi tiết máy đã chọn"):
            check(f"main gui: {title!r} is present", title in texts,
                  str(texts))
        check("main gui: toolbar buttons keep their labels",
              all(label in texts for label in
                  ("Quét ngay", "Xuất phiếu sửa", "Mở web tại chỗ")),
              str(texts))

        record = {
            "ip": "10.0.0.9", "model": "Antminer S19 Pro",
            "source": "vnish", "ths": 100.5, "chips_alive": 340,
            "chips_total": 342, "max_temp_c": 87.0,
            "fans_rpm": [4000], "status": "CHECK",
            "problems": [{"code": "OVER_TEMP", "detail": "hot"}],
            "chains": [],
        }
        app.show_records([record])
        check("main gui: stat cards follow a scan (1 máy, 100.50 TH/s)",
              app.stat_total_var.get() == "1"
              and app.stat_ths_var.get() == "100.50",
              f"{app.stat_total_var.get()} / {app.stat_ths_var.get()}")
        check("main gui: problem stat counts and turns red",
              app.stat_problem_var.get() == "1"
              and str(app._problem_value_label.cget("fg")).casefold()
              == ui_theme.BAD.casefold())
        check("main gui: max-temp stat shows the hottest miner",
              app.stat_temp_var.get() == "87 °C",
              app.stat_temp_var.get())
        root.update_idletasks()
    finally:
        root.destroy()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-theme-"))
    test_theme_applies()
    test_agent_window(tmp)
    test_main_window()
    print()
    if FAILURES:
        print(f"THEME TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("THEME TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
