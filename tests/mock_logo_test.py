#!/usr/bin/env python3
"""BeeSky v0.11.2 logo wiring checks — pure file-content assertions.

The official BeeSky logo (packaging/assets/, from the owner's
Illustrator master) must be what every surface shows:

  * both web dashboards inline the real SVG in the header (no more
    CSS letter "B" mark) and carry it as an SVG favicon;
  * the PyInstaller spec uses beesky-logo.ico for both exes and
    bundles the logo PNG/ICO for the GUI build;
  * the Inno installer uses it as SetupIconFile and ships it;
  * the tkinter GUI resolves it (_asset_path / iconbitmap /
    iconphoto + header image).

No servers, no network — this is a static wiring test, run last in
tests/run_mock_test_v11_2.sh after the full v0.11 mock chain.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
VIEWBOX = 'viewBox="-373.37 -15.87 198.58 198.58"'
CHEVRON_FRAGMENT = "M-207.439,26.24"   # first chevron path of the master

FAILURES = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}: {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    # -- bundled assets exist -------------------------------------------
    for name in ("beesky-logo.svg", "beesky-logo.ico", "beesky-logo-512.png"):
        path = ROOT / "packaging" / "assets" / name
        check(f"asset bundled: packaging/assets/{name}",
              path.exists() and path.stat().st_size > 0)

    # -- dashboards: inline logo + favicon, letter mark gone ------------
    for rel in ("beesky/web/dashboard.html", "beesky/cloud/dashboard.html"):
        html = read(rel)
        check(f"{rel}: header inlines the official SVG",
              'class="logo-mark"' in html and VIEWBOX in html
              and CHEVRON_FRAGMENT in html and "#F4D600" in html)
        check(f"{rel}: SVG favicon link present",
              '<link rel="icon" type="image/svg+xml" '
              'href="data:image/svg+xml,' in html)
        check(f"{rel}: old CSS letter mark removed",
              '<span class="mark">B</span>' not in html
              and ".logo .mark" not in html)

    # -- PyInstaller spec ------------------------------------------------
    spec = read("packaging/beesky.spec")
    check("spec: exe icon is the official logo ico",
          'os.path.join(PROJECT_ROOT, "packaging", "assets", '
          '"beesky-logo.ico")' in spec)
    check("spec: GUI datas bundle the logo PNG + ICO",
          "GUI_DATAS" in spec and "beesky-logo-512.png" in spec
          and "beesky-logo.ico" in spec)

    # -- Inno installer ---------------------------------------------------
    iss = read("packaging/installer.iss")
    check("installer: SetupIconFile is the official logo ico",
          "SetupIconFile=assets\\beesky-logo.ico" in iss)
    check("installer: ships the official logo ico",
          'Source: "assets\\beesky-logo.ico"' in iss)

    # -- tkinter GUI -------------------------------------------------------
    gui = read("beesky/gui.py")
    check("gui: resolves bundled assets (_asset_path, _MEIPASS pattern)",
          "_asset_path" in gui and '"assets"' in gui)
    check("gui: window icon via iconbitmap + iconphoto fallback",
          "iconbitmap" in gui and "iconphoto" in gui)
    check("gui: header shows the logo PNG",
          "beesky-logo-512.png" in gui and "subsample" in gui)

    # -- version -----------------------------------------------------------
    # Version-relative since v0.12 (same fix the update test got in
    # v0.11): the wiring intent is "installer define == package
    # version", not a literal release number that ages out each bump.
    import beesky
    check("version: installer define matches the package version",
          f'#define MyAppVersion "{beesky.__version__}"' in iss,
          f"package reports {beesky.__version__}")

    if FAILURES:
        print(f"\nLOGO TEST FAILED ({len(FAILURES)} assertion(s))")
        return 1
    print("\nLOGO TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
