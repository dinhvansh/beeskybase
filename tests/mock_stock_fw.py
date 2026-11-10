#!/usr/bin/env python3
"""Fake stock-firmware miner for the v0.11 firmware tests.

Digest-auth (root/root, RFC 7616 verified) like mock_bitmain.py, plus
the firmware surface BeeSky v0.11 talks to:

  GET  /cgi-bin/get_miner_status.cgi — cgminer-shaped status (probe)
  GET  /cgi-bin/get_system_info.cgi  — {"DATA": {"minertype": ...}}
  GET  /cgi-bin/miner_type.cgi       — plain text "Antminer S19 Pro"
  POST /cgi-bin/upgrade.cgi          — multipart upload; every upload is
      logged as ``upload:<filename>:<sha256hex>``. An upload of
      ``update_first.bmu`` BLOCKS until the marker file named by
      BEESKY_MOCK_FW_MARKER exists (up to 10 s) — that mimics the real
      miner spending its time verifying the signature, which is exactly
      the window the unlock race shoots into.
  GET  /cgi-bin/patch_success.cgi    — 200 only once BOTH .bmu uploads
      were seen AND the marker file exists; 404 otherwise.

Every HTTP request (even 401 challenges) is appended as one line to the
file named by BEESKY_MOCK_FW_LOG, so the test can count requests (the
gated unlock must produce ZERO) and assert the cross-process event
order (the fake ssh shim appends ``ssh:...`` lines to the same file).

Run directly:  python3 tests/mock_stock_fw.py [host] [port]
"""

import hashlib
import json
import os
import re
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.5"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 80
LOG_PATH = os.environ.get("BEESKY_MOCK_FW_LOG")
MARKER_PATH = os.environ.get("BEESKY_MOCK_FW_MARKER")

USERNAME = "root"
PASSWORD = "root"
REALM = "WebAdmin"
NONCE = secrets.token_hex(16)
OPAQUE = "beesky-mock-fw"

_LOCK = threading.Lock()
_UPLOADS: list[str] = []  # filenames, in arrival order


def _log(line: str) -> None:
    if not LOG_PATH:
        return
    with _LOCK:
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")


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


def _parse_multipart(headers, body: bytes):
    """Crude multipart reader: (filename, file_bytes) of the file part."""
    match = re.search(r"boundary=([^;]+)", headers.get("Content-Type", ""))
    if not match:
        return None, b""
    boundary = match.group(1).strip().strip('"').encode()
    for part in body.split(b"--" + boundary):
        if b"filename=" not in part:
            continue
        name_match = re.search(rb'filename="([^"]*)"', part)
        _head, _, rest = part.partition(b"\r\n\r\n")
        if rest.endswith(b"\r\n"):
            rest = rest[:-2]
        return (name_match.group(1).decode() if name_match else None), rest
    return None, b""


def miner_status_payload() -> dict:
    acs = "o" * 114
    return {
        "STATUS": [{"STATUS": "S", "When": 1700003600, "Code": 0,
                    "Msg": "getMinerStatus ok", "Description": "bmminer"}],
        "DATA": {
            "SUMMARY": [{"Elapsed": 7200, "GHS 5s": 110000.0,
                         "GHS av": 110000.0, "Type": "Antminer S19 Pro"}],
            "STATS": [
                {"ID": "BMminer0", "Miner": "bmminer", "API": "3.1"},
                {"ID": "BMminer1", "Elapsed": 7200, "Chains": 3,
                 "chain_acs1": acs, "chain_acs2": acs, "chain_acs3": acs,
                 "temp1": 66, "temp2": 68, "temp3": 70,
                 "fan1": 4200, "fan2": 4260, "fan3": 4320, "fan4": 4380},
            ],
        },
    }


def system_info_payload() -> dict:
    return {"DATA": {"minertype": "Antminer S19 Pro",
                     "system_version": "1.0.0-mock-fw"}}


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

    def _authed(self, method: str) -> bool:
        auth = self.headers.get("Authorization", "")
        return auth.startswith("Digest ") and _check_digest(
            auth[len("Digest "):], method, self.path)

    def _send(self, code: int, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        _log(f"http:GET {self.path}")
        if not self._authed("GET"):
            self._challenge()
            return
        if self.path == "/cgi-bin/get_miner_status.cgi":
            self._send(200, json.dumps(miner_status_payload()).encode(),
                       "application/json")
        elif self.path == "/cgi-bin/get_system_info.cgi":
            self._send(200, json.dumps(system_info_payload()).encode(),
                       "application/json")
        elif self.path == "/cgi-bin/miner_type.cgi":
            self._send(200, b"Antminer S19 Pro\n", "text/plain")
        elif self.path == "/cgi-bin/patch_success.cgi":
            complete = {"update_first.bmu", "update_second.bmu"} <= \
                set(_UPLOADS) and bool(
                    MARKER_PATH and Path(MARKER_PATH).exists())
            if complete:
                _log("http:patch_success:ok")
                self._send(200, b"patch success", "text/plain")
            else:
                self._send(404, b"no patch marker", "text/plain")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        _log(f"http:POST {self.path}")
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        body = self.rfile.read(length) if length > 0 else b""
        if not self._authed("POST"):
            self._challenge()
            return
        if self.path != "/cgi-bin/upgrade.cgi":
            self._send(404, b"not found", "text/plain")
            return
        filename, content = _parse_multipart(self.headers, body)
        digest = hashlib.sha256(content).hexdigest()
        with _LOCK:
            _UPLOADS.append(filename or "")
        _log(f"upload:{filename}:{digest}")
        if filename == "update_first.bmu":
            # The "signature verification" window: hold the response
            # until the race's kill lands (marker file) or 10 s pass.
            waited = 0.0
            hit = False
            while waited < 10.0:
                if MARKER_PATH and Path(MARKER_PATH).exists():
                    hit = True
                    break
                time.sleep(0.05)
                waited += 0.05
            _log(f"first-upload-window:{'marker' if hit else 'timeout'}")
        self._send(200, b"<html><body>upgrade accepted</body></html>",
                   "text/html")


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"mock stock fw listening on {HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
