#!/usr/bin/env python3
"""Fake Braiins OS (BOSMiner) — the cgminer-compatible TCP API on 4028.

Speaks the contract in docs/vendor-oss-mapping.md §1, built from
Braiins Academy's BOSminer API page (worked examples, quoted
verbatim where the page gives them) and pyasic's BOSMiner handler:

  * `version` -> STATUS Description "BOSminer+ 0.2.0-ea64aec8e"
    (the Academy's string, in every worked example) — the
    detection fingerprint (substring "bosminer"/"boser");
  * `summary` -> SUMMARY with "MHS 1m" (pyasic's rate key), an
    S19 Pro at ~110.5 TH/s;
  * `fans` / `temps` / `tunerstatus` / `devdetails` in the
    Academy's shapes (temps IDs 6–8, the S9-style offset pyasic
    applies; values cooled below 85 C so the record reads OK —
    the Academy's own example runs 104–108 C mid-tune, which
    would trip OVER_TEMP);
  * `pause` -> {"PAUSE": [...]} and `resume` -> {"RESUME": [...]}
    (pyasic's stop/resume_mining require those sections);
  * `tunerstatus` reports all chains "Stable" by default; with
    env MOCK_BRAIINS_TUNER_BAD=1 chain 8 reports an error state
    so the TUNER-problem path can be tested.

Every received command name is appended to the file named by env
MOCK_BRAIINS_LOG (when set) so tests can assert what the scanner
did and did NOT ask (notably: reads never pause/resume).

Run:  python3 tests/mock_braiins.py [host] [port]
"""

import json
import os
import socketserver
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4028
LOG = os.environ.get("MOCK_BRAIINS_LOG")
TUNER_BAD = os.environ.get("MOCK_BRAIINS_TUNER_BAD") == "1"

VERSION = "BOSminer+ 0.2.0-ea64aec8e"


def _log(name: str) -> None:
    if LOG:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(name + "\n")


def _status(code: int, msg: str, status: str = "S") -> dict:
    return {"STATUS": [{"STATUS": status, "When": 1595938455,
                        "Code": code, "Msg": msg,
                        "Description": VERSION}],
            "id": 1}


def version_reply() -> dict:
    payload = _status(22, "Version")
    payload["VERSION"] = [{
        "CGMiner": "4.11.1",
        "API": "3.1",
        "Miner": VERSION,
        "CompileTime": "Mon May 1 2024",
    }]
    return payload


def summary_reply() -> dict:
    payload = _status(11, "Summary")
    payload["SUMMARY"] = [{
        "Elapsed": 90000,
        "Type": "Antminer S19 Pro",
        "MHS 1m": 110500000.0,
        "MHS 5s": 110200000.0,
        "MHS av": 109800000.0,
        "Accepted": 123456,
        "Rejected": 12,
        "Hardware Errors": 0,
    }]
    return payload


def pools_reply() -> dict:
    payload = _status(7, "pools")
    payload["POOLS"] = [{
        "POOL": 0,
        "URL": "stratum+tcp://pool.example.com:3333",
        "Status": "Alive",
        "User": "braiinsuser.001",
        "Accepted": 123456,
        "Rejected": 12,
        "Get Failures": 0,
        "Remote Failures": 0,
        "Stratum Active": True,
    }]
    return payload


def fans_reply() -> dict:
    # Academy's fans example, verbatim (RPM + Speed).
    payload = _status(202, "4 Fan(s)")
    payload["FANS"] = [
        {"FAN": 0, "ID": 0, "RPM": 5340, "Speed": 100},
        {"FAN": 1, "ID": 1, "RPM": 4620, "Speed": 100},
        {"FAN": 2, "ID": 2, "RPM": 0, "Speed": 100},
        {"FAN": 3, "ID": 3, "RPM": 0, "Speed": 100},
    ]
    return payload


def temps_reply() -> dict:
    # Academy's temps example SHAPE (IDs 6–8, Chip/Board keys);
    # values cooled so the record stays OK (see module docstring).
    payload = _status(201, "3 Temp(s)")
    payload["TEMPS"] = [
        {"Board": 61.0, "Chip": 71.0, "ID": 6, "TEMP": 0},
        {"Board": 63.0, "Chip": 73.0, "ID": 7, "TEMP": 1},
        {"Board": 60.0, "Chip": 69.0, "ID": 8, "TEMP": 2},
    ]
    return payload


def tunerstatus_reply() -> dict:
    # Academy's tunerstatus example SHAPE (power + chain states).
    chains = [
        {"ApproximatePowerConsumptionWatt": 1083,
         "HashchainIndex": 6, "Iteration": 0,
         "PowerLimitWatt": 1083, "StageElapsed": 78,
         "Status": "Stable", "TunerRunning": False,
         "TuningElapsed": 98},
        {"ApproximatePowerConsumptionWatt": 1083,
         "HashchainIndex": 7, "Iteration": 0,
         "PowerLimitWatt": 1083, "StageElapsed": 78,
         "Status": "Stable", "TunerRunning": False,
         "TuningElapsed": 98},
        {"ApproximatePowerConsumptionWatt": 1084,
         "HashchainIndex": 8, "Iteration": 0,
         "PowerLimitWatt": 1084, "StageElapsed": 78,
         "Status": ("overheating" if TUNER_BAD
                    else "Stable"),
         "TunerRunning": False, "TuningElapsed": 98},
    ]
    payload = _status(203, "Tuner Status")
    payload["TUNERSTATUS"] = [{
        "ApproximateChainPowerConsumption": 3250,
        "ApproximateMinerPowerConsumption": 3250,
        "DynamicPowerScaling": "Disabled",
        "PowerLimit": 3250,
        "TunerChainStatus": chains,
    }]
    return payload


def devdetails_reply() -> dict:
    # Academy's devdetails example SHAPE (IDs 6–8, Model/Chips).
    payload = _status(69, "Device Details")
    payload["DEVDETAILS"] = [
        {"Chips": 114, "Cores": 12996, "DEVDETAILS": 0,
         "Device Path": "", "Driver": "",
         "Frequency": 545000000, "ID": 6, "Kernel": "",
         "Model": "Bitmain Antminer S19 Pro", "Name": "Hash Chain 6",
         "Voltage": 13.5},
        {"Chips": 114, "Cores": 12996, "DEVDETAILS": 1,
         "Device Path": "", "Driver": "",
         "Frequency": 545000000, "ID": 7, "Kernel": "",
         "Model": "Bitmain Antminer S19 Pro", "Name": "Hash Chain 7",
         "Voltage": 13.5},
        {"Chips": 114, "Cores": 12996, "DEVDETAILS": 2,
         "Device Path": "", "Driver": "",
         "Frequency": 545000000, "ID": 8, "Kernel": "",
         "Model": "Bitmain Antminer S19 Pro", "Name": "Hash Chain 8",
         "Voltage": 13.5},
    ]
    return payload


def devs_reply() -> dict:
    payload = _status(9, "3 ASC(s)")
    payload["DEVS"] = [
        {"ID": 6, "MHS 1m": 36800000.0, "MHS 5s": 36700000.0,
         "MHS av": 36600000.0, "Nominal MHS": 36700000.0},
        {"ID": 7, "MHS 1m": 36900000.0, "MHS 5s": 36800000.0,
         "MHS av": 36700000.0, "Nominal MHS": 36700000.0},
        {"ID": 8, "MHS 1m": 36800000.0, "MHS 5s": 36800000.0,
         "MHS av": 36600000.0, "Nominal MHS": 36700000.0},
    ]
    return payload


def pause_reply() -> dict:
    payload = _status(0, "Mining paused")
    payload["PAUSE"] = [{"When": 1595938455, "Code": 0,
                         "Msg": "Mining paused"}]
    return payload


def resume_reply() -> dict:
    payload = _status(0, "Mining resumed")
    payload["RESUME"] = [{"When": 1595938455, "Code": 0,
                          "Msg": "Mining resumed"}]
    return payload


_REPLIES = {"version": version_reply, "summary": summary_reply,
            "pools": pools_reply, "fans": fans_reply,
            "temps": temps_reply, "tunerstatus": tunerstatus_reply,
            "devdetails": devdetails_reply, "devs": devs_reply,
            "pause": pause_reply, "resume": resume_reply}


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
        if command in _REPLIES:
            payload = _REPLIES[command]()
        else:
            payload = _status(14, f"Invalid command: {command}",
                              status="E")
        try:
            self.request.sendall(json.dumps(payload).encode() + b"\x00")
        except OSError:
            pass


class Server(socketserver.ThreadingTCPServer):
    # Set BEFORE bind: tests respawn this mock on the same port
    # (TUNER-bad variant) and a listener without SO_REUSEADDR
    # cannot rebind while the previous run's connections sit in
    # TIME_WAIT.
    allow_reuse_address = True
    daemon_threads = True


def main():
    with Server((HOST, PORT), Handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
