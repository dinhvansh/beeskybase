#!/usr/bin/env python3
"""Fake Auradine (Teraflux) miner — cgminer RPC on 4028 + web API :8080.

Speaks the contract in docs/vendor-docs2-mapping.md §1, built from
asic-rs ``asic-rs-firmwares/auradine`` (RPC + web backends, real
test-JSON fixtures — the replies below are those fixtures verbatim)
and pyasic (``backends/auradine.py``, ``web/auradine.py``,
``rpc/gcminer.py``), which agree on transport, auth and every
control body:

  * RPC `version` -> STATUS Description "GCMiner-0.5-devsbXXX",
    VERSION GCMiner "0.5" — the detection fingerprint
    ("gcminer"/"fluxos", case-insensitive, D-AU1);
  * RPC `summary` -> MHS 5s/av (the fixture's magnitudes look
    like a dev unit — U-AU3 — but the UNITS are MH/s per the
    cgminer convention and both libraries agree);
  * RPC `devs` -> 3 ASICBoards (ID 1-3, temps 28.25/29.06/30.12);
    `asccount` -> AsicCount 396 / BoardCount 3 (132 chips/board);
    `pools` -> 3 pools (first Alive, rest Dead);
  * RPC `devdetails` -> CONSTRUCTED (no fixture exists in
    asic-rs; the field path /DEVDETAILS/0/Model is asic-rs's
    get_model, the value "AT1500" is the ipreport fixture's
    model — see the mapping doc);
  * Web POST /token {"command": "token", "user": "admin",
    "password": "admin"} -> token at /Token/0/Token ("mock-token"
    here); every other web call needs the `Token` header.
    Wrong credentials -> HTTP 401, no token.
  * Web GET /ipreport, /fan, /psu, /temperature, /voltage,
    /frequency, /led, /mode -> the asic-rs fixtures verbatim
    (ipreport: hostname "teraflux-01", mac 1c:00:00:0e:3b:2b,
    model AT1500, SerialNo AU23200006; fan: 4 fans ~7020-7100
    rpm; psu: PowerIn "58.94W"; temperature: ChipTemp entries
    all > 0, BoardTemp 20.5-47.5 C).
  * Web POST /restart (no params = full reboot; param "gcminer"
    = mining restart), /mode {"sleep": "on"/"off"} and
    {"mode": "custom", "tune": "power", "power": <watts>},
    /led {"code": 3|2}, /updatepools {"pools": [{url, user,
    pass}]} -> STATUS S. Bodies are logged for assertion.
  * With env MOCK_AURADINE_EXPIRE_ONCE=1 the first non-token
    web request answers 401, exercising the client's one
    re-auth-and-retry (asic-rs web.rs).

Every received command / request line is appended to the file
named by env MOCK_AURADINE_LOG (when set) so tests can assert
what the scanner did (reads never POST a write) and the exact
body each action sent.

Run:  python3 tests/mock_auradine.py [host] [rpc_port] [web_port]
"""

import json
import os
import socketserver
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
RPC_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 14034
WEB_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 18085
LOG = os.environ.get("MOCK_AURADINE_LOG")
EXPIRE_ONCE = os.environ.get("MOCK_AURADINE_EXPIRE_ONCE") == "1"
TOKEN = "mock-token"


def _log(line: str) -> None:
    if LOG:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def _status(code: int, msg: str, description: str,
            status: str = "S") -> dict:
    return {"STATUS": [{"STATUS": status, "When": 1700000000,
                        "Code": code, "Msg": msg,
                        "Description": description}],
            "id": 1}


# --- RPC fixtures (asic-rs test JSON, verbatim) ---------------------------

VERSION_REPLY = {
    "STATUS": [{"Code": 22, "Description": "GCMiner-0.5-devsbXXX",
                "Msg": "GCMiner versions", "STATUS": "S",
                "When": 1647971699}],
    "VERSION": [{"API": "1.0", "GCMiner": "0.5"}],
    "id": 1,
}

SUMMARY_REPLY = {
    "STATUS": [{"Code": 11, "Description": "GCMiner-0.5-devsbXXX",
                "Msg": "Summary", "STATUS": "S", "When": 1708622703}],
    "SUMMARY": [{"Accepted": 3310, "Difficulty Accepted": 829210624,
                 "Difficulty Rejected": 32768, "Difficulty Stale": 0,
                 "Discarded": 0, "Elapsed": 56696,
                 "Hardware Errors": 0, "Last getwork": 0,
                 "MHS 15m": 8245002.419711528,
                 "MHS 1m": 10256844.54901739,
                 "MHS 5m": 8778584.71373768,
                 "MHS 5s": 20599767.1774699,
                 "MHS av": 7970630.042671183,
                 "Network Blocks": 0, "Pool Rejected%": 0.0,
                 "Pool Stale%": 0.0, "Rejected": 1,
                 "Remote Failures": 0, "Stale": 0,
                 "Total MH": 451890758070, "Utility": 3.5035376205973425,
                 "Work Utility": 0}],
    "id": 1,
}

DEVS_REPLY = {
    "DEVS": [
        {"DEV": 1, "Enabled": True, "ID": 1, "MHS 5s": 6800000.0,
         "Name": "ASICBoard", "Status": "Alive",
         "Temperature": 28.25},
        {"DEV": 2, "Enabled": True, "ID": 2, "MHS 5s": 6900000.0,
         "Name": "ASICBoard", "Status": "Alive",
         "Temperature": 29.06},
        {"DEV": 3, "Enabled": True, "ID": 3, "MHS 5s": 7000000.0,
         "Name": "ASICBoard", "Status": "Alive",
         "Temperature": 30.12},
    ],
    "STATUS": [{"Code": 9,
                "Description": "GCMiner-2023-05.24-0ce5e7cc93a3815240"
                               "fa189d0beb44b8c834936c",
                "Msg": "3 Dev(s)", "STATUS": "S", "When": 1685118068}],
    "id": 1,
}

ASCCOUNT_REPLY = {
    "ASCCount": [{"AsicCount": 396, "BoardCount": 3}],
    "STATUS": [{"Code": 104,
                "Description": "FluxOS-2024-06.11-d37c5dd4a7f8e4837"
                               "e63dc99e577620cb5e9361d",
                "Msg": "ASC count", "STATUS": "S", "When": 1708622703}],
    "id": 1,
}

POOLS_REPLY = {
    "POOLS": [
        {"Accepted": 10, "POOL": 0, "Priority": 0, "Quota": 1,
         "Rejected": 1, "Status": "Alive", "Stratum Active": True,
         "URL": "stratum+tcp://btc.viabtc.io:3333",
         "User": "username.suffix"},
        {"Accepted": 0, "POOL": 1, "Priority": 1, "Quota": 1,
         "Rejected": 0, "Status": "Dead", "Stratum Active": False,
         "URL": "stratum+tcp://stratum.slushpool.com:3333",
         "User": "username.suffix"},
        {"Accepted": 0, "POOL": 2, "Priority": 2, "Quota": 1,
         "Rejected": 0, "Status": "Dead", "Stratum Active": False,
         "URL": "stratum+tcp://stratum.slushpool.com:3333",
         "User": "username.suffix"},
    ],
    "STATUS": [{"Code": 7, "Description": "GCMiner-0.5-devsbXXX",
                "Msg": "3 Pool(s)", "STATUS": "S", "When": 1647971699}],
    "id": 1,
}

# CONSTRUCTED (see module docstring): only the field the client
# reads — /DEVDETAILS/0/Model — with the ipreport fixture's value.
DEVDETAILS_REPLY = {
    "STATUS": [{"Code": 9, "Description": "GCMiner-0.5-devsbXXX",
                "Msg": "Device details", "STATUS": "S",
                "When": 1708622703}],
    "DEVDETAILS": [{"Model": "AT1500"}],
    "id": 1,
}

_RPC_REPLIES = {
    "version": VERSION_REPLY,
    "summary": SUMMARY_REPLY,
    "devs": DEVS_REPLY,
    "asccount": ASCCOUNT_REPLY,
    "pools": POOLS_REPLY,
    "devdetails": DEVDETAILS_REPLY,
}


# --- Web fixtures (asic-rs test JSON, verbatim) ---------------------------

IPREPORT_REPLY = {
    "IPReport": [{"CBSerialNo": "AU23200006",
                  "ChassisSerialNo": "000020",
                  "HBSerialNo": ["QAHB01230908001X",
                                 "QAHB01230908001Y",
                                 "QAHB01230908001Z"],
                  "InternalType": "T0", "SerialNo": "AU23200006",
                  "command": "ipreport", "hostname": "teraflux-01",
                  "ip": "192.168.1.50", "mac": "1c:00:00:0e:3b:2b",
                  "model": "AT1500", "version": "2023-12.27"}],
    "STATUS": [{"Code": 620,
                "Description": "FluxOS-2023-12.27-9bf070ee4408866329"
                               "c93a70f2dfdc6248938aaa",
                "Msg": "IP Report", "STATUS": "S", "When": 1703711730}],
    "id": 1,
}

FAN_REPLY = {
    "Fan": [{"ID": 1, "Max": 7700, "Speed": 7080, "Target": 7000},
            {"ID": 2, "Max": 7700, "Speed": 7020, "Target": 7000},
            {"ID": 3, "Max": 7700, "Speed": 7100, "Target": 7000},
            {"ID": 4, "Max": 7700, "Speed": 7020, "Target": 7000}],
    "STATUS": [{"Code": 510,
                "Description": "GCMiner-2023-05.24-0ce5e7cc93a3815240"
                               "fa189d0beb44b8c834936c",
                "Msg": "Total fans: 4", "STATUS": "S",
                "When": 1685118277}],
    "id": 1,
}

PSU_REPLY = {
    "PSU": [{"FanSpeed1": "4052.00 RPM",
             "FanSpeed2": "4144.00 RPM", "Iin": "0.28A",
             "Iout": "0.00A", "PoutMax": "3452.00W",
             "PowerIn": "58.94W", "PowerOut": "0.00W",
             "Vin": "245.00V", "Vout": "11.53V",
             "VoutSet": "11.50V"}],
    "STATUS": [{"Code": 570,
                "Description": "GCMiner-2023-04.14-a2b42b45e25194dcd"
                               "f799c07cbb51d18c6c7ed51",
                "Msg": "PSU status", "STATUS": "S", "When": 1681497182}],
    "id": 1,
}

TEMPERATURE_REPLY = {
    "STATUS": [{"Code": 590, "Description": "2.2.0",
                "Msg": "System temperature", "STATUS": "S",
                "When": 1775782219}],
    "Temperature": [
        {"BoardTemp": [{"ID": 0, "Temperature": 24.9375}],
         "ChipTemp": None, "ID": 0, "Name": "Control Board"},
        {"BoardTemp": [{"ID": 0, "Temperature": 21.5},
                       {"ID": 1, "Temperature": 20.5},
                       {"ID": 2, "Temperature": 22.5},
                       {"ID": 3, "Temperature": 41.5},
                       {"ID": 4, "Temperature": 41.0}],
         "ChipTemp": [{"ID": 0, "Temperature": 45.827271728515655},
                      {"ID": 1, "Temperature": 45.827271728515655},
                      {"ID": 2, "Temperature": 45.029410400390645}],
         "ID": 1, "Name": "Hash Board 1"},
        {"BoardTemp": [{"ID": 0, "Temperature": 22.0},
                       {"ID": 1, "Temperature": 21.5},
                       {"ID": 2, "Temperature": 23.0},
                       {"ID": 3, "Temperature": 43.0},
                       {"ID": 4, "Temperature": 42.5}],
         "ChipTemp": [{"ID": 0, "Temperature": 44.43101440429689},
                      {"ID": 1, "Temperature": 46.22620239257816},
                      {"ID": 2, "Temperature": 48.220855712890625}],
         "ID": 2, "Name": "Hash Board 2"},
        {"BoardTemp": [{"ID": 0, "Temperature": 23.0},
                       {"ID": 1, "Temperature": 22.5},
                       {"ID": 2, "Temperature": 22.0},
                       {"ID": 3, "Temperature": 47.5},
                       {"ID": 4, "Temperature": 45.0}],
         "ChipTemp": [{"ID": 0, "Temperature": 51.41230102539066},
                      {"ID": 1, "Temperature": 50.21550903320315},
                      {"ID": 2, "Temperature": 50.21550903320315}],
         "ID": 3, "Name": "Hash Board 3"},
    ],
    "id": 1,
}

VOLTAGE_REPLY = {
    "STATUS": [{"Code": 630, "Description": "2.2.0",
                "Msg": "System voltage", "STATUS": "S",
                "When": 1775782219}],
    "Voltage": [
        {"ChipVoltage": [{"ID": 0, "Voltage": 0.23929554013739107},
                         {"ID": 1, "Voltage": 0.24232864508667262},
                         {"ID": 2, "Voltage": 0.2405087821171037}],
         "ID": 1, "Name": "Hash Board 1"},
        {"ChipVoltage": [{"ID": 0, "Voltage": 0.2452606465376448},
                         {"ID": 1, "Voltage": 0.2464738885173574},
                         {"ID": 2, "Voltage": 0.2457661640291917}],
         "ID": 2, "Name": "Hash Board 2"},
        {"ChipVoltage": [{"ID": 0, "Voltage": 0.24890037247678265},
                         {"ID": 1, "Voltage": 0.24879926897847326},
                         {"ID": 2, "Voltage": 0.24890037247678265}],
         "ID": 3, "Name": "Hash Board 3"},
    ],
    "id": 1,
}

FREQUENCY_REPLY = {
    "Frequency": [
        {"ChipFrequency": [{"Frequency": 281.25, "ID": 0},
                           {"Frequency": 247.5, "ID": 1},
                           {"Frequency": 268.75, "ID": 2}],
         "ID": 1, "Name": "Hash Board 1"},
        {"ChipFrequency": [{"Frequency": 327.5, "ID": 0},
                           {"Frequency": 323.75, "ID": 1},
                           {"Frequency": 328.75, "ID": 2}],
         "ID": 2, "Name": "Hash Board 2"},
        {"ChipFrequency": [{"Frequency": 391.25, "ID": 0},
                           {"Frequency": 352.5, "ID": 1},
                           {"Frequency": 166.25, "ID": 2}],
         "ID": 3, "Name": "Hash Board 3"},
    ],
    "STATUS": [{"Code": 640, "Description": "2.2.0",
                "Msg": "System frequency", "STATUS": "S",
                "When": 1775782219}],
    "id": 1,
}

LED_REPLY = {
    "LED": [{"Code": 2, "LED1": 1, "LED2": 1, "Msg": "Normal"}],
    "STATUS": [{"Code": 530,
                "Description": "GCMiner-2022-12.21-38b82d1466eedb60"
                               "9a7920339f8baa83b78a93c2",
                "Msg": "Total LEDs 2", "STATUS": "S",
                "When": 1671667240}],
    "id": 1,
}

MODE_REPLY = {
    "Mode": [{"Mode": "custom", "Power": 2000, "Sleep": "off",
              "Ths": 160}],
    "STATUS": [{"Code": 540,
                "Description": "FluxOS-2023-12.27-9bf070ee4408866329"
                               "c93a70f2dfdc6248938aaa",
                "Msg": "Operating mode: 'normal', sleep: 'false'",
                "STATUS": "S", "When": 1703715266}],
    "id": 1,
}

_WEB_GETS = {
    "ipreport": IPREPORT_REPLY,
    "fan": FAN_REPLY,
    "psu": PSU_REPLY,
    "temperature": TEMPERATURE_REPLY,
    "voltage": VOLTAGE_REPLY,
    "frequency": FREQUENCY_REPLY,
    "led": LED_REPLY,
    "mode": MODE_REPLY,
}


# --- RPC server -------------------------------------------------------------

class RpcHandler(socketserver.BaseRequestHandler):
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
            req = json.loads(data.decode("utf-8", errors="replace"))
            command = req.get("command", "")
            parameter = req.get("parameter")
        except json.JSONDecodeError:
            command, parameter = "", None
        _log(f"RPC {command}"
             + (f" {json.dumps(parameter)}" if parameter is not None
                else ""))
        reply = _RPC_REPLIES.get(command)
        if reply is None:
            payload = {"STATUS": [{"STATUS": "E", "Code": 14,
                                   "Msg": f"Invalid command: {command}"}],
                       "id": 1}
        else:
            payload = reply
        try:
            # cgminer replies end with a trailing NUL byte.
            self.request.sendall(json.dumps(payload).encode() + b"\x00")
        except OSError:
            pass


class RpcServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


# --- Web server -------------------------------------------------------------

_expired_once = {"done": False}


class WebHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep test output clean
        pass

    def _send_json(self, code: int, payload: dict,
                   headers: dict | None = None) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(raw)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            parsed = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError:
            parsed = {}
        return parsed if isinstance(parsed, dict) else {}

    def _unauthorised(self, why: str) -> None:
        self._send_json(401, _status(401, why,
                                     "GCMiner-0.5-devsbXXX", "E"))

    def _check_token(self) -> bool:
        if EXPIRE_ONCE and not _expired_once["done"]:
            _expired_once["done"] = True
            return False
        return self.headers.get("Token") == TOKEN

    def do_GET(self):
        command = urlparse(self.path).path.strip("/")
        _log(f"WEB GET /{command}")
        if command not in _WEB_GETS:
            self._send_json(404, {"error": f"unknown command {command}"})
            return
        if not self._check_token():
            self._unauthorised("token expired")
            return
        self._send_json(200, _WEB_GETS[command])

    def do_POST(self):
        command = urlparse(self.path).path.strip("/")
        body = self._read_body()
        _log(f"WEB POST /{command} {json.dumps(body, sort_keys=True)}")
        if command == "token":
            if body.get("user") == "admin" \
                    and body.get("password") == "admin":
                self._send_json(200, {
                    "Token": [{"Token": TOKEN}],
                    "STATUS": [{"STATUS": "S", "Code": 200,
                                "Msg": "Token created",
                                "Description": "GCMiner-0.5-devsbXXX"}],
                    "id": 1,
                })
            else:
                self._unauthorised("bad credentials")
            return
        if not self._check_token():
            self._unauthorised("token expired")
            return
        if command in ("restart", "mode", "led", "updatepools"):
            self._send_json(200, _status(
                200, "OK", "GCMiner-0.5-devsbXXX"))
            return
        self._send_json(404, {"error": f"unknown command {command}"})


def main() -> None:
    rpc = RpcServer((HOST, RPC_PORT), RpcHandler)
    thread = threading.Thread(target=rpc.serve_forever, daemon=True)
    thread.start()
    web = ThreadingHTTPServer((HOST, WEB_PORT), WebHandler)
    try:
        web.serve_forever()
    finally:
        rpc.shutdown()


if __name__ == "__main__":
    main()
