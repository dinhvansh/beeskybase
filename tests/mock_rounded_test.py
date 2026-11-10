#!/usr/bin/env python3
"""v0.17 test — the rounded-corner overhaul (beesky/rounded.py).

Runs under xvfb-run (see run_mock_test_v17.sh). Asserts:

  * the radius tokens exist at the design values (cards 16,
    widgets 12, pills 999) in ui_theme AND as CSS custom
    properties in both web dashboards, with no pre-token literal
    border-radius left in either dashboard stylesheet;
  * RoundedButton: constructs in all three variants at >= 36px
    tall; a simulated click (press+release inside) fires the
    command; press-inside/release-outside cancels; Return and
    Space fire it once it holds keyboard focus (and a focus ring
    is drawn); a disabled button fires neither on click nor on
    invoke(); configure(state=/text=) and cget("state"/"text")
    behave like the ttk button it replaced;
  * RoundedEntry: the textvariable round-trips both ways,
    show="*" masks and configure(show="") unmasks (the agent
    window's "Hiện key" path), focus turns the canvas outline
    accent, and .entry is the hosted tk.Entry;
  * ui_theme.card() returns a ttk.Frame (RoundedCard) whose title
    is findable by widget-tree walk and whose canvas actually
    draws the rounded surface; RoundedPill recolours via
    ui_theme.set_pill with cget("bg") reporting the tone colour;
  * both real windows construct with the swapped widgets in place
    (scan_button / key_entry / autostart_button / view_log_button
    are the rounded classes).

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
from beesky.rounded import RoundedButton, RoundedCard, RoundedEntry, \
    RoundedPill  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label} {extra}")
        FAILURES.append(label)


def widget_texts(widget) -> list[str]:
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


def click(widget, root, release_at=None) -> None:
    root.update_idletasks()
    root.update()
    width, height = widget.winfo_width(), widget.winfo_height()
    widget.event_generate("<ButtonPress-1>", x=width // 2,
                          y=height // 2, when="now")
    rx, ry = release_at if release_at is not None \
        else (width // 2, height // 2)
    widget.event_generate("<ButtonRelease-1>", x=rx, y=ry, when="now")
    root.update()


def test_tokens_and_web() -> None:
    check("tokens: radius scale is 16 / 12 / 999",
          (ui_theme.RADIUS_CARD, ui_theme.RADIUS_WIDGET,
           ui_theme.RADIUS_PILL) == (16, 12, 999))
    for name in ("cloud/dashboard.html", "web/dashboard.html"):
        css = (ROOT / "beesky" / name).read_text(encoding="utf-8")
        check(f"web {name}: radius tokens are defined",
              "--radius-card: 16px" in css
              and "--radius-widget: 12px" in css
              and "--radius-pill: 999px" in css)
        leftovers = [v for v in ("border-radius: 4px",
                                 "border-radius: 8px",
                                 "border-radius: 9px",
                                 "border-radius: 10px",
                                 "border-radius: 12px")
                     if v in css]
        check(f"web {name}: no pre-token literal radii remain",
              not leftovers, str(leftovers))
        check(f"web {name}: token vars are actually used",
              css.count("var(--radius-card)") >= 3
              and css.count("var(--radius-widget)") >= 2
              and css.count("var(--radius-pill)") >= 2)


def test_button(root) -> None:
    fired: list[str] = []
    btn = RoundedButton(root, text="Quét ngay", variant="accent",
                        command=lambda: fired.append("scan"))
    btn.pack()
    root.update()
    check("button: accent constructs at >= 36px tall",
          btn.winfo_height() >= 36, str(btn.winfo_height()))
    check("button: cget reports text + state like ttk",
          btn.cget("text") == "Quét ngay"
          and btn.cget("state") == "normal")
    click(btn, root)
    check("button: press+release inside fires the command",
          fired == ["scan"], str(fired))
    click(btn, root, release_at=(-10, -10))
    check("button: release outside cancels the click",
          fired == ["scan"], str(fired))
    btn.focus_force()
    root.update()
    check("button: keyboard focus draws the focus ring",
          btn._focused and len(btn.find_all()) >= 3,
          f"focused={btn._focused} items={len(btn.find_all())}")
    btn.event_generate("<Return>", when="now")
    btn.event_generate("<space>", when="now")
    root.update()
    check("button: Return and Space activate a focused button",
          fired == ["scan", "scan", "scan"], str(fired))
    btn.invoke()
    check("button: invoke() fires while enabled",
          fired == ["scan"] * 4, str(fired))
    btn.configure(state="disabled")
    check("button: configure(state=) updates cget('state')",
          btn.cget("state") == "disabled")
    click(btn, root)
    btn.invoke()
    check("button: a disabled button never fires (click or invoke)",
          fired == ["scan"] * 4, str(fired))
    btn.set_state("normal")
    btn.set_text("Quét lại")
    root.update()
    check("button: set_text relabels and resizes",
          btn.cget("text") == "Quét lại")
    ghost = RoundedButton(root, text="Ghost", variant="ghost")
    danger = RoundedButton(root, text="Thu hồi",
                           variant="danger-ghost")
    ghost.pack()
    danger.pack()
    root.update()
    check("button: ghost + danger-ghost variants construct",
          ghost.winfo_height() >= 36
          and danger._colours()[2] == ui_theme.BAD)


def test_entry(root) -> None:
    var = tk.StringVar()
    entry = RoundedEntry(root, textvariable=var, show="*", width=12)
    entry.pack()
    root.update()
    check("entry: .entry hosts the real tk.Entry",
          isinstance(entry.entry, tk.Entry))
    entry.entry.insert(0, "s3cret")
    check("entry: typing flows into the textvariable",
          var.get() == "s3cret", var.get())
    var.set("from-var")
    check("entry: variable writes flow into the entry",
          entry.get() == "from-var", entry.get())
    check("entry: show='*' masks (cget delegates to the entry)",
          entry.cget("show") == "*")
    entry.configure(show="")
    check("entry: configure(show='') unmasks ('Hiện key' path)",
          entry.cget("show") == "")
    entry.entry.focus_force()
    root.update()
    check("entry: focus turns the frame outline accent",
          entry._focused
          and entry.itemcget(entry._shape, "outline")
          == ui_theme.ACCENT,
          entry.itemcget(entry._shape, "outline"))
    entry.entry.focus_displayof()  # keep linters quiet about focus use


def test_card_and_pill(root) -> None:
    card = ui_theme.card(root, title="Thẻ bo tròn", pad=12)
    card.pack(fill="x")
    ttk.Label(card, text="nội dung", style="Card.TLabel").pack()
    root.update()
    check("card: ui_theme.card returns a ttk.Frame (RoundedCard)",
          isinstance(card, RoundedCard)
          and isinstance(card, ttk.Frame))
    texts = widget_texts(root)
    check("card: title + content findable by tree walk",
          "Thẻ bo tròn" in texts and "nội dung" in texts,
          str(texts))
    check("card: the rounded surface is drawn on its canvas",
          len(card._canvas.find_all()) >= 1)
    pill = ui_theme.status_pill(root, text="Chưa chạy thử",
                                state="dim")
    pill.pack()
    root.update()
    check("pill: status_pill returns a RoundedPill",
          isinstance(pill, RoundedPill)
          and pill.cget("text") == "Chưa chạy thử")
    ui_theme.set_pill(pill, "ok", "Chạy thử: OK")
    check("pill: set_pill recolours + retexts (cget('bg') = OK)",
          str(pill.cget("bg")).casefold() == ui_theme.OK.casefold()
          and pill.cget("text") == "Chạy thử: OK")


def test_windows(tmp: Path) -> None:
    from beesky import agent_gui, gui

    root = tk.Tk()
    try:
        app = agent_gui.AgentConfigApp(
            root, config_path=tmp / "agent-config.json")
        check("windows: agent key_entry is a RoundedEntry",
              isinstance(app.key_entry, RoundedEntry))
        check("windows: agent buttons are RoundedButtons",
              isinstance(app.save_button, RoundedButton)
              and isinstance(app.test_button, RoundedButton)
              and isinstance(app.autostart_button, RoundedButton)
              and isinstance(app.view_log_button, RoundedButton))
        check("windows: agent pills are RoundedPills",
              isinstance(app.test_pill, RoundedPill)
              and isinstance(app.bg_pill, RoundedPill))
        root.update()
    finally:
        root.destroy()

    root = tk.Tk()
    try:
        app = gui.BeeSkyApp(root)
        check("windows: main scan_button is a RoundedButton",
              isinstance(app.scan_button, RoundedButton)
              and app.scan_button.cget("text") == "Quét ngay")
        root.update()
    finally:
        root.destroy()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-rounded-"))
    test_tokens_and_web()
    root = tk.Tk()
    try:
        ui_theme.setup_theme(root)
        test_button(root)
        test_entry(root)
        test_card_and_pill(root)
    finally:
        root.destroy()
    test_windows(tmp)
    print()
    if FAILURES:
        print(f"ROUNDED TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("ROUNDED TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
