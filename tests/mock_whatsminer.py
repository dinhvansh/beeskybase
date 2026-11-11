#!/usr/bin/env python3
"""Fake MicroBT Whatsminer — the API v2 socket dialect on TCP 4028.

Speaks the contract dissected in docs/vendor-coverage-mapping.md
§1 plus the privileged side closed in v0.33.0 from MicroBT's own
manuals (docs/vendor-docs-mapping.md §1): requests are
{"cmd": "<name>"} envelopes, replies wrap their payload in a
"Msg" envelope (a list for summary/devs/pools, a dict for
version). The summary item carries the Whatsminer fan pair
("Fan Speed In" / "Fan Speed Out") — the detection fingerprint.
Board 2 runs at 87 C so the record builder flags OVER_TEMP.

Token flow (the mock uses the manuals' OWN worked example, so
the client's token is checked against an independent value, not
against the implementation under test):

  get_token -> {"time": "5626", "salt": "BQ5hoXV9",
                "newsalt": "jbzkfQls"}   (manual §3 example)
  expected sign for password "admin" (the manual's default):
  "w.BNbkCV6n1aNWgiBWLzT/" — generated with the manuals' own
  reference implementation (openssl passwd -1); any other
  password computes a different sign and is refused.

Privileged commands (restart_btminer, reboot, power_off,
power_on, set_led, update_pools) answer Code 131 only when the
request's "token" equals that sign, else Code 135 ("check token
error", the manual's own code). A privileged command sent with
NO token is refused the same way. cgminer-envelope requests
({"command": ...}) are refused like the real dialect boundary.

Every received request's cmd/command name is appended to the
file named by env MOCK_WM_LOG (when set) so tests can assert
what the scanner did and did NOT ask (notably: reads never send
get_token). update_pools requests also log one
"update_pools:pool1=<url>:worker1=<worker>:pool2=...:..." line
(all three slots) so tests can prove the pool payload shape.

Run:  python3 tests/mock_whatsminer.py [host] [port]
"""

import json
import os
import socketserver
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4028
LOG = os.environ.get("MOCK_WM_LOG")

# The manuals' worked example (V2.0.5 §3): get_token returns these
# exact fields, and the sign for the default password "admin" is
# this openssl-derived value (see docs/vendor-docs-mapping.md §1.3).
TOKEN_TIME = "5626"
TOKEN_SALT = "BQ5hoXV9"
TOKEN_NEWSALT = "jbzkfQls"
EXPECTED_SIGN = "w.BNbkCV6n1aNWgiBWLzT/"

_PRIVILEGED = ("restart_btminer", "reboot", "power_off", "power_on",
               "set_led", "update_pools")


def _log(name: str) -> None:
    if LOG:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(name + "\n")


def _ok(msg, code=131):
    return {"STATUS": [{"STATUS": "S", "When": 1700000000,
                        "Code": code, "Msg": "ok",
                        "Description": "mockwhatsminer 1.0"}],
            "Msg": msg, "id": 1}


def _err(message: str, code: int = 14):
    return {"STATUS": [{"STATUS": "E", "When": 1700000000,
                        "Code": code, "Msg": message,
                        "Description": "mockwhatsminer 1.0"}], "id": 1}


def summary_reply() -> dict:
    return _ok([{
        "Elapsed": 90061,
        "Type": "WhatsMiner M30S",
        "MHS 5s": 111800000.0,
        "MHS av": 112000000.0,
        "Fan Speed In": 4560,
        "Fan Speed Out": 4620,
        "Accepted": 123456,
        "Rejected": 123,
        "Hardware Errors": 4,
        "Stratum URL": "stratum+tcp://btc.pool.example:3333",
    }])


def devs_reply() -> dict:
    return _ok([
        {"Slot": 0, "Status": "Alive", "Temperature": 62.0,
         "MHS av": 37300000.0},
        {"Slot": 1, "Status": "Alive", "Temperature": 87.0,
         "MHS av": 37100000.0},
        {"Slot": 2, "Status": "Alive", "Temperature": 65.0,
         "MHS av": 37600000.0},
    ])


def pools_reply() -> dict:
    return _ok([{
        "POOL": 0,
        "URL": "stratum+tcp://btc.pool.example:3333",
        "Status": "Alive",
        "User": "wmworker.001",
        "Accepted": 123456,
        "Rejected": 123,
    }])


def version_reply() -> dict:
    return _ok({"Type": "WhatsMiner M30S", "BMMiner": "2.0.0",
                "API": "2.0"})


def token_reply() -> dict:
    return _ok({"time": TOKEN_TIME, "salt": TOKEN_SALT,
                "newsalt": TOKEN_NEWSALT}, code=134)


_REPLIES = {"summary": summary_reply, "devs": devs_reply,
            "pools": pools_reply, "version": version_reply,
            "get_token": token_reply}


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
            return  # bare port probe — nothing to answer
        try:
            request = json.loads(data.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            request = {}
        cmd = request.get("cmd")
        if cmd is None:
            # The cgminer envelope is a different dialect — refused.
            _log(f"command:{request.get('command', '')}")
            payload = _err("Invalid command")
        else:
            _log(cmd)
            if cmd in _PRIVILEGED:
                if request.get("token") != EXPECTED_SIGN:
                    payload = _err("check token error", code=135)
                else:
                    if cmd == "update_pools":
                        _log(":".join(
                            [f"update_pools"]
                            + [f"pool{i}={request.get(f'pool{i}', '')}"
                               f":worker{i}={request.get(f'worker{i}', '')}"
                               for i in (1, 2, 3)]))
                    payload = _ok({})
            elif cmd in _REPLIES:
                payload = _REPLIES[cmd]()
            else:
                payload = _err(f"Invalid cmd: {cmd}")
        try:
            self.request.sendall(json.dumps(payload).encode() + b"\x00")
        except OSError:
            pass


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((HOST, PORT), Handler) as server:
        print(f"mock whatsminer listening on {HOST}:{PORT}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
