#!/usr/bin/env python3
"""Fake SealMiner (Bitdeer) — cgminer RPC on 4028 + web CGI :80.

Speaks the contract in docs/vendor-docs2-mapping.md §2, built
from asic-rs ``asic-rs-firmwares/sealminer`` (RPC 4028 + web CGI
backends, real test-JSON fixtures — the replies below are those
fixtures verbatim) plus the Bitdeer setup guides for the web-UI
facts the code does not state:

  * RPC `version` -> STATUS Description "bdminer 4.11.1",
    VERSION BDMiner "4.11.1" — the detection fingerprint
    ("bdminer", case-insensitive, D-SE1);
  * RPC `summary` -> MHS 5s 368479432.78 / MHS av 206860473.51
    (a realistic A2-class unit);
  * RPC `stats` -> the whole board/PSU picture in one flat
    object: 3 boards x 153 chips, 0 bad chips, Temp 0..3 per
    board (max 70 C), "<n> Speed" fan rpm (Fan Count 4),
    "PSU Input Power" 3504 W, MAC 50:d4:48:4b:86:78,
    "PM State" "Running", "Mining Mode" "Normal",
    "Power Limit" 3500, "Ctrl Board SN" S127200252001850;
  * RPC `devdetails` -> CONSTRUCTED (no fixture exists in
    asic-rs; the field path /DEVDETAILS/0/Model is asic-rs's
    get_model, the value "A2" is the get_system_info
    fixture's miner_type — see the mapping doc);
  * RPC `ascset` -> "0,suspend" answers STATUS S;
    "0,powerlimit,{"value":"<watts>"}" and
    "0,workmode,{"mode": ...}" answer STATUS S + Code 119
    (asic-rs set_tuning_option); malformed tuning params
    answer STATUS E. `restart` answers STATUS S.
  * RPC `updatepools` -> the parameter is a JSON STRING
    {"pools": [{url, user, pass}]} (asic-rs); a parseable
    pools parameter answers STATUS S.
  * Web POST /cgi-bin/login.php (form
    username=seal&origin_pwd=seal + X-Requested-With) ->
    session cookie "session=seal-mock". Wrong credentials ->
    200 with no set-cookie (asic-rs: "No session cookie in
    login response").
  * Web GET /cgi-bin/get_system_info.php and
    /cgi-bin/miner_psu_status.php -> the asic-rs fixtures
    verbatim (miner_type "A2", firmware 2025091001, PSU
    Power 3504). GET /cgi-bin/reboot.php -> STATUS S.
    POST /cgi-bin/led_conf.php {"key": "led", "value":
    "on"|"off"} -> STATUS S. All but login.php need the
    session cookie, else HTTP 401.

Env knobs for the tests: MOCK_SEALMINER_PM_STATE overrides
the stats "PM State" (the resume no-op guard reads it);
MOCK_SEALMINER_MODEL overrides the devdetails Model (the
low_power A2 gate reads it).

Every received command / request line is appended to the
file named by env MOCK_SEALMINER_LOG (when set) so tests
can assert what the scanner did and the exact body each
action sent.

Run:  python3 tests/mock_sealminer.py [host] [rpc_port] [web_port]
"""

import json
import os
import socketserver
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
RPC_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 14035
WEB_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 18086
LOG = os.environ.get("MOCK_SEALMINER_LOG")
PM_STATE = os.environ.get("MOCK_SEALMINER_PM_STATE")
MODEL = os.environ.get("MOCK_SEALMINER_MODEL", "A2")
COOKIE = "session=seal-mock"


def _log(line: str) -> None:
    if LOG:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


# --- RPC fixtures (asic-rs test JSON, verbatim) ---------------------------

VERSION_REPLY = json.loads(r'''{    "STATUS": [
        {
            "Code": 22,
            "Description": "bdminer 4.11.1",
            "Msg": "BDMiner versions",
            "STATUS": "S",
            "When": 1773869546
        }
    ],
    "VERSION": [
        {
            "API": "3.7",
            "BDMiner": "4.11.1"
        }
    ],
    "id": 1
}''')
SUMMARY_REPLY = json.loads(r'''{    "STATUS": [
        {
            "Code": 11,
            "Description": "bdminer 4.11.1",
            "Msg": "Summary",
            "STATUS": "S",
            "When": 1773869546
        }
    ],
    "SUMMARY": [
        {
            "Accepted": 1421,
            "Best Share": 33318911,
            "Device Hardware%": 0.0,
            "Device Rejected%": 0.5485,
            "Difficulty Accepted": 118444032.0,
            "Difficulty Rejected": 655360.0,
            "Difficulty Stale": 0.0,
            "Discarded": 1650,
            "Elapsed": 2481,
            "Found Blocks": 0,
            "Get Failures": 0,
            "Getworks": 264,
            "Hardware Errors": 54,
            "Last getwork": 1773869546,
            "Local Work": 97055,
            "MHS 15m": 194087385.26,
            "MHS 1m": 197599714.1,
            "MHS 5m": 199742402.75,
            "MHS 5s": 368479432.78,
            "MHS av": 206860473.51,
            "Network Blocks": 2,
            "Pool Rejected%": 0.5503,
            "Pool Stale%": 0.0,
            "Rejected": 3,
            "Remote Failures": 0,
            "Stale": 0,
            "Total MH": 513216843003.0,
            "Utility": 34.37,
            "Work Utility": 2889807.43
        }
    ],
    "id": 1
}''')
POOLS_REPLY = json.loads(r'''{    "POOLS": [
        {
            "Accepted": 322,
            "Bad Work": 0,
            "Best Share": 8834293,
            "Current Block Height": 941198,
            "Current Block Version": 536870912,
            "Diff1 Shares": 42270720,
            "Difficulty Accepted": 41746432.0,
            "Difficulty Rejected": 131072.0,
            "Difficulty Stale": 0.0,
            "Discarded": 590,
            "Get Failures": 0,
            "Getworks": 84,
            "Has GBT": false,
            "Has Stratum": true,
            "Has Vmask": true,
            "Last Share Difficulty": 262144.0,
            "Last Share Time": 1773869544,
            "Long Poll": "N",
            "POOL": 0,
            "Pool Rejected%": 0.313,
            "Pool Stale%": 0.0,
            "Priority": 0,
            "Proxy": "",
            "Proxy Type": "",
            "Quota": 1,
            "Rejected": 1,
            "Remote Failures": 0,
            "Stale": 0,
            "Status": "Alive",
            "Stratum Active": true,
            "Stratum Difficulty": 262144.0,
            "Stratum URL": "stratum.braiins.com",
            "URL": "stratum+tcp://stratum.braiins.com:3333",
            "User": "Dow_Mining.SealMinerA2",
            "Work Difficulty": 262144.0,
            "Works": 35726
        }
    ],
    "STATUS": [
        {
            "Code": 7,
            "Description": "bdminer 4.11.1",
            "Msg": "1 Pool(s)",
            "STATUS": "S",
            "When": 1773869546
        }
    ],
    "id": 1
}''')
_STATS = json.loads(r'''{    "STATS": [
        {
            "0 Bad Chip Count": 0,
            "0 Chip Count": 153,
            "0 Freq": 349,
            "0 MHS(Ideal)": 74342544,
            "0 MHS(Sample)": 73905832.003432,
            "0 Online": true,
            "0 PWM": 112,
            "0 SN": "S124600252004637",
            "0 Speed": 3723,
            "0 Temp 0": 55,
            "0 Temp 1": 52,
            "0 Temp 2": 70,
            "0 Temp 3": 69,
            "0 Tune Status": "Fine Tuning Done",
            "1 Bad Chip Count": 0,
            "1 Chip Count": 153,
            "1 Freq": 347,
            "1 MHS(Ideal)": 73927728,
            "1 MHS(Sample)": 73626639.194207,
            "1 Online": true,
            "1 PWM": 112,
            "1 SN": "S124600252004521",
            "1 Speed": 3723,
            "1 Temp 0": 58,
            "1 Temp 1": 55,
            "1 Temp 2": 70,
            "1 Temp 3": 68,
            "1 Tune Status": "Fine Tuning Done",
            "2 Bad Chip Count": 0,
            "2 Chip Count": 153,
            "2 Freq": 344,
            "2 MHS(Ideal)": 73393200,
            "2 MHS(Sample)": 72846394.903347,
            "2 Online": true,
            "2 PWM": 112,
            "2 SN": "S124600252004476",
            "2 Speed": 3753,
            "2 Temp 0": 56,
            "2 Temp 1": 51,
            "2 Temp 2": 70,
            "2 Temp 3": 65,
            "2 Tune Status": "Fine Tuning Done",
            "3 PWM": 112,
            "3 Speed": 3723,
            "ASIC": "Seal02-V1",
            "BIN Number": 24,
            "BIN Version": 1,
            "Bad Chip Count": 0,
            "Board Count": 3,
            "Boot Count": 3,
            "Boot Temp": 39,
            "Boot Time": 222.256938,
            "Calls": 0,
            "Chip Count": 459,
            "Chip Voltage": 307,
            "Coarse Tune Time": 627.802376,
            "Ctrl Board": "taurus_air_v1.1",
            "Ctrl Board SN": "S127200252001850",
            "Current BTC Price": 30664.550781,
            "Current Block Reward": 6.580114,
            "Current Electric Price": 0.04,
            "Current Network Hashrate": 339810000,
            "Debug": true,
            "Elapsed": 2481,
            "Error Chip": "",
            "Error Code": "",
            "Fan Count": 4,
            "Fast Raise Freq": false,
            "Fine Tune Time": 86.916604,
            "Firmware": "2025091001",
            "Freq": 346,
            "Hashrate Boost Ratio": 0.0,
            "ID": "A20",
            "IP": "10.0.13.179",
            "Liquid Cooling": false,
            "MAC": "50:d4:48:4b:86:78",
            "MHS(15m)": 220165799.256646,
            "MHS(1h)": 122108173.142338,
            "MHS(1m)": 220315525.22617,
            "MHS(2h)": 61054086.571169,
            "MHS(2m)": 220298736.318481,
            "MHS(30m)": 219399667.040008,
            "MHS(30s)": 220407636.771225,
            "MHS(5m)": 220245222.406483,
            "MHS(Avg)": 218701205.628067,
            "MHS(Ideal)": 221663472,
            "MHS(Rated)": 230839407.28559,
            "MHS(Sample)": 220377998.845847,
            "Max": 0.0,
            "Min": 99999999.0,
            "Mining Mode": "Normal",
            "Model": "A2",
            "PM State": "Running",
            "PSU Efficiency": 0.922374,
            "PSU Error": "0x00000000",
            "PSU Fan Speed": 4408,
            "PSU Firmware": "222121",
            "PSU Input Power": 3504,
            "PSU Input Voltage": 246.0,
            "PSU Model": "BTPSU04KSA-03.00",
            "PSU Output Current": 206.0,
            "PSU Output Power": 3232,
            "PSU Output Voltage": 15.671,
            "PSU SN": "3C251501801",
            "PSU Temp AMB": 26,
            "Power Limit": 3500,
            "Profit Boost Ratio": 0.0,
            "Profit Dayli": 0.0,
            "Raise Freq Done": true,
            "Raise Freq Done Reason": "Input Power Limit",
            "Raise Freq Time": 579.123231,
            "STATS": 0,
            "Software Version": "4.11.1-08690-gd309fbe0",
            "Stratum Disconnect": false,
            "System Uptime": 2743,
            "Target Ctrl Temp": 70,
            "Temp": 70,
            "Total Energy Consumption": 4.107023,
            "Tune Status": "Fine Tuning Done",
            "Tune Time": 719.876594,
            "Wait": 0.0
        }
    ],
    "STATUS": [
        {
            "Code": 70,
            "Description": "bdminer 4.11.1",
            "Msg": "BDMiner stats",
            "STATUS": "S",
            "When": 1773869546
        }
    ],
    "id": 1
}''')

if PM_STATE is not None:
    _STATS["STATS"][0]["PM State"] = PM_STATE

STATS_REPLY = _STATS

# CONSTRUCTED (see module docstring): only the field the client
# reads — /DEVDETAILS/0/Model — with the sysinfo fixture's value.
DEVDETAILS_REPLY = {
    "STATUS": [{"Code": 9, "Description": "bdminer 4.11.1",
                "Msg": "Device details", "STATUS": "S",
                "When": 1773869546}],
    "DEVDETAILS": [{"Model": MODEL}],
    "id": 1,
}

_RPC_REPLIES = {
    "version": VERSION_REPLY,
    "summary": SUMMARY_REPLY,
    "pools": POOLS_REPLY,
    "stats": STATS_REPLY,
    "devdetails": DEVDETAILS_REPLY,
}


def _rpc_status(status: str, code: int, msg: str) -> dict:
    return {"STATUS": [{"STATUS": status, "When": 1773869546,
                        "Code": code, "Msg": msg,
                        "Description": "bdminer 4.11.1"}],
            "id": 1}


# --- Web fixtures (asic-rs test JSON, verbatim) ---------------------------

SYSINFO_REPLY = json.loads(r'''{    "DHCP": "true",
    "brand": "Sealminer",
    "crtl_sn": "S127200252001850",
    "ctrl_version": "taurus_air_v1.1",
    "custom": 5,
    "firmware_version": "2025091001",
    "high_performance": 3,
    "ipaddress": "10.0.13.179",
    "led": "on",
    "low_power": 0,
    "macaddr": "50:d4:48:4b:86:78",
    "miner_type": "A2",
    "miningMode": "2",
    "nomalPowerRatio": null,
    "normal": 2,
    "psu_model": "boco_v2.0",
    "ratedHashrate": 0,
    "systemTime": "Wed Mar 18 21:32:32 UTC 2026",
    "tuning_done": 0,
    "upgrade_result": "0\n"
}''')
PSU_STATUS_REPLY = json.loads(r'''{    "Current": 206,
    "Online": 1,
    "Power": 3504,
    "StatusCode": "0x0000",
    "Temp": 26,
    "Voltage": 15.67
}''')


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
        payload = _rpc_reply(command, parameter)
        try:
            # cgminer replies end with a trailing NUL byte.
            self.request.sendall(json.dumps(payload).encode() + b"\x00")
        except OSError:
            pass


def _rpc_reply(command: str, parameter) -> dict:
    if command in _RPC_REPLIES:
        return _RPC_REPLIES[command]
    if command == "restart":
        return _rpc_status("S", 0, "Restart")
    if command == "ascset":
        return _ascset_reply(parameter)
    if command == "updatepools":
        return _updatepools_reply(parameter)
    return {"STATUS": [{"STATUS": "E", "Code": 14,
                        "Msg": f"Invalid command: {command}"}],
            "id": 1}


def _ascset_reply(parameter) -> dict:
    """STATUS S for "0,suspend"; STATUS S + Code 119 for a
    well-formed tuning ascset (asic-rs set_tuning_option);
    STATUS E otherwise."""
    if not isinstance(parameter, str):
        return _rpc_status("E", 119, "ascset needs a string parameter")
    if parameter == "0,suspend":
        return _rpc_status("S", 0, "ASC set")
    parts = parameter.split(",", 2)
    if len(parts) != 3 or parts[0] != "0":
        return _rpc_status("E", 119, "bad ascset parameter")
    option, settings_raw = parts[1], parts[2]
    try:
        settings = json.loads(settings_raw)
    except ValueError:
        return _rpc_status("E", 119, "bad ascset settings JSON")
    if not isinstance(settings, dict):
        return _rpc_status("E", 119, "bad ascset settings JSON")
    if option == "powerlimit" and "value" in settings:
        try:
            watts = int(settings["value"])
        except (TypeError, ValueError):
            return _rpc_status("E", 119, "bad powerlimit value")
        if watts < 0 or watts > 0xFFFFFFFF:
            return _rpc_status("E", 119, "bad powerlimit value")
        return _rpc_status("S", 119, "ASC set")
    if option == "workmode" and settings.get("mode") in (
            "low_power", "normal", "high_performance"):
        return _rpc_status("S", 119, "ASC set")
    return _rpc_status("E", 119, f"unknown ascset option {option!r}")


def _updatepools_reply(parameter) -> dict:
    """The parameter is a JSON STRING {"pools": [...]}."""
    if not isinstance(parameter, str):
        return _rpc_status("E", 0, "updatepools needs a string parameter")
    try:
        parsed = json.loads(parameter)
    except ValueError:
        return _rpc_status("E", 0, "bad updatepools parameter JSON")
    pools = parsed.get("pools") if isinstance(parsed, dict) else None
    if not isinstance(pools, list) or not pools \
            or not all(isinstance(p, dict) and p.get("url")
                       for p in pools):
        return _rpc_status("E", 0, "updatepools needs 1+ pools with url")
    return _rpc_status("S", 0, "Pools updated")


class RpcServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


# --- Web server -------------------------------------------------------------

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

    def _read_raw(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def _check_cookie(self) -> bool:
        return COOKIE in (self.headers.get("Cookie") or "")

    def _unauthorised(self) -> None:
        self._send_json(401, {"error": "unauthorised"})

    def do_GET(self):
        command = urlparse(self.path).path.strip("/").removeprefix(
            "cgi-bin/").removesuffix(".php")
        _log(f"WEB GET /cgi-bin/{command}.php")
        if command == "get_system_info":
            if not self._check_cookie():
                self._unauthorised()
                return
            self._send_json(200, SYSINFO_REPLY)
            return
        if command == "miner_psu_status":
            if not self._check_cookie():
                self._unauthorised()
                return
            self._send_json(200, PSU_STATUS_REPLY)
            return
        if command == "reboot":
            if not self._check_cookie():
                self._unauthorised()
                return
            self._send_json(200, _rpc_status("S", 200, "Rebooting"))
            return
        self._send_json(404, {"error": f"unknown command {command}"})

    def do_POST(self):
        command = urlparse(self.path).path.strip("/").removeprefix(
            "cgi-bin/").removesuffix(".php")
        raw = self._read_raw()
        try:
            body = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError:
            body = {}
        _log(f"WEB POST /cgi-bin/{command}.php "
             f"{json.dumps(body, sort_keys=True)}")
        if command == "login":
            form = parse_qs(raw.decode("utf-8", errors="replace"))
            user = (form.get("username") or [""])[0]
            password = (form.get("origin_pwd") or [""])[0]
            if user == "seal" and password == "seal":
                self._send_json(200, {"result": "ok"}, headers={
                    "Set-Cookie": COOKIE + "; Path=/"})
            else:
                # No set-cookie — the client fails with "no session
                # cookie in login response" (asic-rs behaviour).
                self._send_json(200, {
                    "error": "Invalid username or password"})
            return
        if not self._check_cookie():
            self._unauthorised()
            return
        if command == "led_conf":
            if isinstance(body, dict) \
                    and body.get("key") == "led" \
                    and body.get("value") in ("on", "off"):
                self._send_json(200, _rpc_status("S", 200, "LED set"))
            else:
                self._send_json(400, {"error": "bad led_conf body"})
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
