#!/usr/bin/env python3
"""Fake Bitmain stock-firmware web server — a healthy S19 on 127.0.0.3:80.

Everything sits behind HTTP digest auth (factory default root/root),
verified properly (RFC 7616, MD5, qop=auth) so the client's hand-rolled
digest code is exercised end to end:

  GET /cgi-bin/get_miner_status.cgi — {"DATA": {SUMMARY, STATS}} mirroring
      the cgminer sections, like the real stock CGI. This build's status
      payload deliberately omits the model name, so the scanner must fall
      back to system info for it.
  GET /cgi-bin/get_system_info.cgi  — {"DATA": {"minertype": "Antminer S19",
      "gMac": ..., ...}}

The miner is healthy: 3 chains x 114 chips all responding, temps <= 70 C,
~95 TH/s — the scanner must report it OK.

Remote actions (v0.6): ``GET /cgi-bin/reboot.cgi`` (digest-auth, like
everything else here) answers 200 with an HTML page and records the
hit to the JSON state file named by BEESKY_MOCK_BITMAIN_STATE.

Run directly to serve forever:  python3 tests/mock_bitmain.py [host] [port]
"""

import hashlib
import json
import os
import re
import secrets
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.3"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 80
STATE_PATH = os.environ.get("BEESKY_MOCK_BITMAIN_STATE")
_REBOOTS: list[float] = []


def _record_reboot() -> None:
    _REBOOTS.append(time.time())
    if STATE_PATH:
        Path(STATE_PATH).write_text(
            json.dumps({"reboots": _REBOOTS}), encoding="utf-8")

USERNAME = "root"
PASSWORD = "root"
REALM = "WebAdmin"
NONCE = secrets.token_hex(16)
OPAQUE = "beesky-mock"


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _check_digest(header: str, method: str, uri: str) -> bool:
    params = {}
    for match in re.finditer(r'(\w+)=(?:"([^"]*)"|([^,\s]+))', header or ""):
        params[match.group(1)] = (
            match.group(2) if match.group(2) is not None else match.group(3))
    if params.get("username") != USERNAME or params.get("nonce") != NONCE:
        return False
    if params.get("uri") != uri:
        return False
    ha1 = _md5(f"{USERNAME}:{REALM}:{PASSWORD}")
    ha2 = _md5(f"{method}:{uri}")
    if params.get("qop"):
        expected = _md5(
            f"{ha1}:{NONCE}:{params.get('nc')}:{params.get('cnonce')}"
            f":{params['qop']}:{ha2}")
    else:
        expected = _md5(f"{ha1}:{NONCE}:{ha2}")
    return secrets.compare_digest(expected, params.get("response", ""))


def miner_status_payload() -> dict:
    acs = "o" * 114
    return {
        "STATUS": [{
            "STATUS": "S", "When": 1700003600, "Code": 0,
            "Msg": "getMinerStatus ok", "Description": "bmminer",
        }],
        "DATA": {
            "SUMMARY": [{
                "Elapsed": 7200,
                "GHS 5s": 95100.0,
                "GHS av": 95050.0,
                "MHS av": 95050000.0,
                "Found Blocks": 0,
                "Accepted": 4096,
                "Rejected": 4,
                "Hardware Errors": 0,
            }],
            "STATS": [
                {
                    "ID": "BMminer0",
                    "Miner": "bmminer",
                    "CompileTime": "Mon Nov 9 2026",
                    "API": "3.1",
                },
                {
                    "ID": "BMminer1",
                    "Elapsed": 7200,
                    "Chains": 3,
                    "chain_acs1": acs,
                    "chain_acs2": acs,
                    "chain_acs3": acs,
                    "temp1": 66,
                    "temp2": 68,
                    "temp3": 70,
                    "fan1": 4200,
                    "fan2": 4260,
                    "fan3": 4320,
                    "fan4": 4380,
                    "frequency1": 485,
                    "frequency2": 485,
                    "frequency3": 485,
                },
            ],
        },
    }


def system_info_payload() -> dict:
    return {
        "STATUS": [{
            "STATUS": "S", "When": 1700003600, "Code": 0,
            "Msg": "getSystemInfo ok", "Description": "bmminer",
        }],
        "DATA": {
            "gMac": "02:42:ac:11:00:03",
            "gNetType": "DHCP",
            "gHostname": "Antminer",
            "minertype": "Antminer S19",
            "system_version": "1.0.0-mock",
            "filesystem_version": "Fri Sep 27 15:00:00 CST 2024",
        },
    }


_ROUTES = {
    "/cgi-bin/get_miner_status.cgi": miner_status_payload,
    "/cgi-bin/get_system_info.cgi": system_info_payload,
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _challenge(self):
        body = b"Unauthorized"
        self.send_response(401)
        self.send_header(
            "WWW-Authenticate",
            f'Digest realm="{REALM}", nonce="{NONCE}", qop="auth", '
            f'opaque="{OPAQUE}", algorithm=MD5')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Digest ") or not _check_digest(
                auth[len("Digest "):], "GET", self.path):
            self._challenge()
            return
        if self.path == "/cgi-bin/reboot.cgi":
            _record_reboot()
            body = b"<html><body>Rebooting...</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        payload_fn = _ROUTES.get(self.path)
        if payload_fn is None:
            body = b"not found"
            self.send_response(404)
        else:
            body = json.dumps(payload_fn()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"mock stock bitmain listening on {HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
