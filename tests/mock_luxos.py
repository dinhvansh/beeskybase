#!/usr/bin/env python3
"""Fake LuxOS (LUXminer) — the cgminer-compatible TCP API on 4028.

Speaks the contract in docs/vendor-docs-mapping.md §2, built from
Luxor's own docs pages (values quoted verbatim from them):

  * `version` -> STATUS Description "LUXminer 2024.5.1.155432-f2badc0f"
    (the exact string Luxor's own `luxos` CLI prints for --cmd version)
    — the detection fingerprint;
  * `summary` / `stats` / `pools` in cgminer vocabulary: an S19 Pro
    at ~109 TH/s, 3 boards; board 2 runs at 87 C with 2 dead chip
    positions so the record builder flags OVER_TEMP + missing chips;
  * `logon` -> SESSION [{"SessionID": "yJN2nlj1"}] (the Sessions
    page's own example id), Code 316; `logoff` -> Code 317;
  * `curtail` with parameter "<session>,sleep|wakeup" -> the
    curtail page's CURTAIL payloads, Code 335; a wrong session is
    refused (STATUS-E);
  * `rebootdevice` -> STATUS S (the command name is Luxor's own
    CLI's; its reply code is a mock choice — the client only
    requires STATUS S).

Every received command name is appended to the file named by env
MOCK_LUXOS_LOG (when set) so tests can assert what the scanner
did and did NOT ask (notably: reads never logon).

Run:  python3 tests/mock_luxos.py [host] [port]
"""

import json
import os
import socketserver
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4028
LOG = os.environ.get("MOCK_LUXOS_LOG")

SESSION_ID = "yJN2nlj1"  # the Sessions page's example id
VERSION = "LUXminer 2024.5.1.155432-f2badc0f"


def _log(name: str) -> None:
    if LOG:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(name + "\n")


def _status(code: int, msg: str, status: str = "S") -> dict:
    return {"STATUS": [{"STATUS": status, "When": 1700000000,
                        "Code": code, "Msg": msg,
                        "Description": VERSION}],
            "id": 1}


def summary_reply() -> dict:
    payload = _status(11, "Summary")
    payload["SUMMARY"] = [{
        "Elapsed": 86400,
        "Type": "Antminer S19 Pro",
        "GHS 5s": 109130.0,
        "GHS av": 109000.0,
        "MHS av": 109000000.0,
        "Accepted": 98765,
        "Rejected": 98,
        "Hardware Errors": 3,
    }]
    return payload


def stats_reply() -> dict:
    payload = _status(70, "stats")
    acs = "o" * 114
    acs_hot = "o" * 60 + "x" + "o" * 51 + "x" + "o"
    payload["STATS"] = [
        {
            "Type": "Antminer S19 Pro",
            "Miner": VERSION,
            "CompileTime": "Mon May 1 2024",
            "API": "3.1",
            "ID": "LUX0",
            "Elapsed": 86400,
        },
        {
            "ID": "LUX1",
            "chain_acs1": acs,
            "chain_acs2": acs_hot,
            "chain_acs3": acs,
            "temp1": 61.0,
            "temp2": 87.0,
            "temp3": 63.0,
            "fan1": 4320,
            "fan2": 4380,
        },
    ]
    return payload


def pools_reply() -> dict:
    payload = _status(7, "pools")
    payload["POOLS"] = [{
        "POOL": 0,
        "URL": "stratum+tcp://pool.example.com:3333",
        "Status": "Alive",
        "User": "luxosworker.001",
        "Accepted": 98765,
        "Rejected": 98,
    }]
    return payload


def version_reply() -> dict:
    payload = _status(22, "Version")
    payload["VERSION"] = [{
        "CGMiner": "4.11.1",
        "API": "3.1",
        "Miner": VERSION,
        "CompileTime": "Mon May 1 2024",
    }]
    return payload


def logon_reply() -> dict:
    payload = _status(316, "Session created")
    payload["SESSION"] = [{"SessionID": SESSION_ID}]
    return payload


def logoff_reply() -> dict:
    return _status(317, "Session dropped")


def session_reply() -> dict:
    payload = _status(319, "Session information")
    payload["SESSION"] = [{"SessionID": SESSION_ID}]
    return payload


def curtail_reply(action: str) -> dict:
    payload = _status(335, "Curtailment command sent")
    if action == "sleep":
        payload["CURTAIL"] = [{"Action": "sleep mode"}]
    else:
        payload["CURTAIL"] = [{"Action": "wake up",
                               "FrequencyStep": 5,
                               "VoltageStep": 0.05}]
    return payload


_REPLIES = {"summary": summary_reply, "stats": stats_reply,
            "pools": pools_reply, "version": version_reply,
            "logon": logon_reply, "logoff": logoff_reply,
            "session": session_reply}


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
        command = request.get("command", "")
        _log(command)
        if command == "curtail":
            param = str(request.get("parameter") or "")
            parts = param.split(",")
            session, action = (parts[0] if parts else ""), \
                (parts[1] if len(parts) > 1 else "")
            if session != SESSION_ID:
                payload = _status(45, "Invalid session", status="E")
            elif action not in ("sleep", "wakeup"):
                payload = _status(14, f"Invalid curtail action: {action}",
                                  status="E")
            else:
                payload = curtail_reply(action)
        elif command == "rebootdevice":
            payload = _status(85, "Rebooting device")
        elif command in _REPLIES:
            payload = _REPLIES[command]()
        else:
            payload = _status(14, f"Invalid command: {command}",
                              status="E")
        try:
            self.request.sendall(json.dumps(payload).encode() + b"\x00")
        except OSError:
            pass


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((HOST, PORT), Handler) as server:
        print(f"mock luxos listening on {HOST}:{PORT}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
