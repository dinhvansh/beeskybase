#!/usr/bin/env python3
"""Fake cgminer API server — a sick Antminer S19 Pro on 127.0.0.1:4028.

Sample data is deliberately unhealthy so the scanner has something to find:
  * board 2: exactly 3 dead chips (positions 10, 55, 114 of 114)
  * board 3: 88 C — above the 85 C flag threshold
  * boards otherwise healthy; hashrate reduced accordingly (~103 TH/s)

Run directly to serve forever:  python3 tests/mock_miner.py
"""

import json
import socketserver

HOST, PORT = "127.0.0.1", 4028
DEAD_BOARD2 = (10, 55, 114)  # 1-based chip positions


def _acs(total: int, dead: tuple[int, ...] = ()) -> str:
    chars = ["o"] * total
    for pos in dead:
        chars[pos - 1] = "x"
    return "".join(chars)


def summary_reply() -> dict:
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 11,
                    "Msg": "Summary", "Description": "mockminer 1.0"}],
        "SUMMARY": [{
            "Elapsed": 3600,
            "Type": "Antminer S19 Pro",
            "GHS 5s": 102900.0,
            "GHS av": 103250.0,
            "MHS av": 103250000.0,
            "Found Blocks": 0,
            "Getworks": 512,
            "Accepted": 2048,
            "Rejected": 12,
            "Hardware Errors": 3,
            "Utility": 34.13,
            "Total MH": 371700000.0,
        }],
        "id": 1,
    }


def stats_reply() -> dict:
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 70,
                    "Msg": "stats", "Description": "mockminer 1.0"}],
        "STATS": [
            {
                "Type": "Antminer S19 Pro",
                "Miner": "mockminer 1.0",
                "CompileTime": "Mon Nov 9 2026",
                "API": "3.1",
                "ID": "BMminer0",
            },
            {
                "ID": "BMminer1",
                "Elapsed": 3600,
                "Chains": 3,
                "chain_acs1": _acs(114),
                "chain_acs2": _acs(114, DEAD_BOARD2),
                "chain_acs3": _acs(114),
                "temp1": 65,
                "temp2": 71,
                "temp3": 88,
                "fan1": 4320,
                "fan2": 4380,
                "fan3": 4440,
                "fan4": 4500,
                "frequency1": 500,
                "frequency2": 500,
                "frequency3": 500,
            },
        ],
        "id": 1,
    }


def pools_reply() -> dict:
    return {
        "STATUS": [{"STATUS": "S", "When": 1700000000, "Code": 7,
                    "Msg": "pools", "Description": "mockminer 1.0"}],
        "POOLS": [{
            "POOL": 0,
            "URL": "stratum+tcp://pool.example.com:3333",
            "Status": "Alive",
            "User": "mockworker.001",
            "Accepted": 2048,
            "Rejected": 12,
        }],
        "id": 1,
    }


_REPLIES = {"summary": summary_reply, "stats": stats_reply, "pools": pools_reply}


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
            command = json.loads(data.decode("utf-8", errors="replace")).get("command", "")
        except json.JSONDecodeError:
            command = ""
        reply_fn = _REPLIES.get(command)
        if reply_fn is None:
            payload = {"STATUS": [{"STATUS": "E", "Code": 14,
                                   "Msg": f"Invalid command: {command}"}], "id": 1}
        else:
            payload = reply_fn()
        try:
            # cgminer replies end with a trailing NUL byte.
            self.request.sendall(json.dumps(payload).encode() + b"\x00")
        except OSError:
            pass


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((HOST, PORT), Handler) as server:
        print(f"mock miner listening on {HOST}:{PORT}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
