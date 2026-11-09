# PyInstaller spec — builds the two single-file BeeSky executables:
#
#   dist/beesky.exe      console CLI (entry.py — scan/watch/serve/
#                        agent/cloud/gui subcommands)
#   dist/beesky-gui.exe  windowed GUI (entry_gui.py pins argv to the
#                        `gui` subcommand; console=False so a
#                        double-click opens the BeeSky window, no
#                        black console behind it)
#
# PyInstaller does NOT cross-compile: this spec produces binaries for
# whatever OS runs it. The Windows exes are built on a windows-latest
# runner by .github/workflows/build-windows.yml:
#
#     pyinstaller packaging/beesky.spec --noconfirm
#
# BeeSky is pure Python 3 stdlib (argparse / tkinter / sqlite3 /
# urllib ...), so there are no third-party hidden imports to collect.
# tkinter ships with the standard CPython install and PyInstaller's
# built-in _tkinter hook bundles the Tcl/Tk runtime; the explicit
# hiddenimports below are just a nudge for the submodules the GUI
# imports lazily. The dashboard pages are bundled under beesky/<pkg>/
# in the _MEIPASS layout, which is exactly where beesky/web/server.py
# and beesky/cloud/server.py look first when running frozen.

import os

PROJECT_ROOT = os.path.dirname(SPECPATH)  # SPECPATH == <repo>/packaging
ICON = os.path.join(PROJECT_ROOT, "packaging", "beesky.ico")
DATAS = [
    (os.path.join(PROJECT_ROOT, "beesky", "web", "dashboard.html"),
     os.path.join("beesky", "web")),
    (os.path.join(PROJECT_ROOT, "beesky", "cloud", "dashboard.html"),
     os.path.join("beesky", "cloud")),
]
TK_HIDDENIMPORTS = ["tkinter", "tkinter.ttk", "tkinter.filedialog"]

# --- console CLI ------------------------------------------------------
a = Analysis(
    [os.path.join(PROJECT_ROOT, "packaging", "entry.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=DATAS,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="beesky",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON if os.path.exists(ICON) else None,
)

# --- windowed GUI -------------------------------------------------------
a_gui = Analysis(
    [os.path.join(PROJECT_ROOT, "packaging", "entry_gui.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=DATAS,
    hiddenimports=TK_HIDDENIMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz_gui = PYZ(a_gui.pure)

exe_gui = EXE(
    pyz_gui,
    a_gui.scripts,
    a_gui.binaries,
    a_gui.datas,
    [],
    name="beesky-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON if os.path.exists(ICON) else None,
)
