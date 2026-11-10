"""PyInstaller entry point for the frozen `beesky-agent.exe`.

Same idea as packaging/entry.py, but hands argv to the agent app's
own dispatcher (beesky.agent_app.main): no arguments opens the
config window; `run` / `test` / `install-task` / `remove-task` do
what they say. The build is a CONSOLE build (see packaging/
beesky.spec) so `run` logs stay visible when started by hand — the
Scheduled Task doesn't care either way.
"""

import sys

from beesky.agent_app import main

if __name__ == "__main__":
    sys.exit(main())
