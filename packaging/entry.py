"""PyInstaller entry point for the frozen `beesky.exe`.

PyInstaller needs a top-level script to freeze; this shim just hands
argv to the real CLI (`beesky.cli.main`), exactly like
`python -m beesky` does via `beesky/__main__.py`.
"""

import sys

from beesky.cli import main

if __name__ == "__main__":
    sys.exit(main())
