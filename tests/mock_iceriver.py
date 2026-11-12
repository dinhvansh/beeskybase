#!/usr/bin/env python3
"""Fake IceRiver — the web API on port 80.

Speaks the contract in docs/vendor-oss-mapping.md §2, built from
pyasic's IceRiverWebAPI and the real captured KS0 Ultra packet
(HackMD, owner-published 2024-06-30), reproduced here verbatim
except for the IP (127.0.0.1) and the clock:

  * GET / -> a console page whose title is
    ``<TITLE>用户界面</TITLE>`` (pyasic's factory fingerprint);
  * POST /user/loginpost?post=6&user=admin&pwd=... -> {"error": 0}
    and sets a session cookie (the API needs no token per the
    HackMD note; login is best-effort);
  * POST /user/userpanel?post=4 -> the KS0 Ultra status JSON:
    softver1 "ICM168_3_2_14_ks0ultra_miner", rtpow "359G",
    unit "G", runtime "00:01:15:16", fans [6079, 6079, 0, 0],
    one board (chipnum 18, intmp 48, outtmp 37), three pools
    (one Alive with 281 accepted), mac 00:0a:66:30:00:6d.
    With env MOCK_ICERIVER_WRAPPED=1 the same data is served
    under the {"userpanel": {"data": ...}} wrapper pyasic's
    backend reads (mapping U-I1 — BeeSky accepts both shapes);
  * POST /user/userpanel?post=5&locate=1|0 -> {"error": 0}
    (pyasic's locate); GET is accepted for userpanel too, as
    the HackMD author called it.
  * A wrong password on loginpost still returns error 0 (the
    endpoint does not enforce the UI password — the HackMD
    finding); the panel itself is what the shape gate checks.

Every request line is appended to the file named by env
MOCK_ICERIVER_LOG (when set) so tests can assert what the
scanner did (login before panel, cookie forwarded) and did NOT
do (no machineconfig writes).

Run:  python3 tests/mock_iceriver.py [host] [port]
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 18082
LOG = os.environ.get("MOCK_ICERIVER_LOG")
WRAPPED = os.environ.get("MOCK_ICERIVER_WRAPPED") == "1"

CONSOLE_PAGE = (
    "<html><head><TITLE>用户界面</TITLE></head>"
    "<body>ICERIVER Console</body></html>"
)

# The HackMD KS0 Ultra packet, verbatim (IP adapted to this mock).
PANEL_DATA = {
    "model": "none", "algo": "none", "online": True,
    "firmver1": "BOOT_3_3", "firmver2": "image_1.0",
    "softver1": "ICM168_3_2_14_ks0ultra_miner",
    "softver2": "ICM168_3_2_14_ks0ultra_bg",
    "firmtype": "Factory", "nic": "eth0",
    "mac": "00:0a:66:30:00:6d", "ip": "127.0.0.1",
    "netmask": "255.255.255.0", "host": "ICERIVER",
    "dhcp": True, "gateway": "127.0.0.1", "dns": "127.0.0.1",
    "locate": 0, "rtpow": "359G", "avgpow": "375G",
    "reject": 0.0, "runtime": "00:01:15:16", "unit": "G",
    "pows": {"board1": [0, 230, 282, 364, 377, 361, 395, 417,
                        350, 362, 397, 357, 382, 397, 359,
                        -1, -1, -1, -1, -1, -1, -1, -1]},
    "pows_x": ["0 mins", "5 mins", "10 mins"],
    "powstate": True, "netstate": True, "fanstate": True,
    "tempstate": True, "fans": [6079, 6079, 0, 0],
    "pools": [
        {"no": 1.0, "addr": "stratum+tcp://kas-asia.f2pool.com:1400",
         "user": "kwl88347.001", "pass": "21235365876986800",
         "connect": -1.0, "diff": "0.00G", "priority": 1.0,
         "accepted": 0.0, "rejected": 0.0, "diffa": 0.0,
         "diffr": 0.0, "state": 0.0, "lsdiff": 0.0,
         "lstime": "00:00:00"},
        {"no": 2.0, "addr": "stratum+tcp://kas-asia.f2pool.com:1430",
         "user": "kwl88347.002", "pass": "",
         "connect": 1.0, "diff": "8796.09G", "priority": 2.0,
         "accepted": 281.0, "rejected": 0.0, "diffa": 0.0,
         "diffr": 0.0, "state": 1.0, "lsdiff": 0.0,
         "lstime": "00:00:00"},
        {"no": 3.0, "addr": "stratum+tcp://kas-euro.f2pool.com:1400",
         "user": "kwl88347.003", "pass": "",
         "connect": -1.0, "diff": "0.00G", "priority": 3.0,
         "accepted": 0.0, "rejected": 0.0, "diffa": 0.0,
         "diffr": 0.0, "state": 0.0, "lsdiff": 0.0,
         "lstime": "00:00:00"},
    ],
    "boards": [
        {"no": 1.0, "chipnum": 18.0, "chipsuc": 0.0,
         "error": 0.0, "freq": 875.0, "rtpow": "359.17G",
         "avgpow": "376.28G", "idealpow": "0.00G",
         "tempnum": "(null)", "pcbtemp": "0.00-0.00-0.00-0.00",
         "intmp": 48.0, "outtmp": 37.0, "state": True,
         "false": list(range(1, 19))},
    ],
    "refTime": "2024-06-30 07:07:42 UTC",
}


def _log(line: str) -> None:
    if LOG:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep test output clean
        pass

    def _send_json(self, payload: dict, cookie: str | None = None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        cookie = self.headers.get("Cookie") or ""
        _log(f"{self.command} {parsed.path} "
             f"post={query.get('post', [''])[0]} "
             f"cookie={'yes' if cookie else 'no'}")
        if parsed.path == "/" and self.command == "GET":
            self._send_text(CONSOLE_PAGE)
            return
        if parsed.path == "/user/loginpost":
            # The UI password is not enforced on the API (HackMD);
            # login always succeeds and sets a session cookie.
            self._send_json({"error": 0, "message": ""},
                            cookie="session=iceriver-mock; Path=/")
            return
        if parsed.path == "/user/userpanel":
            post = query.get("post", [""])[0]
            if post == "4":
                if WRAPPED:
                    payload = {"error": 0,
                               "userpanel": {"data": PANEL_DATA},
                               "message": ""}
                else:
                    payload = {"error": 0, "data": PANEL_DATA,
                               "message": ""}
                self._send_json(payload)
                return
            if post == "5":
                locate = query.get("locate", [""])[0]
                if locate in ("0", "1"):
                    self._send_json({"error": 0, "message": ""})
                    return
            self._send_json({"error": 1, "message": "bad post"},
                            )
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        self._handle()

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        self._handle()


class Server(ThreadingHTTPServer):
    # Set BEFORE bind: tests respawn this mock on the same port
    # (wrapped-shape variant) and a listener without SO_REUSEADDR
    # cannot rebind while the previous run's connections sit in
    # TIME_WAIT.
    allow_reuse_address = True


def main():
    server = Server((HOST, PORT), Handler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
