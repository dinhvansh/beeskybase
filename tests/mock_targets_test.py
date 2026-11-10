#!/usr/bin/env python3
"""v0.19.6 test — auto-detected default target + multi-range targets.

Field bug behind the release: on the owner's laptop the scan target
defaulted to the hard-coded 192.168.1.0/24, his fleet lives on
192.168.2.0/24, the sweep found 0 miners and the app read as broken;
and BTC Tools next to it scanned several /24 ranges at once while
BeeSky's target was treated as a single spec.

Asserts:

  * default_scan_target() (beesky/core/discover.py) maps the primary
    LAN IPv4 from the UDP-connect trick to its /24, with the socket
    layer stubbed: a normal detection, a failure at socket creation,
    a failure at connect, a failure at getsockname, and loopback /
    link-local / unspecified results ALL fall back to
    192.168.1.0/24 — the helper never raises;
  * parse_targets() unions comma-separated specs: union of several
    ranges, first-seen order (not a global re-sort), de-duplication
    of overlapping specs, whitespace tolerance, mixed item forms,
    the size cap applied to the de-duplicated union, one bad item
    rejecting the whole spec, and single-spec output unchanged;
  * the main GUI pre-fills its target from the helper (stubbed for
    determinism) and an explicit default still wins; a comma target
    reaches the scan pipeline byte-for-byte unchanged;
  * the agent config window pre-fills the target on first run (no
    config file), a saved config still wins over the helper, and a
    comma target survives the form -> AgentConfig round-trip;
  * the CLI `gui` command passes no target by default (None -> the
    GUI resolves it via the helper) and an explicit --target wins.

Runs under xvfb-run (see run_mock_test_v19_6.sh) for the Tk parts.
Prints PASS lines; exit 1 on failure.
"""

import socket
import sys
import tkinter as tk
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from beesky.core import discover  # noqa: E402
from beesky.core.discover import (  # noqa: E402
    FALLBACK_TARGET, default_scan_target, parse_targets)

FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label} {extra}")
        FAILURES.append(label)


# ----------------------------------------------------------------------
# default_scan_target — socket layer stubbed
# ----------------------------------------------------------------------

class _FakeSocket:
    """Stand-in for a UDP socket: records connect(), serves a canned
    getsockname(), and can be armed to fail at either call."""

    def __init__(self, family, type_, result=None, connect_error=None,
                 name_error=None):
        self.family = family
        self.type = type_
        self._result = result
        self._connect_error = connect_error
        self._name_error = name_error
        self.connected_to = None

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def connect(self, address):
        if self._connect_error is not None:
            raise self._connect_error
        self.connected_to = address

    def getsockname(self):
        if self._name_error is not None:
            raise self._name_error
        return self._result


def _stubbed_factory(created, **fake_kwargs):
    def factory(family, type_):
        sock = _FakeSocket(family, type_, **fake_kwargs)
        created.append(sock)
        return sock
    return factory


def test_helper() -> None:
    check("fallback constant is the historic default",
          FALLBACK_TARGET == "192.168.1.0/24")

    created: list[_FakeSocket] = []
    with mock.patch.object(socket, "socket", _stubbed_factory(
            created, result=("192.168.2.37", 54321))):
        got = default_scan_target()
    check("helper: detected 192.168.2.37 -> its /24",
          got == "192.168.2.0/24", got)
    check("helper: detection used an AF_INET datagram socket",
          len(created) == 1
          and created[0].family == socket.AF_INET
          and created[0].type == socket.SOCK_DGRAM
          and created[0].connected_to is not None)

    with mock.patch.object(socket, "socket", _stubbed_factory(
            [], result=("10.20.30.40", 0))):
        check("helper: detected 10.20.30.40 -> 10.20.30.0/24",
              default_scan_target() == "10.20.30.0/24")

    def dead_factory(_family, _type):
        raise OSError("no sockets")
    with mock.patch.object(socket, "socket", dead_factory):
        check("helper: socket creation failure -> fallback",
              default_scan_target() == FALLBACK_TARGET)

    with mock.patch.object(socket, "socket", _stubbed_factory(
            [], connect_error=OSError("network unreachable"))):
        check("helper: connect failure (offline) -> fallback",
              default_scan_target() == FALLBACK_TARGET)

    with mock.patch.object(socket, "socket", _stubbed_factory(
            [], name_error=OSError("no address"))):
        check("helper: getsockname failure -> fallback, never raises",
              default_scan_target() == FALLBACK_TARGET)

    for ip, why in (("127.0.0.1", "loopback"),
                    ("169.254.9.9", "link-local"),
                    ("0.0.0.0", "unspecified")):
        with mock.patch.object(socket, "socket", _stubbed_factory(
                [], result=(ip, 0))):
            check(f"helper: {why} result {ip} -> fallback",
                  default_scan_target() == FALLBACK_TARGET)

    real = default_scan_target()
    check("helper: unstubbed call returns a parseable /24 target",
          real.endswith("/24") and len(parse_targets(real)) == 254,
          real)


# ----------------------------------------------------------------------
# parse_targets — multi-range union
# ----------------------------------------------------------------------

def _raises_value_error(spec: str) -> bool:
    try:
        parse_targets(spec)
    except ValueError:
        return True
    return False


def test_parser() -> None:
    check("parser: union of two CIDRs",
          parse_targets("192.168.0.0/30, 192.168.2.0/30")
          == ["192.168.0.1", "192.168.0.2",
              "192.168.2.1", "192.168.2.2"])
    check("parser: union keeps first-seen order, no global re-sort",
          parse_targets("192.168.2.0/30, 192.168.0.0/30")
          == ["192.168.2.1", "192.168.2.2",
              "192.168.0.1", "192.168.0.2"])
    check("parser: overlapping ranges de-duplicate",
          parse_targets("192.168.1.10-192.168.1.12, "
                        "192.168.1.11-192.168.1.13")
          == ["192.168.1.10", "192.168.1.11",
              "192.168.1.12", "192.168.1.13"])
    check("parser: an item fully inside another adds nothing",
          parse_targets("192.168.1.0/30, 192.168.1.1")
          == ["192.168.1.1", "192.168.1.2"])
    check("parser: whitespace around items is tolerated",
          parse_targets("  192.168.0.1 ,  192.168.0.2 ")
          == ["192.168.0.1", "192.168.0.2"])
    check("parser: mixed forms (IP + CIDR + range) union",
          parse_targets("10.0.0.5, 10.0.1.0/30, 10.0.2.7-10.0.2.8")
          == ["10.0.0.5", "10.0.1.1", "10.0.1.2",
              "10.0.2.7", "10.0.2.8"])
    check("parser: one bad item rejects the whole spec",
          _raises_value_error("192.168.0.0/30, bogus"))
    check("parser: bad first item rejects the whole spec",
          _raises_value_error("bogus, 192.168.0.0/30"))
    check("parser: empty spec still rejected",
          _raises_value_error(""))
    check("parser: oversized union still rejected",
          _raises_value_error("10.0.0.0/16"))
    check("parser: size cap counts the union, not raw duplicates",
          len(parse_targets(", ".join(["10.1.0.0/22"] * 5))) == 1022)
    check("parser: single CIDR output unchanged",
          parse_targets("192.168.1.0/30")
          == ["192.168.1.1", "192.168.1.2"])
    check("parser: single IP output unchanged",
          parse_targets("192.168.1.50") == ["192.168.1.50"])
    check("parser: single range output unchanged",
          parse_targets("192.168.1.10-192.168.1.12")
          == ["192.168.1.10", "192.168.1.11", "192.168.1.12"])


# ----------------------------------------------------------------------
# desktop apps — defaults + comma passthrough (Tk; xvfb)
# ----------------------------------------------------------------------

COMMA_SPEC = "192.168.0.0/30, 192.168.2.0/30"
STUB_TARGET = "10.9.8.0/24"


def test_main_gui() -> None:
    from beesky import gui

    original = gui.default_scan_target
    gui.default_scan_target = lambda: STUB_TARGET
    try:
        root = tk.Tk()
        try:
            app = gui.BeeSkyApp(root)
            check("main gui: target pre-filled from the helper",
                  app.target_var.get() == STUB_TARGET,
                  app.target_var.get())
        finally:
            root.destroy()

        root = tk.Tk()
        try:
            app = gui.BeeSkyApp(root, default_target="172.16.0.0/24")
            check("main gui: explicit default beats the helper",
                  app.target_var.get() == "172.16.0.0/24",
                  app.target_var.get())
        finally:
            root.destroy()
    finally:
        gui.default_scan_target = original

    from beesky import cli
    captured: dict = {}

    def fake_scan_records(args):
        captured["target"] = args.target
        return []

    original_scan = cli._scan_records
    cli._scan_records = fake_scan_records
    try:
        gui._scan(COMMA_SPEC, "root", "root")
    finally:
        cli._scan_records = original_scan
    check("main gui: comma target reaches the scan unchanged",
          captured.get("target") == COMMA_SPEC, str(captured))
    check("main gui: make_scan_args passes the target through",
          gui.make_scan_args(COMMA_SPEC).target == COMMA_SPEC)


def test_agent_gui(tmp: Path) -> None:
    from beesky import agent_gui
    from beesky.agent_config import AgentConfig

    original = agent_gui.default_scan_target
    agent_gui.default_scan_target = lambda: STUB_TARGET
    try:
        root = tk.Tk()
        try:
            app = agent_gui.AgentConfigApp(
                root, config_path=tmp / "missing.json")
            check("agent gui: first run pre-fills the helper target",
                  app.target_var.get() == STUB_TARGET,
                  app.target_var.get())
            app.target_var.set(COMMA_SPEC)
            check("agent gui: comma target reaches the config "
                  "unchanged",
                  app.current_config().target == COMMA_SPEC,
                  app.current_config().target)
        finally:
            root.destroy()

        saved = tmp / "agent-config.json"
        AgentConfig(target="192.168.5.0/24").save(saved)
        root = tk.Tk()
        try:
            app = agent_gui.AgentConfigApp(root, config_path=saved)
            check("agent gui: saved config target beats the helper",
                  app.target_var.get() == "192.168.5.0/24",
                  app.target_var.get())
        finally:
            root.destroy()
    finally:
        agent_gui.default_scan_target = original

    cfg = AgentConfig.from_dict(AgentConfig(
        target=COMMA_SPEC).to_dict())
    check("agent config: comma target round-trips verbatim",
          cfg.target == COMMA_SPEC, cfg.target)


def test_cli() -> None:
    from beesky import cli, gui

    captured: list = []
    original = gui.run_gui
    gui.run_gui = lambda default_target=None: \
        captured.append(default_target) or 0
    try:
        rc_auto = cli.main(["gui"])
        rc_explicit = cli.main(["gui", "--target", "192.168.7.0/24"])
    finally:
        gui.run_gui = original
    check("cli: `gui` without --target hands None to run_gui "
          "(helper resolves it)",
          rc_auto == 0 and captured[:1] == [None], str(captured))
    check("cli: `gui --target X` hands X through unchanged",
          rc_explicit == 0 and captured[1:] == ["192.168.7.0/24"],
          str(captured))


def main() -> int:
    import tempfile
    test_helper()
    test_parser()
    test_main_gui()
    with tempfile.TemporaryDirectory() as tmp:
        test_agent_gui(Path(tmp))
    test_cli()
    print()
    if FAILURES:
        print(f"TARGETS TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("TARGETS TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
