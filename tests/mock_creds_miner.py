#!/usr/bin/env python3
"""Fake miner for the v0.23 multi-credential scan tests.

Two modes (argv[3] or BEESKY_MOCK_CREDS_MODE), both AUTH-GATED with
configurable accepted credentials, both logging every authentication
attempt as a JSON line to the file named by BEESKY_MOCK_CREDS_LOG so
tests can assert WHICH set was tried, in which order:

  dashd — a VNish/dashd whose reads are locked: GET /api/v1/summary
      answers 401 unless the request carries the bearer token minted
      by POST /api/v1/unlock for the accepted password
      (BEESKY_MOCK_CREDS_PW, default "dashd-pw"). Unlock attempts are
      logged as {"kind": "unlock", "pw": ...}. /boards, /info and
      /model answer 404 (the adapter's counts-only fallbacks engage).
      Variant: with BEESKY_MOCK_CREDS_API_KEY set, /summary accepts
      ONLY that x-api-key header (the bearer token no longer opens
      it) — the API-key unlock method. Requests carrying an
      x-api-key are logged as {"kind": "apikey", "key": ...}.

  stock — a Bitmain stock CGI server behind RFC 7616 digest auth
      accepting exactly BEESKY_MOCK_CREDS_USER / BEESKY_MOCK_CREDS_PW
      (defaults "stockuser" / "stockpw"). Every request carrying an
      Authorization header is logged as {"kind": "auth",
      "user": ...} (the digest header carries the username in the
      clear). Status payload mirrors mock_stock_fw.py's, which the
      firmware suites already prove against BitmainClient.

Run:  python3 tests/mock_creds_miner.py [host] [port] [mode]
"""

import hashlib
import json
import os
import re
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 80
MODE = (sys.argv[3] if len(sys.argv) > 3
        else os.environ.get("BEESKY_MOCK_CREDS_MODE", "dashd"))
LOG_PATH = os.environ.get("BEESKY_MOCK_CREDS_LOG")

_LOCK = threading.Lock()


def _log(entry: dict) -> None:
    if not LOG_PATH:
        return
    with _LOCK:
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# dashd mode
# ---------------------------------------------------------------------------

DASHD_TOKEN = "creds-jwt"
DASHD_PW = os.environ.get("BEESKY_MOCK_CREDS_PW", "dashd-pw")
DASHD_API_KEY = os.environ.get("BEESKY_MOCK_CREDS_API_KEY")


def _dashd_summary() -> dict:
    chains = []
    for i in range(3):
        chains.append({
            "id": i,
            "chip_temp": {"min": 55, "max": 62 + i},
            "pcb_temp": {"min": 40, "max": 50},
            "chip_statuses": {"red": 0, "orange": 0, "grey": 114},
            "status": {"state": "mining"},
        })
    return {"miner": {
        "miner_type": "Antminer S19 Pro",
        "hr_realtime": 109.5,
        "hr_average": 109.1,
        "power_consumption": 3200,
        "miner_status": {"miner_state_time": 7200},
        "chains": chains,
        "cooling": {"fans": [{"id": i, "rpm": 4200} for i in range(4)]},
    }}


class DashdHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _send_json(self, code: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/v1/summary":
            key = self.headers.get("x-api-key")
            if key:
                _log({"kind": "apikey", "key": key})
            if DASHD_API_KEY:
                # API-key variant: ONLY the key opens the reads —
                # a minted bearer token does not.
                authed = key == DASHD_API_KEY
            else:
                authed = (
                    self.headers.get("Authorization")
                    == f"Bearer {DASHD_TOKEN}")
            if authed:
                self._send_json(200, _dashd_summary())
            else:
                self._send_json(401, {"err": "unauthorized"})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""
        if self.path == "/api/v1/unlock":
            try:
                pw = json.loads(raw.decode("utf-8") or "{}").get("pw")
            except (UnicodeDecodeError, json.JSONDecodeError):
                pw = None
            _log({"kind": "unlock", "pw": pw})
            if pw == DASHD_PW:
                self._send_json(200, {"token": DASHD_TOKEN})
            else:
                self._send_json(403, {"err": "invalid password"})
            return
        self._send_json(404, {"error": "not found"})


# ---------------------------------------------------------------------------
# stock mode (digest auth, RFC 7616 — mirrors mock_stock_fw.py)
# ---------------------------------------------------------------------------

STOCK_USER = os.environ.get("BEESKY_MOCK_CREDS_USER", "stockuser")
STOCK_PW = os.environ.get("BEESKY_MOCK_CREDS_PW", "stockpw")
REALM = "WebAdmin"
NONCE = secrets.token_hex(16)
OPAQUE = "beesky-mock-creds"


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _check_digest(header: str, method: str, uri: str) -> bool:
    params = {}
    for match in re.finditer(r'(\w+)=(?:"([^"]*)"|([^,\s]+))', header or ""):
        params[match.group(1)] = (
            match.group(2) if match.group(2) is not None else match.group(3))
    if params.get("username") != STOCK_USER or params.get("nonce") != NONCE:
        return False
    if params.get("uri") != uri:
        return False
    ha1 = _md5(f"{STOCK_USER}:{REALM}:{STOCK_PW}")
    ha2 = _md5(f"{method}:{uri}")
    if params.get("qop"):
        expected = _md5(
            f"{ha1}:{NONCE}:{params.get('nc')}:{params.get('cnonce')}"
            f":{params['qop']}:{ha2}")
    else:
        expected = _md5(f"{ha1}:{NONCE}:{ha2}")
    return secrets.compare_digest(expected, params.get("response", ""))


def _stock_status() -> dict:
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


class StockHandler(BaseHTTPRequestHandler):
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

    def _send(self, code: int, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Digest "):
            params = dict(re.findall(r'(\w+)="([^"]*)"', auth))
            _log({"kind": "auth", "user": params.get("username")})
        if not auth.startswith("Digest ") or not _check_digest(
                auth[len("Digest "):], "GET", self.path):
            self._challenge()
            return
        if self.path == "/cgi-bin/get_miner_status.cgi":
            self._send(200, json.dumps(_stock_status()).encode(),
                       "application/json")
        elif self.path == "/cgi-bin/get_system_info.cgi":
            self._send(200, json.dumps(
                {"DATA": {"minertype": "Antminer S19 Pro"}}).encode(),
                "application/json")
        else:
            self._send(404, b"not found", "text/plain")


def main():
    handler = DashdHandler if MODE == "dashd" else StockHandler
    server = ThreadingHTTPServer((HOST, PORT), handler)
    print(f"mock creds miner ({MODE}) listening on {HOST}:{PORT}",
          flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
