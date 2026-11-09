#!/usr/bin/env python3
"""Scripted fake cgminer miner for the watch-mode test.

Same wire format as tests/mock_miner.py, but the numbers come from a
JSON *control file* that the test driver rewrites between watch passes:

    {"ghs": 110000, "temps": [65, 71, 74], "dead": {"2": [10, 55]}}

  ghs    -> "GHS 5s" and "GHS av" of the summary reply (GH/s)
  temps  -> per-chain temperatures in the stats reply
  dead   -> chain index (str) -> 1-based dead chip positions in chain_acs

A missing/unreadable control file falls back to a healthy S19 Pro.
Offline phases are simulated by the driver killing this process.

Remote actions (v0.6): the privileged ``restart`` RPC is answered like
a real unit — accepted (STATUS S) and recorded in a state file next to
the control file (``<control>.state.json``, ``{"restarts": n}``), or,
when the control file sets ``"api_writable": false``, refused with the
STATUS E "Access denied" a read-only-provisioned API returns.

Usage: python3 tests/mock_watch_miner.py --port 14028 --control ctrl.json
"""

import argparse
import json
import socketserver
import time
from pathlib import Path

CONTROL: Path | None = None
DEFAULTS = {"ghs": 110000.0, "temps": [65, 71, 74], "dead": {}}
CHIPS_PER_CHAIN = 114
CHAINS = 3


def _control() -> dict:
    try:
        data = json.loads(CONTROL.read_text(encoding="utf-8"))
        return {**DEFAULTS, **data}
    except (OSError, json.JSONDecodeError, TypeError):
        return dict(DEFAULTS)


def _state_path() -> Path:
    return CONTROL.with_name(CONTROL.name + ".state.json")


def _record_restart() -> None:
    path = _state_path()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    state["restarts"] = int(state.get("restarts") or 0) + 1
    state["last_restart_at"] = time.time()
    path.write_text(json.dumps(state), encoding="utf-8")


def restart_reply(ctrl: dict) -> dict:
    if ctrl.get("api_writable", True) is False:
        return {"STATUS": [{"STATUS": "E", "When": 1700000000, "Code": 45,
                            "Msg": "Access denied to 'restart' command",
                            "Description": "mockwatchminer 1.0"}], "id": 1}
    _record_restart()
    return {"STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 142,
                        "Msg": "Restarting", "Description": "mockwatchminer 1.0"}],
            "id": 1}


def _acs(total: int, dead=()) -> str:
    chars = ["o"] * total
    for pos in dead:
        chars[pos - 1] = "x"
    return "".join(chars)


def summary_reply(ctrl: dict) -> dict:
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 11,
                    "Msg": "Summary", "Description": "mockwatchminer 1.0"}],
        "SUMMARY": [{
            "Elapsed": 3600,
            "Type": "Antminer S19 Pro",
            "GHS 5s": ctrl["ghs"],
            "GHS av": ctrl["ghs"],
            "MHS av": ctrl["ghs"] * 1000.0,
            "Found Blocks": 0, "Getworks": 512, "Accepted": 2048,
            "Rejected": 12, "Hardware Errors": 3, "Utility": 34.13,
            "Total MH": 396000000.0,
        }],
        "id": 1,
    }


def stats_reply(ctrl: dict) -> dict:
    dead = {str(k): v for k, v in (ctrl.get("dead") or {}).items()}
    temps = list(ctrl.get("temps") or DEFAULTS["temps"])
    entry = {"ID": "BMminer1", "Elapsed": 3600, "Chains": CHAINS}
    for idx in range(1, CHAINS + 1):
        entry[f"chain_acs{idx}"] = _acs(CHIPS_PER_CHAIN, dead.get(str(idx), ()))
        entry[f"temp{idx}"] = temps[idx - 1] if idx - 1 < len(temps) else 65
        entry[f"frequency{idx}"] = 500
    for fan in range(1, 5):
        entry[f"fan{fan}"] = 4200 + fan * 60
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 70,
                    "Msg": "stats", "Description": "mockwatchminer 1.0"}],
        "STATS": [{"Type": "Antminer S19 Pro", "Miner": "mockwatchminer 1.0",
                   "API": "3.1", "ID": "BMminer0"}, entry],
        "id": 1,
    }


def pools_reply() -> dict:
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 7,
                    "Msg": "pools", "Description": "mockwatchminer 1.0"}],
        "POOLS": [{"POOL": 0, "URL": "stratum+tcp://pool.example.com:3333",
                   "Status": "Alive", "User": "mockworker.001",
                   "Accepted": 2048, "Rejected": 12}],
        "id": 1,
    }


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(5)
        data = b""
        try:
            while b"\n" not in data and len(data) < 65536:
                chunk = self.request.recv(4096)
                if not chunk:
                    break
                data += chunk
        except OSError:
            return
        if not data.strip():
            return  # bare port probe
        try:
            command = json.loads(
                data.decode("utf-8", errors="replace")).get("command", "")
        except json.JSONDecodeError:
            command = ""
        ctrl = _control()
        if command == "summary":
            payload = summary_reply(ctrl)
        elif command == "stats":
            payload = stats_reply(ctrl)
        elif command == "pools":
            payload = pools_reply()
        elif command == "restart":
            payload = restart_reply(ctrl)
        else:
            payload = {"STATUS": [{"STATUS": "E", "Code": 14,
                                   "Msg": f"Invalid command: {command}"}],
                       "id": 1}
        try:
            self.request.sendall(json.dumps(payload).encode() + b"\x00")
        except OSError:
            pass


def main():
    global CONTROL
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=14028)
    parser.add_argument("--control", required=True)
    args = parser.parse_args()
    CONTROL = Path(args.control)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((args.host, args.port), Handler) as srv:
        print(f"mock watch miner on {args.host}:{args.port} "
              f"(control: {CONTROL})", flush=True)
        srv.serve_forever()


if __name__ == "__main__":
    main()
