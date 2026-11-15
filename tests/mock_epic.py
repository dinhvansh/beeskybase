#!/usr/bin/env python3
"""Fake ePIC miner — the HTTP JSON API on port 4028.

Speaks the contract in docs/epic-mapping.md, built from Epic's
own published material (docs/APIv2.md + docs/APIv3.md) and the
dashboard's connection code (src/portscan.js, src/app.jsx
handleApi, src/tabs/ControlTab.jsx, src/tabs/FanTab.jsx):

  * GET /summary -> the doc-shaped status JSON: Hostname
    "epicminer30032518" (README's example), Session Average
    MHs 8500.5 with LastAverageMHs 8490.0, Uptime 90000 s,
    Accepted 123456 / Rejected 123, three HBs (Index 0-2,
    Temperature 62/68/65, Input Power 1100/1080/1120 W,
    Core Clock [500.0, 525.0]), Fans Speed 80 (%),
    StratumConfigs (2 pools, first current + connected),
    Mining Coin "BTC", PresetInfo "Balanced" @ 3300 W,
    Misc Locate Miner State false, Append Unique Id false.
    All values are synthetic — the docs only ever show
    <placeholders> (mapping U-E1) — but the SHAPES are the
    docs' own, and the control bodies are the dashboard's.
  * GET /capabilities -> Model "SC200" (APIv2's machine),
    Presets Eco/Balanced/Turbo with power levels, Coins
    BTC/BCH, v3 Display + Tune Presets + Temp Sensor Info
    + Psu Info.
  * POST /reboot, /softreboot, /miner, /identify, /fanspeed,
    /mode, /coin, /password, /power, /shutdowntemp, /tune ->
    {"result": true, "error": null} when the password is the
    factory default "letmein" (README), else
    {"result": false, "error": "wrong password"}. The /miner
    call only accepts param "stop" (the only value the
    dashboard ever sends — mapping U-E3); /fanspeed accepts
    an int 1-100 (the dashboard sends a number, D-E2);
    /tune accepts {"clks": "<MHz>", "voltage": "<mV>"} as
    strings (app.jsx /tune case); /coin accepts the
    dashboard's body incl. pool_url/login (D-E1).
  * Any other path -> 404 JSON. Non-HTTP bytes on the socket
    (the Whatsminer/cgminer probes) get the stdlib server's
    400 and the connection closes — exactly what a real
    ePIC HTTP server does to a text-protocol probe.

Every request line is appended to the file named by env
MOCK_EPIC_LOG (when set) so tests can assert what the
scanner did (reads never POST) and what each action sent.

Run:  python3 tests/mock_epic.py [host] [port]
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 14031
LOG = os.environ.get("MOCK_EPIC_LOG")
PASSWORD = "letmein"

SUMMARY = {
    "Status": {
        "Operating State": "Mining",
        "Last Command": "",
        "Last Command Result": "",
    },
    "Hostname": "epicminer30032518",
    "PresetInfo": {"Preset": "Balanced", "Target Power": 3300},
    "Software": "ePIC-Miner 4.0.0",
    "Mining": {"Coin": "BTC", "Algorithm": "SHA256"},
    "Stratum": {
        "Current Pool": "stratum+tcp://pool.example.com:3333",
        "Current User": "wallet123.worker001",
        "IsPoolConnected": True,
        "Average Latency": 42.5,
    },
    "Session": {
        "Startup Timestamp": 1762819200,
        "Startup String": "2026-11-11 00:00:00",
        "Uptime": 90000,
        "Last Work Timestamp": 1762909200,
        "WorkReceived": 1000,
        "Active HBs": 3,
        "Average MHs": 8500.5,
        "LastAverageMHs": {"Hashrate": 8490.0,
                           "Timestamp": 1762909200},
        "Accepted": 123456,
        "Rejected": 123,
        "Submitted": 123579,
        "Last Accepted Share Timestamp": 1762909190,
        "Difficulty": 123456.0,
    },
    "HBs": [
        {"Index": 0, "Input Voltage": 12.1, "Output Voltage": 12.0,
         "Input Current": 90.9, "Output Current": 87.5,
         "Input Power": 1100.0, "Output Power": 1050.0,
         "Temperature": 62, "Core Clock": [500.0, 525.0]},
        {"Index": 1, "Input Voltage": 12.1, "Output Voltage": 12.0,
         "Input Current": 89.3, "Output Current": 86.0,
         "Input Power": 1080.0, "Output Power": 1032.0,
         "Temperature": 68, "Core Clock": [500.0, 525.0]},
        {"Index": 2, "Input Voltage": 12.2, "Output Voltage": 12.0,
         "Input Current": 91.8, "Output Current": 88.4,
         "Input Power": 1120.0, "Output Power": 1060.0,
         "Temperature": 65, "Core Clock": [500.0, 525.0]},
    ],
    "Fans": {"Fans Speed": 80},
    "Misc": {"Locate Miner State": False,
             "Append Unique Id To Worker": False},
    "StratumConfigs": [
        {"pool": "stratum+tcp://pool.example.com:3333",
         "login": "wallet123.worker001", "password": "x"},
        {"pool": "stratum+tcp://backup.example.com:3333",
         "login": "wallet123.worker001", "password": "x"},
    ],
}

CAPABILITIES = {
    "Model": "SC200",
    "Presets": ["Eco", "Balanced", "Turbo"],
    "PresetsPowerLevels": {
        "Eco": [800, 1000],
        "Balanced": [1200, 1500, 3300],
        "Turbo": [1800, 2200],
    },
    "Coins": ["BTC", "BCH"],
    "Display": ["ClksAndVoltage", "Fans"],
    "Tune Presets": [
        {"voltage": 12500, "clk": 500, "hashrate": 8500.5,
         "power": 3300},
    ],
    "Temp Sensor Info": {"Type": "onboard", "Count": 3},
    "Psu Info": {"PSU Type": 1, "FW": 2, "Min Vout": 11000,
                 "Max Vout": 13000},
}


def _log(line: str) -> None:
    if LOG:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep test output clean
        pass

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = {}
        if self.command == "POST":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8")) \
                    if raw else {}
            except ValueError:
                body = {}
            if not isinstance(body, dict):
                body = {}
        _log(f"{self.command} {path} "
             f"param={json.dumps(body.get('param'), sort_keys=True)} "
             f"password={'yes' if body.get('password') else 'no'}")
        if self.command == "GET" and path == "/summary":
            self._send_json(SUMMARY)
            return
        if self.command == "GET" and path == "/capabilities":
            self._send_json(CAPABILITIES)
            return
        if self.command == "POST" and path in (
                "/reboot", "/softreboot", "/miner", "/identify",
                "/fanspeed", "/mode", "/coin", "/password",
                "/power", "/shutdowntemp", "/tune"):
            if body.get("password") != PASSWORD:
                self._send_json({"result": False,
                                 "error": "wrong password"})
                return
            param = body.get("param")
            if path == "/miner" and param != "stop":
                # The dashboard only ever sends "stop" (mapping
                # U-E3); anything else is refused like the
                # miner would refuse an unknown command.
                self._send_json(
                    {"result": False,
                     "error": "unknown miner command"})
                return
            if path == "/fanspeed" and not (
                    isinstance(param, int) and 1 <= param <= 100):
                self._send_json(
                    {"result": False,
                     "error": "fan speed must be 1-100"})
                return
            if path == "/tune" and not (
                    isinstance(param, dict)
                    and isinstance(param.get("clks"), str)
                    and isinstance(param.get("voltage"), str)):
                self._send_json(
                    {"result": False,
                     "error": "tune needs clks/voltage strings"})
                return
            if path == "/coin" and not (
                    isinstance(param, dict)
                    and isinstance(param.get("coin"), str)
                    and isinstance(param.get("stratum_configs"), list)
                    and "pool_url" in param and "login" in param):
                self._send_json(
                    {"result": False,
                     "error": "coin needs the dashboard body"})
                return
            self._send_json({"result": True, "error": None})
            return
        self._send_json({"error": "not found"}, status=404)

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()


class Server(ThreadingHTTPServer):
    # Set BEFORE bind: tests respawn this mock on the same port
    # and a listener without SO_REUSEADDR cannot rebind while
    # the previous run's connections sit in TIME_WAIT.
    allow_reuse_address = True


def main():
    server = Server((HOST, PORT), Handler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
