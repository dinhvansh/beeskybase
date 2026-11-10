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

# -- Liquid Glass, simulated (v0.18) ---------------------------------------
# The web dashboards do REAL glass (translucent white + backdrop
# blur). Tk has no backdrop blur, so the desktop simulates the
# material: a lighter glass tint for card surfaces, brighter
# outlines, and a 1px rim light along the top edge drawn by
# beesky/rounded.py. PANEL/PANEL2/BORDER above remain the solid
# fallback tokens for ttk styles (the Treeview moved to its own
# darker well tokens in v0.19). See docs/design-tokens.md
# ("Liquid Glass").

PANEL_GLASS = "#191920"   # card fill — simulated glass tint
GLASS_BORDER = "#34343E"  # outline for cards + ghost buttons
RIM_LIGHT = "#3D3D4A"     # 1px top rim light (cards, ghost buttons)
GHOST_FILL = "#22222B"    # ghost button glass fill
ENTRY_FILL = "#1E1E26"    # entry glass fill
ENTRY_BORDER = "#30303C"  # entry outline (focus still turns ACCENT)

# -- miners table well (v0.19) ----------------------------------------------
# The main window's results table sits in a dark inset well inside
# its glass card: a fill darker than the glass, its own heading
# strip, and a zebra parity wash for odd rows. The Treeview and
# scrollbar styles below are built on these tokens so no light
# clam default can leak back in around the table.

TABLE_WELL = "#121216"     # table well fill (darker than PANEL_GLASS)
TABLE_HEADING = "#1D1D24"  # treeview heading strip
TABLE_ZEBRA = "#17171D"    # odd-row parity wash (plain OK rows only)

# -- type scale (points) ----------------------------------------------------

TITLE_SIZE = 19
SECTION_SIZE = 12
BODY_SIZE = 11
SMALL_SIZE = 10
STAT_SIZE = 24

# -- radius scale (v0.17, see docs/design-tokens.md) --------------------------
# One radius system for desktop + web: cards/panels round at 16,
# interactive widgets (buttons, inputs) at 12, chips/pills fully
# round. ttk cannot draw these — beesky/rounded.py renders them on
# tk.Canvas; the web dashboards use the same values as CSS tokens
# (--radius-card / --radius-widget / --radius-pill).

RADIUS_CARD = 16
RADIUS_WIDGET = 12
RADIUS_PILL = 999

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
    # Card-hosted content sits on the RoundedCard's simulated-glass
    # fill, so these backgrounds are PANEL_GLASS (v0.18), matching
    # the canvas-drawn surface pixel-for-pixel at the label edges.
    style.configure("Card.TFrame", background=PANEL_GLASS, borderwidth=1,
                    relief="solid", bordercolor=GLASS_BORDER,
                    lightcolor=GLASS_BORDER, darkcolor=GLASS_BORDER)
    style.configure("Card.TLabel", background=PANEL_GLASS,
                    foreground=TEXT, font=body)
    style.configure("Card.Section.TLabel", background=PANEL_GLASS,
                    foreground=TEXT,
                    font=(family, SECTION_SIZE, "bold"))
    style.configure("Card.Sub.TLabel", background=PANEL_GLASS,
                    foreground=MUTED, font=body)
    style.configure("Card.Hint.TLabel", background=PANEL_GLASS,
                    foreground=MUTED, font=small)
    style.configure("StatTitle.TLabel", background=PANEL_GLASS,
                    foreground=MUTED, font=(family, SMALL_SIZE, "bold"))
    style.configure("Stat.TLabel", background=PANEL_GLASS,
                    foreground=TEXT,
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
    style.configure("Card.TCheckbutton", background=PANEL_GLASS,
                    foreground=TEXT, font=body, focuscolor=PANEL_GLASS)

    # -- treeview ------------------------------------------------------------
    # v0.19: the tree lives in the dark inset well (TABLE_WELL).
    # bordercolor / lightcolor / darkcolor are pinned to the well
    # colour — clam falls back to a LIGHT default border when they
    # are left unset, which is exactly where the pre-v0.19 white
    # frame around the table came from. The heading pins its
    # border colours to its own background so the separator line
    # under the headings vanishes too.
    style.configure("Treeview", background=TABLE_WELL,
                    fieldbackground=TABLE_WELL,
                    foreground=TEXT, rowheight=30, borderwidth=0,
                    relief="flat", bordercolor=TABLE_WELL,
                    lightcolor=TABLE_WELL, darkcolor=TABLE_WELL,
                    font=body)
    style.configure("Treeview.Heading", background=TABLE_HEADING,
                    foreground=MUTED, borderwidth=0,
                    bordercolor=TABLE_HEADING,
                    lightcolor=TABLE_HEADING,
                    darkcolor=TABLE_HEADING,
                    font=(family, SMALL_SIZE, "bold"), padding=(8, 6))
    style.map("Treeview.Heading",
              background=[("active", TABLE_HEADING)])
    style.map("Treeview", background=[("selected", SELECT_BG)],
              foreground=[("selected", ACCENT)])

    # -- scrollbar -----------------------------------------------------------
    # v0.19: dark to match the table well — BORDER thumb riding in
    # a TABLE_WELL trough, no light strip beside the rows.
    style.configure("TScrollbar", background=BORDER,
                    troughcolor=TABLE_WELL, bordercolor=TABLE_WELL,
                    arrowcolor=MUTED, relief="flat")
    style.configure("Vertical.TScrollbar", background=BORDER,
                    troughcolor=TABLE_WELL, bordercolor=TABLE_WELL,
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
    """A rounded panel card (radius RADIUS_CARD); the caller
    packs/grids it and fills it.

    With *title*, a section header is placed at the top inside the
    card and the caller packs its content below it. The return
    value is a beesky.rounded.RoundedCard — a ttk.Frame subclass,
    so every pre-v0.17 call site works unchanged.
    """
    from . import rounded  # deferred: rounded imports this module
    return rounded.RoundedCard(parent, title=title, pad=pad)


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
                state: str = "dim", backdrop: str | None = None):
    """A small solid status chip — since v0.17 a full-round
    beesky.rounded.RoundedPill instead of the square tk.Label.

    *backdrop* is the surface the pill sits on (window BG by
    default, PANEL inside a card) so its canvas corners blend in.
    """
    from . import rounded  # deferred: rounded imports this module
    return rounded.RoundedPill(parent, text=text, tone=state,
                               backdrop=backdrop)


def set_pill(pill, state: str, text: str | None = None) -> None:
    """Recolour (and optionally retext) a pill from status_pill()."""
    if hasattr(pill, "set_tone"):  # RoundedPill
        pill.set_tone(state, text)
        return
    bg, fg = _PILL_COLORS.get(state, _PILL_COLORS["dim"])
    pill.configure(bg=bg, fg=fg)
    if text is not None:
        pill.configure(text=text)
