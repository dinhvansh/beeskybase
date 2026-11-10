"""BeeSky desktop design system — one theme for both windows.

    from . import ui_theme
    ui_theme.setup_theme(root)

Shared by the main GUI (beesky/gui.py) and the agent config window
(beesky/agent_gui.py) so the two desktop apps look like one product
and match the cloud dashboard's palette (beesky/cloud/dashboard.html):
near-black layered panels, hairline borders, one yellow accent.

Stdlib only: tkinter/ttk on the "clam" theme, which is the one ttk
theme whose colours are fully scriptable. Everything visual lives
here — widget code should ask for a style name or a helper, never
hard-code a colour.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# -- palette (mirrors the cloud dashboard) --------------------------------

BG = "#0B0B0D"        # window background
PANEL = "#15151A"     # card background
PANEL2 = "#1C1C22"    # inset fields / hover surfaces
BORDER = "#26262E"    # hairline borders
TEXT = "#F2F2F3"      # primary text
MUTED = "#9CA3AF"     # secondary text
ACCENT = "#F5D800"    # BeeSky yellow
ACCENT_TEXT = "#141414"
OK = "#34D399"
WARN = "#FBBF24"
BAD = "#F87171"
SELECT_BG = "#3A3410"  # treeview selection (dark accent wash)

# -- type scale (points) ----------------------------------------------------

TITLE_SIZE = 19
SECTION_SIZE = 12
BODY_SIZE = 11
SMALL_SIZE = 10
STAT_SIZE = 24

_PREFERRED_FAMILIES = ("Segoe UI", "Helvetica Neue", "Noto Sans",
                       "DejaVu Sans")


def font_family(root: tk.Misc) -> str:
    """Best UI font family available on this machine.

    "Segoe UI" on Windows (the platform the frozen apps ship for);
    otherwise the family Tk itself picked for TkDefaultFont, so the
    windows still look native under xvfb/Linux dev runs.
    """
    cached = getattr(root, "_beesky_font_family", None)
    if cached:
        return cached
    try:
        available = {name.casefold(): name
                     for name in tkfont.families(root)}
    except tk.TclError:
        available = {}
    family = None
    for wanted in _PREFERRED_FAMILIES:
        if wanted.casefold() in available:
            family = available[wanted.casefold()]
            break
    if family is None:
        try:
            family = tkfont.nametofont("TkDefaultFont").actual("family")
        except tk.TclError:
            family = "TkDefaultFont"
    try:
        root._beesky_font_family = family  # type: ignore[attr-defined]
    except Exception:
        pass
    return family


def setup_theme(root: tk.Tk) -> str:
    """Apply the BeeSky design system to *root*; returns the font family.

    Call once per window, before building widgets. Safe to call on
    more than one root (styles live per-interpreter).
    """
    family = font_family(root)
    root.configure(bg=BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    body = (family, BODY_SIZE)
    body_bold = (family, BODY_SIZE, "bold")
    small = (family, SMALL_SIZE)

    # -- base ------------------------------------------------------------
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT, font=body)
    style.configure("Title.TLabel", background=BG, foreground=ACCENT,
                    font=(family, TITLE_SIZE, "bold"))
    style.configure("Sub.TLabel", background=BG, foreground=MUTED,
                    font=body)
    style.configure("Section.TLabel", background=BG, foreground=TEXT,
                    font=(family, SECTION_SIZE, "bold"))
    style.configure("Hint.TLabel", background=BG, foreground=MUTED,
                    font=small)
    style.configure("TSeparator", background=BORDER)

    # -- cards -------------------------------------------------------------
    style.configure("Card.TFrame", background=PANEL, borderwidth=1,
                    relief="solid", bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER)
    style.configure("Card.TLabel", background=PANEL, foreground=TEXT,
                    font=body)
    style.configure("Card.Section.TLabel", background=PANEL,
                    foreground=TEXT,
                    font=(family, SECTION_SIZE, "bold"))
    style.configure("Card.Sub.TLabel", background=PANEL,
                    foreground=MUTED, font=body)
    style.configure("Card.Hint.TLabel", background=PANEL,
                    foreground=MUTED, font=small)
    style.configure("StatTitle.TLabel", background=PANEL,
                    foreground=MUTED, font=(family, SMALL_SIZE, "bold"))
    style.configure("Stat.TLabel", background=PANEL, foreground=TEXT,
                    font=(family, STAT_SIZE, "bold"))

    # -- entries -----------------------------------------------------------
    style.configure("TEntry", fieldbackground=PANEL2, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER, insertcolor=TEXT,
                    padding=(10, 7), font=body)
    style.map("TEntry",
              bordercolor=[("focus", ACCENT)],
              lightcolor=[("focus", ACCENT)],
              darkcolor=[("focus", ACCENT)])

    # -- buttons -----------------------------------------------------------
    style.configure("Accent.TButton", background=ACCENT,
                    foreground=ACCENT_TEXT, font=body_bold,
                    padding=(16, 8), borderwidth=0, focuscolor=ACCENT)
    style.map("Accent.TButton",
              background=[("pressed", "#D9BE00"), ("active", "#FFE14D"),
                          ("disabled", "#57500F")],
              foreground=[("disabled", "#8A8A8A")])
    style.configure("Ghost.TButton", background=PANEL2, foreground=TEXT,
                    font=body, padding=(14, 8), bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER,
                    focuscolor=PANEL2)
    style.map("Ghost.TButton",
              background=[("pressed", PANEL), ("active", "#26262E"),
                          ("disabled", PANEL)],
              foreground=[("disabled", MUTED)],
              bordercolor=[("focus", ACCENT)],
              lightcolor=[("focus", ACCENT)],
              darkcolor=[("focus", ACCENT)])
    style.configure("Danger.TButton", background=PANEL2, foreground=BAD,
                    font=body, padding=(14, 8), bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER,
                    focuscolor=PANEL2)
    style.map("Danger.TButton",
              background=[("pressed", "#2A1515"), ("active", "#2A1A1A"),
                          ("disabled", PANEL)],
              foreground=[("disabled", MUTED)])

    # -- checkbuttons --------------------------------------------------------
    style.configure("TCheckbutton", background=BG, foreground=TEXT,
                    font=body, focuscolor=BG)
    style.configure("Card.TCheckbutton", background=PANEL,
                    foreground=TEXT, font=body, focuscolor=PANEL)

    # -- treeview ------------------------------------------------------------
    style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, rowheight=30, borderwidth=0,
                    relief="flat", font=body)
    style.configure("Treeview.Heading", background=PANEL2,
                    foreground=MUTED, borderwidth=0,
                    font=(family, SMALL_SIZE, "bold"), padding=(8, 6))
    style.map("Treeview.Heading", background=[("active", PANEL2)])
    style.map("Treeview", background=[("selected", SELECT_BG)],
              foreground=[("selected", ACCENT)])

    # -- scrollbar -----------------------------------------------------------
    style.configure("TScrollbar", background=PANEL2, troughcolor=BG,
                    bordercolor=BORDER, arrowcolor=MUTED, relief="flat")
    style.configure("Vertical.TScrollbar", background=PANEL2,
                    troughcolor=BG, bordercolor=BORDER,
                    arrowcolor=MUTED, relief="flat")

    return family


# -- layout helpers -----------------------------------------------------------


def center_window(win: tk.Tk, width: int | None = None,
                  height: int | None = None,
                  minsize: tuple[int, int] | None = None) -> None:
    """Centre *win* on screen, sized to content unless told otherwise.

    With no explicit size the window takes its requested (content)
    size and that becomes its minimum too — a form window should
    never be shrinkable below the content it was laid out for.
    """
    win.update_idletasks()
    w = width or win.winfo_reqwidth()
    h = height or win.winfo_reqheight()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = max(0, (screen_w - w) // 2)
    y = max(0, (screen_h - h) // 3)
    win.geometry(f"{w}x{h}+{x}+{y}")
    if minsize is not None:
        win.minsize(*minsize)
    elif width is None and height is None:
        win.minsize(w, h)


def card(parent: tk.Misc, title: str | None = None,
         pad: int = 16) -> ttk.Frame:
    """A panel card; the caller packs/grids it and fills it.

    With *title*, a section header is placed at the top inside the
    card and the caller packs its content below it.
    """
    frame = ttk.Frame(parent, style="Card.TFrame", padding=pad)
    if title is not None:
        ttk.Label(frame, text=title,
                  style="Card.Section.TLabel").pack(
                      anchor="w", pady=(0, 10))
    return frame


def labeled_field(parent: tk.Misc, row: int, label: str,
                  entry_widget: tk.Widget,
                  hint: str | None = None) -> None:
    """Grid a modern form field inside *parent*: label above, field
    below, optional hint under the field.

    *entry_widget* must already have been created with *parent* as
    its master (a container frame works too — e.g. an entry plus a
    toggle packed inside it). Logical rows are tripled internally
    (label / field / hint), and the field spans every column, so the
    caller should let column 0 of *parent* carry the weight.
    """
    base = row * 3
    ttk.Label(parent, text=label, style="Card.Hint.TLabel").grid(
        row=base, column=0, columnspan=99, sticky="w", pady=(8, 4))
    entry_widget.grid(row=base + 1, column=0, columnspan=99,
                      sticky="ew")
    if hint is not None:
        ttk.Label(parent, text=hint, style="Card.Hint.TLabel",
                  wraplength=560, justify="left").grid(
                      row=base + 2, column=0, columnspan=99,
                      sticky="w", pady=(4, 0))


# -- status pill ----------------------------------------------------------------

_PILL_COLORS = {
    "ok": (OK, ACCENT_TEXT),
    "warn": (WARN, ACCENT_TEXT),
    "bad": (BAD, ACCENT_TEXT),
    "dim": (PANEL2, MUTED),
}


def status_pill(parent: tk.Misc, text: str = "",
                state: str = "dim") -> tk.Label:
    """A small solid status chip (tk.Label — ttk has no solid-fill
    label that recolours per state without a new style each)."""
    bg, fg = _PILL_COLORS.get(state, _PILL_COLORS["dim"])
    family = font_family(parent)
    return tk.Label(parent, text=text, bg=bg, fg=fg,
                    font=(family, SMALL_SIZE, "bold"),
                    padx=10, pady=3)


def set_pill(pill: tk.Label, state: str, text: str | None = None) -> None:
    """Recolour (and optionally retext) a pill from status_pill()."""
    bg, fg = _PILL_COLORS.get(state, _PILL_COLORS["dim"])
    pill.configure(bg=bg, fg=fg)
    if text is not None:
        pill.configure(text=text)
