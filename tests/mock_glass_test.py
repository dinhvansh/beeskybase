#!/usr/bin/env python3
"""v0.18 test — Liquid Glass (web real, desktop simulated).

Asserts:

  * both web dashboards carry the glass material: the translucent
    tokens (--glass rgba(255,255,255,.045) etc.), backdrop-filter
    blur(16px) saturate(150%) on the card surfaces, the ambient
    radial-gradient body backdrop, the @supports no-backdrop-filter
    fallback AND the prefers-reduced-transparency fallback (both
    re-pointing the tokens at the solid colours), and the accent
    CTA still solid BeeSky yellow;
  * the desktop simulation: ui_theme's glass tokens feed the
    rounded widgets — a RoundedCard's drawn surface fill is
    PANEL_GLASS with GLASS_BORDER outline, and it draws exactly
    ONE rim-light item (tagged "rim") that survives a resize
    without double-drawing; a ghost RoundedButton draws one rim
    item while an accent button draws none; the ghost colour
    triple is (GHOST_FILL, GLASS_BORDER, TEXT); a RoundedEntry's
    shape fill/outline are ENTRY_FILL / ENTRY_BORDER.

Runs the desktop part under xvfb-run (see run_mock_test_v18.sh).
Prints PASS lines; exit 1 on failure.
"""

import sys
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from beesky import ui_theme  # noqa: E402
from beesky.rounded import RoundedButton, RoundedEntry  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label} {extra}")
        FAILURES.append(label)


def test_web() -> None:
    for name in ("cloud/dashboard.html", "web/dashboard.html"):
        css = (ROOT / "beesky" / name).read_text(encoding="utf-8")
        check(f"web {name}: glass token is translucent white .045",
              "--glass: rgba(255, 255, 255, .045)" in css)
        check(f"web {name}: glass line token is rgba .09",
              "--glass-line: rgba(255, 255, 255, .09)" in css)
        check(f"web {name}: backdrop blur 16px saturate 150% applied",
              "backdrop-filter: var(--glass-blur)" in css
              and "--glass-blur: blur(16px) saturate(150%)" in css)
        check(f"web {name}: ambient radial-gradient body backdrop",
              "radial-gradient(600px 400px at 15% -5%, "
              "rgba(245, 216, 0, .07), transparent 60%)" in css
              and "background-attachment: fixed" in css)
        check(f"web {name}: @supports no-backdrop-filter fallback",
              "@supports not ((backdrop-filter: blur(1px)) or "
              "(-webkit-backdrop-filter: blur(1px)))" in css
              and "--glass: #15151A" in css)
        check(f"web {name}: reduced-transparency fallback",
              "@media (prefers-reduced-transparency: reduce)" in css)
        check(f"web {name}: glass shadow token (rim inset + drop)",
              "--glass-shadow: inset 0 1px 0 rgba(255, 255, 255, .08), "
              "0 8px 32px rgba(0, 0, 0, .35)" in css)
        check(f"web {name}: accent CTA stays solid yellow",
              "background: var(--yellow)" in css)


def test_desktop(root) -> None:
    card = ui_theme.card(root, title="Kính lỏng", pad=12)
    card.pack(fill="both", expand=True)
    root.geometry("420x220")
    root.update()
    canvas = card._canvas
    surfaces = canvas.find_withtag("surface")
    check("desktop: card surface is drawn", len(surfaces) >= 1,
          str(surfaces))
    fill_item = surfaces[0]
    check("desktop: card fill is PANEL_GLASS, outline GLASS_BORDER",
          canvas.itemcget(fill_item, "fill") == ui_theme.PANEL_GLASS
          and canvas.itemcget(fill_item, "outline")
          == ui_theme.GLASS_BORDER,
          f"{canvas.itemcget(fill_item, 'fill')} / "
          f"{canvas.itemcget(fill_item, 'outline')}")
    rims = canvas.find_withtag("rim")
    check("desktop: card draws exactly one rim-light item",
          len(rims) == 1, str(len(rims)))
    if rims:
        check("desktop: rim light colour is RIM_LIGHT",
              canvas.itemcget(rims[0], "fill") == ui_theme.RIM_LIGHT)
    root.geometry("560x300")
    root.update()
    check("desktop: rim survives a resize without double-drawing",
          len(canvas.find_withtag("rim")) == 1
          and len(canvas.find_withtag("surface")) == 2,
          f"rim={len(canvas.find_withtag('rim'))} "
          f"surface={len(canvas.find_withtag('surface'))}")

    ghost = RoundedButton(root, text="Ma quái", variant="ghost")
    ghost.pack()
    accent = RoundedButton(root, text="Quét ngay", variant="accent")
    accent.pack()
    root.update()
    check("desktop: ghost button draws one rim item, accent none",
          len(ghost.find_withtag("rim")) == 1
          and len(accent.find_withtag("rim")) == 0,
          f"ghost={len(ghost.find_withtag('rim'))} "
          f"accent={len(accent.find_withtag('rim'))}")
    check("desktop: ghost colours are the glass triple",
          ghost._colours() == (ui_theme.GHOST_FILL,
                               ui_theme.GLASS_BORDER, ui_theme.TEXT),
          str(ghost._colours()))
    ghost.set_state("disabled")
    root.update()
    check("desktop: disabled ghost drops the rim, mutes to glass",
          len(ghost.find_withtag("rim")) == 0
          and ghost._colours() == (ui_theme.PANEL_GLASS,
                                   ui_theme.GLASS_BORDER,
                                   ui_theme.MUTED),
          str(ghost._colours()))
    ghost.set_state("normal")

    var = tk.StringVar()
    entry = RoundedEntry(root, textvariable=var, width=14)
    entry.pack()
    root.update()
    check("desktop: entry shape is ENTRY_FILL / ENTRY_BORDER",
          entry.itemcget(entry._shape, "fill") == ui_theme.ENTRY_FILL
          and entry.itemcget(entry._shape, "outline")
          == ui_theme.ENTRY_BORDER,
          f"{entry.itemcget(entry._shape, 'fill')} / "
          f"{entry.itemcget(entry._shape, 'outline')}")
    check("desktop: hosted entry bg matches the glass fill",
          str(entry.entry.cget("bg")).casefold()
          == ui_theme.ENTRY_FILL.casefold())


def test_version_stamp() -> None:
    """v0.18.1: served dashboards carry the running version, never a
    stale hard-coded one (the footers sat at v0.13/v0.8 for months)."""
    from beesky import __version__
    from beesky.cloud.server import _load_dashboard_html as load_cloud
    from beesky.web.server import _load_dashboard_html as load_web
    for name, loader in (("cloud", load_cloud), ("web", load_web)):
        html = loader().decode("utf-8")
        check(f"{name}: served footer shows current version",
              f"v{__version__}" in html)
        check(f"{name}: no un-stamped placeholder left",
              "{{VERSION}}" not in html)


def main() -> int:
    test_web()
    test_version_stamp()
    root = tk.Tk()
    try:
        ui_theme.setup_theme(root)
        test_desktop(root)
    finally:
        root.destroy()
    print()
    if FAILURES:
        print(f"GLASS TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("GLASS TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
