# PyInstaller spec — builds a single-file console `beesky.exe`.
#
# PyInstaller does NOT cross-compile: this spec produces a binary for
# whatever OS runs it. The Windows exe is built on a windows-latest
# runner by .github/workflows/build-windows.yml:
#
#     pyinstaller packaging/beesky.spec --noconfirm
#
# BeeSky is pure Python 3 stdlib (verified: argparse / concurrent /
# dataclasses / hashlib / ipaddress / json / socket / statistics /
# urllib ...), so there are no hidden imports or hooks to collect —
# the whole `beesky` package is found through the entry shim. The one
# kind of data file is the two dashboard pages (serve + cloud): they
# are bundled under beesky/<pkg>/ in the _MEIPASS layout, which is
# exactly where beesky/web/server.py and beesky/cloud/server.py look
# first when running frozen.

import os

PROJECT_ROOT = os.path.dirname(SPECPATH)  # SPECPATH == <repo>/packaging
ICON = os.path.join(PROJECT_ROOT, "packaging", "beesky.ico")

a = Analysis(
    [os.path.join(PROJECT_ROOT, "packaging", "entry.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        (os.path.join(PROJECT_ROOT, "beesky", "web", "dashboard.html"),
         os.path.join("beesky", "web")),
        (os.path.join(PROJECT_ROOT, "beesky", "cloud", "dashboard.html"),
         os.path.join("beesky", "cloud")),
    ],
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
