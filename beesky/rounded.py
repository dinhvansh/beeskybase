"""Rounded-corner widgets for the BeeSky desktop apps (v0.17).

ttk has no border-radius, so the design system's rounded surfaces
(radius tokens in beesky/ui_theme.py: cards 16, widgets 12, pills
fully round — see docs/design-tokens.md) are drawn on tk.Canvas
(stdlib only). Since v0.18 the cards / ghost buttons / entries
also carry the SIMULATED Liquid Glass material (Tk cannot blur
what is behind a window): the ui_theme glass tints plus a 1px
rim light along the top edge — the web dashboards do the real
backdrop-filter version of the same material.

  * RoundedCard   — a ttk.Frame whose surface is a canvas-drawn
    rounded rect; callers pack/grid it and fill it exactly like the
    square card it replaces.
  * RoundedButton — canvas button with hover / pressed / focus-ring
    feedback and ttk-compatible configure()/cget()/invoke().
  * RoundedEntry  — a flat tk.Entry hosted in a rounded canvas
    frame; the outline turns accent while the entry has focus.
  * RoundedPill   — a full-round status chip (replaces the square
    tk.Label pill ui_theme used before v0.17).

Colours come from beesky/ui_theme.py — never hard-code a hex here
that the theme does not own. The canvas behind every widget must
match the surface it sits on (the ``backdrop`` parameter): cards
and the agent action row sit on the window background, fields and
buttons inside a card sit on the card panel colour.
"""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from . import ui_theme

# Hover / pressed shades — the same values the pre-v0.17 ttk style
# maps used (ui_theme.setup_theme's Accent/Ghost/Danger maps), so
# the rounded buttons feel identical to the square ones they
# replace, just rounder.
_ACCENT_HOVER = "#FFE14D"
_ACCENT_PRESSED = "#D9BE00"
_ACCENT_DISABLED_BG = "#57500F"
_ACCENT_DISABLED_FG = "#8A8A8A"
_GHOST_HOVER = "#2B2B36"  # v0.18: perceptible step up from GHOST_FILL
_DANGER_HOVER = "#2A1A1A"
_DANGER_PRESSED = "#2A1515"


def rounded_rect_points(x1: float, y1: float, x2: float, y2: float,
                        radius: float, segments: int = 6) -> list[float]:
    """Polygon points tracing a rounded rectangle.

    Each corner arc is sampled with *segments* steps — at the
    design radii (12–16 px, and half-height for pills) six steps
    per corner reads as a smooth curve without spline surprises.
    """
    r = max(0.0, min(radius, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    points: list[float] = []
    corners = (
        (x2 - r, y1 + r, -90.0),   # top-right, arc -90..0
        (x2 - r, y2 - r, 0.0),     # bottom-right, arc 0..90
        (x1 + r, y2 - r, 90.0),    # bottom-left, arc 90..180
        (x1 + r, y1 + r, 180.0),   # top-left, arc 180..270
    )
    for cx, cy, start in corners:
        for i in range(segments + 1):
            angle = math.radians(start + 90.0 * i / segments)
            points.append(cx + r * math.cos(angle))
            points.append(cy + r * math.sin(angle))
    return points


def _draw_rounded(canvas: tk.Canvas, x1: float, y1: float,
                  x2: float, y2: float, radius: float,
                  **options) -> int:
    """One rounded-rect polygon item, inset 1px so a 1px outline
    sits fully inside the canvas instead of clipping at its edge."""
    return canvas.create_polygon(
        rounded_rect_points(x1 + 1, y1 + 1, x2 - 1, y2 - 1, radius),
        **options)


def top_rim_points(x1: float, y1: float, x2: float,
                   radius: float, segments: int = 6) -> list[float]:
    """Polyline points along the TOP edge of a rounded rect whose
    outline spans (x1, y1)-(x2, ·) with corner *radius*: the
    top-left arc, the top straight segment, the top-right arc.

    Drawn 1px inside a surface's outline (callers pass the
    surface rect inset by 1 with radius-1) it reads as the rim
    light on a glass edge — Liquid Glass's signature highlight,
    simulated (v0.18)."""
    r = max(0.0, min(radius, (x2 - x1) / 2.0))
    points: list[float] = []

    def arc(cx: float, start: float) -> None:
        for i in range(segments + 1):
            angle = math.radians(start + 90.0 * i / segments)
            points.append(cx + r * math.cos(angle))
            points.append(y1 + r + r * math.sin(angle))

    arc(x1 + r, 180.0)          # top-left arc, ends at (x1+r, y1)
    points.extend((x2 - r, y1))  # straight run to the right arc
    arc(x2 - r, 270.0)          # top-right arc
    return points


def _font(widget: tk.Misc, size: int, bold: bool = False) -> tkfont.Font:
    family = ui_theme.font_family(widget.winfo_toplevel())
    return tkfont.Font(family=family, size=size,
                       weight="bold" if bold else "normal")


# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------

class RoundedCard(ttk.Frame):
    """A panel card with rounded corners (radius 16).

    Drop-in for the pre-v0.17 square card: it IS a ttk.Frame (on
    the plain background style, so the frame's own corners show
    the backdrop), the caller packs/grids it and packs children
    into it with the card padding applied, exactly as before. A
    canvas placed to fill the frame draws the rounded panel
    surface underneath the children; children sit inset by the
    padding (>= 12px > the corner arc depth), and their panel
    backgrounds match the drawn fill, so the composite reads as
    one rounded card.
    """

    def __init__(self, parent: tk.Misc, title: str | None = None,
                 pad: int = 16, radius: int | None = None,
                 backdrop: str | None = None,
                 fill: str | None = None,
                 outline: str | None = None):
        super().__init__(parent, style="TFrame", padding=pad)
        self._radius = ui_theme.RADIUS_CARD if radius is None else radius
        self._fill = (ui_theme.PANEL_GLASS if fill is None else fill)
        self._outline = (ui_theme.GLASS_BORDER if outline is None
                         else outline)
        self._canvas = tk.Canvas(
            self, bg=backdrop or ui_theme.BG, highlightthickness=0,
            bd=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # Stacking follows creation order: the canvas is created
        # first, so the title and all caller children land above it.
        self._canvas.bind("<Configure>", self._redraw)
        if title is not None:
            ttk.Label(self, text=title,
                      style="Card.Section.TLabel").pack(
                          anchor="w", pady=(0, 10))

    def _redraw(self, _event=None) -> None:
        width = self._canvas.winfo_width()
        height = self._canvas.winfo_height()
        if width <= 2 or height <= 2:
            return
        # One delete by the shared "surface" tag clears the fill
        # AND the rim (tagged with both), so a resize never
        # double-draws either.
        self._canvas.delete("surface")
        self._canvas.create_polygon(
            rounded_rect_points(1, 1, width - 1, height - 1,
                                self._radius),
            fill=self._fill, outline=self._outline, width=1,
            tags=("surface",))
        # Rim light (v0.18 simulated glass): a 1px brighter line
        # along the top inner edge — the inset-by-1 top arc +
        # straight of the surface outline.
        self._canvas.create_line(
            top_rim_points(2, 2, width - 2,
                           max(2, self._radius - 1)),
            fill=ui_theme.RIM_LIGHT, width=1,
            tags=("surface", "rim"))
        # Lowering by the shared tag keeps the rim (created last)
        # above the fill while both stay under the card's children.
        self._canvas.tag_lower("surface")


# ---------------------------------------------------------------------------
# Button
# ---------------------------------------------------------------------------

class RoundedButton(tk.Canvas):
    """A rounded canvas button (radius 12, height >= 36).

    ttk-flavoured API: ``configure(state=...)`` /
    ``configure(text=...)`` / ``set_state()`` / ``set_text()`` /
    ``cget("state")`` / ``cget("text")`` / ``invoke()`` — the call
    sites and tests written against ttk.Button keep working.
    Feedback (per docs/design-tokens.md): hover lightens, press
    darkens, release outside the button cancels, keyboard focus
    draws an accent outline ring, Return/Space activates.
    """

    _VARIANTS = ("accent", "ghost", "danger-ghost")

    def __init__(self, parent: tk.Misc, text: str = "",
                 command=None, variant: str = "ghost",
                 radius: int | None = None, padx: int = 16,
                 state: str = "normal", bold: bool | None = None,
                 backdrop: str | None = None, **canvas_options):
        if variant not in self._VARIANTS:
            raise ValueError(f"unknown button variant: {variant!r}")
        self._text = text
        self._command = command
        self._variant = variant
        self._radius = (ui_theme.RADIUS_WIDGET if radius is None
                        else radius)
        self._padx = padx
        self._state = "disabled" if state == "disabled" else "normal"
        self._bold = (variant == "accent") if bold is None else bold
        self._hover = False
        self._pressed = False
        self._focused = False
        self._font_obj = _font(parent, ui_theme.BODY_SIZE, self._bold)
        height = max(36, self._font_obj.metrics("linespace") + 18)
        width = self._font_obj.measure(text) + 2 * padx
        canvas_options.setdefault("highlightthickness", 0)
        canvas_options.setdefault("bd", 0)
        canvas_options.setdefault("takefocus", 1)
        super().__init__(parent, width=width, height=height,
                         bg=backdrop or ui_theme.BG, **canvas_options)
        self._sync_cursor()
        self.bind("<Configure>", lambda _e: self._redraw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<KeyPress-Return>", self._on_key)
        self.bind("<KeyPress-space>", self._on_key)
        self._redraw()

    # -- colours -----------------------------------------------------

    def _colours(self) -> tuple[str, str, str]:
        """(fill, outline, text colour) for the current state."""
        if self._variant == "accent":
            if self._state == "disabled":
                return (_ACCENT_DISABLED_BG, _ACCENT_DISABLED_BG,
                        _ACCENT_DISABLED_FG)
            fill = ui_theme.ACCENT
            if self._pressed:
                fill = _ACCENT_PRESSED
            elif self._hover:
                fill = _ACCENT_HOVER
            return (fill, fill, ui_theme.ACCENT_TEXT)
        if self._variant == "danger-ghost":
            if self._state == "disabled":
                return (ui_theme.PANEL, ui_theme.BORDER, ui_theme.MUTED)
            fill = ui_theme.PANEL2
            if self._pressed:
                fill = _DANGER_PRESSED
            elif self._hover:
                fill = _DANGER_HOVER
            return (fill, ui_theme.BORDER, ui_theme.BAD)
        # ghost — simulated glass since v0.18 (GHOST_FILL +
        # GLASS_BORDER + the rim light drawn in _redraw)
        if self._state == "disabled":
            return (ui_theme.PANEL_GLASS, ui_theme.GLASS_BORDER,
                    ui_theme.MUTED)
        fill = ui_theme.GHOST_FILL
        if self._pressed:
            fill = ui_theme.PANEL
        elif self._hover:
            fill = _GHOST_HOVER
        return (fill, ui_theme.GLASS_BORDER, ui_theme.TEXT)

    def _ring_colour(self) -> str:
        return (ui_theme.ACCENT_TEXT if self._variant == "accent"
                else ui_theme.ACCENT)

    # -- drawing -------------------------------------------------------

    def _redraw(self) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 2 or height <= 2:
            return
        fill, outline, fg = self._colours()
        self.delete("all")
        _draw_rounded(self, 0, 0, width, height, self._radius,
                      fill=fill, outline=outline, width=1)
        if self._variant == "ghost" and self._state == "normal":
            # Rim light (v0.18 simulated glass) — _redraw rebuilds
            # from delete("all"), so resizes never double-draw it.
            self.create_line(
                top_rim_points(2, 2, width - 2,
                               max(2, self._radius - 1)),
                fill=ui_theme.RIM_LIGHT, width=1, tags=("rim",))
        if self._focused and self._state == "normal":
            self.create_polygon(
                rounded_rect_points(3, 3, width - 3, height - 3,
                                    max(2, self._radius - 3)),
                fill="", outline=self._ring_colour(), width=2)
        self.create_text(width / 2, height / 2, text=self._text,
                         fill=fg, font=self._font_obj)

    # -- events --------------------------------------------------------

    def _inside(self, event) -> bool:
        return (0 <= event.x <= self.winfo_width()
                and 0 <= event.y <= self.winfo_height())

    def _on_enter(self, _event) -> None:
        if self._state == "normal":
            self._hover = True
            self._redraw()

    def _on_leave(self, _event) -> None:
        self._hover = False
        self._pressed = False
        self._redraw()

    def _on_press(self, _event) -> None:
        if self._state != "normal":
            return
        self.focus_set()
        self._pressed = True
        self._redraw()

    def _on_release(self, event) -> None:
        was_pressed = self._pressed
        self._pressed = False
        self._redraw()
        if was_pressed and self._inside(event):
            self.invoke()

    def _on_focus_in(self, _event) -> None:
        self._focused = True
        self._redraw()

    def _on_focus_out(self, _event) -> None:
        self._focused = False
        self._pressed = False
        self._redraw()

    def _on_key(self, _event) -> None:
        self.invoke()

    # -- ttk-compatible API ----------------------------------------------

    def _sync_cursor(self) -> None:
        super().configure(
            cursor="hand2" if self._state == "normal" else "")

    def invoke(self) -> None:
        """Fire the command (a disabled button does nothing, as ttk)."""
        if self._state == "normal" and self._command is not None:
            self._command()

    def set_state(self, state: str) -> None:
        self._state = "disabled" if state == "disabled" else "normal"
        if self._state == "disabled":
            self._pressed = False
            self._hover = False
        self._sync_cursor()
        self._redraw()

    def set_text(self, text: str) -> None:
        self._text = text
        width = self._font_obj.measure(text) + 2 * self._padx
        super().configure(width=width)
        self._redraw()

    def configure(self, cnf=None, **kw):  # type: ignore[override]
        if isinstance(cnf, dict):
            kw.update(cnf)
        if "text" in kw:
            self.set_text(kw.pop("text"))
        if "state" in kw:
            self.set_state(kw.pop("state"))
        if "command" in kw:
            self._command = kw.pop("command")
        if kw:
            return super().configure(**kw)
        return None

    config = configure

    def cget(self, key):  # type: ignore[override]
        if key == "text":
            return self._text
        if key == "state":
            return self._state
        if key == "command":
            return self._command
        return super().cget(key)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

class RoundedEntry(tk.Canvas):
    """A flat text entry in a rounded frame (radius 12).

    The real editor is a borderless tk.Entry hosted via
    create_window (exposed as ``.entry``); the canvas draws the
    ENTRY_FILL glass fill + hairline, which turns ACCENT while
    the entry has keyboard focus. Constructor options mirror the ttk.Entry
    usage in the two GUIs (textvariable / width in characters /
    show); configure()/cget() delegate the entry options, so
    existing call sites (``key_entry.configure(show=...)``,
    ``key_entry.cget("show")``) keep working.
    """

    _ENTRY_OPTIONS = ("show", "textvariable", "state", "font",
                      "justify", "insertbackground", "exportselection")

    def __init__(self, parent: tk.Misc, textvariable=None,
                 width: int | None = None, show: str | None = None,
                 state: str = "normal",
                 radius: int | None = None,
                 backdrop: str | None = None, **canvas_options):
        self._radius = (ui_theme.RADIUS_WIDGET if radius is None
                        else radius)
        self._focused = False
        self._chars = width
        font_obj = _font(parent, ui_theme.BODY_SIZE)
        self._font_obj = font_obj
        char_px = max(1, font_obj.measure("0"))
        px_width = int((width or 20) * char_px) + 22
        height = font_obj.metrics("linespace") + 16
        canvas_options.setdefault("highlightthickness", 0)
        canvas_options.setdefault("bd", 0)
        super().__init__(parent, width=px_width, height=height,
                         bg=backdrop or ui_theme.BG, **canvas_options)
        entry_options: dict = {
            "bg": ui_theme.ENTRY_FILL, "fg": ui_theme.TEXT,
            "insertbackground": ui_theme.TEXT,
            "selectbackground": ui_theme.SELECT_BG,
            "selectforeground": ui_theme.TEXT,
            "disabledbackground": ui_theme.ENTRY_FILL,
            "disabledforeground": ui_theme.MUTED,
            "relief": "flat", "bd": 0, "highlightthickness": 0,
            "font": font_obj,
        }
        if textvariable is not None:
            entry_options["textvariable"] = textvariable
        if show is not None:
            entry_options["show"] = show
        if state == "disabled":
            entry_options["state"] = "disabled"
        self.entry = tk.Entry(self, **entry_options)
        self._window = self.create_window(
            11, height // 2, anchor="w", window=self.entry,
            width=max(10, px_width - 22),
            height=font_obj.metrics("linespace") + 4)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Button-1>", lambda _e: self.entry.focus_set())
        self.bind("<Configure>", self._on_resize)
        self._shape: int | None = None
        self._redraw()

    # -- drawing -----------------------------------------------------

    def _redraw(self) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 2 or height <= 2:
            return
        if self._shape is not None:
            self.delete(self._shape)
        outline = (ui_theme.ACCENT if self._focused
                   else ui_theme.ENTRY_BORDER)
        self._shape = _draw_rounded(
            self, 0, 0, width, height, self._radius,
            fill=ui_theme.ENTRY_FILL, outline=outline, width=1)
        self.tag_lower(self._shape)

    def _on_resize(self, _event=None) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width > 22 and height > 2:
            self.coords(self._window, 11, height // 2)
            self.itemconfigure(
                self._window, width=width - 22,
                height=self._font_obj.metrics("linespace") + 4)
        self._redraw()

    def _on_focus_in(self, _event) -> None:
        self._focused = True
        self._redraw()

    def _on_focus_out(self, _event) -> None:
        self._focused = False
        self._redraw()

    # -- entry API ------------------------------------------------------

    def get(self) -> str:
        return self.entry.get()

    def focus_set(self) -> None:  # typing in the field, not the frame
        self.entry.focus_set()

    def configure(self, cnf=None, **kw):  # type: ignore[override]
        if isinstance(cnf, dict):
            kw.update(cnf)
        entry_kw = {k: kw.pop(k) for k in list(kw)
                    if k in self._ENTRY_OPTIONS}
        if entry_kw:
            self.entry.configure(**entry_kw)
        if kw:
            return super().configure(**kw)
        return None

    config = configure

    def cget(self, key):  # type: ignore[override]
        if key in self._ENTRY_OPTIONS:
            return self.entry.cget(key)
        return super().cget(key)


# ---------------------------------------------------------------------------
# Pill
# ---------------------------------------------------------------------------

class RoundedPill(tk.Canvas):
    """A full-round status chip (radius = half its height).

    API: ``set(text, tone)`` / ``set_tone(tone, text=None)``;
    ``cget("text")`` / ``cget("bg")`` / ``cget("fg")`` report the
    current content the way the pre-v0.17 tk.Label pill did, so
    ui_theme.set_pill() and the GUI tests keep working.
    Tones: ok / warn / bad / dim.
    """

    def __init__(self, parent: tk.Misc, text: str = "",
                 tone: str | None = None, state: str | None = None,
                 backdrop: str | None = None, **canvas_options):
        self._text = text
        self._tone = state or tone or "dim"
        self._font_obj = _font(parent, ui_theme.SMALL_SIZE, bold=True)
        height = self._font_obj.metrics("linespace") + 9
        self._height = height
        width = self._font_obj.measure(text) + 22
        canvas_options.setdefault("highlightthickness", 0)
        canvas_options.setdefault("bd", 0)
        super().__init__(parent, width=width, height=height,
                         bg=backdrop or ui_theme.BG, **canvas_options)
        self.bind("<Configure>", lambda _e: self._redraw())
        self._redraw()

    def _colours(self) -> tuple[str, str]:
        return ui_theme._PILL_COLORS.get(
            self._tone, ui_theme._PILL_COLORS["dim"])

    def _redraw(self) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 2 or height <= 2:
            return
        bg, fg = self._colours()
        self.delete("all")
        _draw_rounded(self, 0, 0, width, height, height / 2,
                      fill=bg, outline=bg, width=1)
        self.create_text(width / 2, height / 2, text=self._text,
                         fill=fg, font=self._font_obj)

    def set(self, text: str | None = None,
            tone: str | None = None) -> None:
        if text is not None:
            self._text = text
            super().configure(
                width=self._font_obj.measure(text) + 22)
        if tone is not None:
            self._tone = tone
        self._redraw()

    def set_tone(self, tone: str, text: str | None = None) -> None:
        self.set(text=text, tone=tone)

    def configure(self, cnf=None, **kw):  # type: ignore[override]
        if isinstance(cnf, dict):
            kw.update(cnf)
        if "text" in kw:
            self.set(text=kw.pop("text"))
        if kw:
            return super().configure(**kw)
        return None

    config = configure

    def cget(self, key):  # type: ignore[override]
        if key == "text":
            return self._text
        if key == "bg":
            return self._colours()[0]
        if key == "fg":
            return self._colours()[1]
        return super().cget(key)
