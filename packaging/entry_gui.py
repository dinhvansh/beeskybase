"""PyInstaller entry point for the frozen `beesky-gui.exe`.

Same idea as packaging/entry.py, but the GUI is a windowed build
(console=False in the spec), so the shim pins argv to the `gui`
subcommand: double-clicking the exe opens the BeeSky window with no
arguments at all. Any extra arguments are forwarded (e.g. a future
`beesky-gui.exe --smoke <target>` self-check).
"""

import sys

from beesky.cli import main

if __name__ == "__main__":
    sys.exit(main(["gui", *sys.argv[1:]]))
