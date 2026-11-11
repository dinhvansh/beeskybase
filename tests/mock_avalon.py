#!/usr/bin/env python3
"""Fake Canaan Avalon — a cgminer-envelope device with Avalon STATS.

Same wire as tests/mock_miner.py ({"command": ...} on TCP 4028),
but the STATS entries carry the Avalon module keys "MM ID<n>" —
the fingerprint docs/vendor-coverage-mapping.md §2 ports from
HashCore's CgminerCommonStatsDto.fromAvalonJson. Deliberately NO
chain_acs data: Avalon chip semantics beyond the fingerprint are
not in the evidenced contract (G-A1), so the record must come out
with no chains and no chip claims. The privileged `restart`
command is accepted and recorded (env MOCK_AVALON_LOG) so the
actions test can prove the family reboot rides the cgminer RPC.

Run:  python3 tests/mock_avalon.py [host] [port]
"""

import json
import os
import socketserver
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4028
LOG = os.environ.get("MOCK_AVALON_LOG")


def _log(name: str) -> None:
    if LOG:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(name + "\n")


def summary_reply() -> dict:
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 11,
                    "Msg": "Summary", "Description": "mockavalon 1.0"}],
        "SUMMARY": [{
            "Elapsed": 54321,
            "Type": "AvalonMiner 1246",
            "GHS 5s": 89800.0,
            "GHS av": 90000.0,
            "MHS av": 90000000.0,
            "Accepted": 54321,
            "Rejected": 42,
            "Hardware Errors": 7,
        }],
        "id": 1,
    }


def stats_reply() -> dict:
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 70,
                    "Msg": "stats", "Description": "mockavalon 1.0"}],
        "STATS": [
            {
                "Type": "AvalonMiner 1246",
                "Miner": "mockavalon 1.0",
                "CompileTime": "Tue Jan 10 2023",
                "API": "3.1",
                "ID": "Avalon0",
                "Elapsed": 54321,
            },
            {
                "ID": "Avalon1",
                "MM ID0": "1246-230110-abcdef01",
                "MM ID1": "1246-230110-abcdef02",
                "MM ID2": "1246-230110-abcdef03",
            },
        ],
        "id": 1,
    }


def pools_reply() -> dict:
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 7,
                    "Msg": "pools", "Description": "mockavalon 1.0"}],
        "POOLS": [{
            "POOL": 0,
            "URL": "stratum+tcp://pool.example.com:3333",
            "Status": "Alive",
            "User": "avalonworker.001",
            "Accepted": 54321,
            "Rejected": 42,
        }],
        "id": 1,
    }


def restart_reply() -> dict:
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 85,
                    "Msg": "Restarting", "Description": "mockavalon 1.0"}],
        "id": 1,
    }


_REPLIES = {"summary": summary_reply, "stats": stats_reply,
            "pools": pools_reply, "restart": restart_reply}


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
        reply_fn = _REPLIES.get(command)
        if reply_fn is None:
            payload = {"STATUS": [{"STATUS": "E", "Code": 14,
                                   "Msg": f"Invalid command: {command}"}],
                       "id": 1}
        else:
            payload = reply_fn()
        try:
            self.request.sendall(json.dumps(payload).encode() + b"\x00")
        except OSError:
            pass


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((HOST, PORT), Handler) as server:
        print(f"mock avalon listening on {HOST}:{PORT}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
