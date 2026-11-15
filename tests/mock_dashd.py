#!/usr/bin/env python3
"""Fake VNish dashd (xminer-api) server — a sick S19 Pro on 127.0.0.2:80.

Payloads are shaped after the firmware's own OpenAPI document
(``usr/share/dashd/ui/docs/api-doc.json``): ``GET /api/v1/summary`` returns
``{"miner": AntmMinerStats}``, ``GET /api/v1/boards`` returns
``[AntmBoardChips]`` with one AntmChip per chip, plus ``/info`` and
``/model``. Sample faults, chosen so the scanner must flag the miner:

  * board 1: 2 dead chips (grade "red", positions 10 and 55 of 114)
  * board 2: chip temperature max 87 C — above the 85 C flag threshold
  * board 3: healthy

Remote actions (v0.6) follow the same api-doc: the write endpoints
``POST /api/v1/system/reboot`` and ``POST /api/v1/mining/switch-pool``,
plus ``GET|POST /api/v1/settings`` and ``POST /api/v1/unlock``, are
implemented — and so is ``POST /api/v1/firmware/update`` (v0.11,
multipart, records filename + sha256 of the uploaded file). All of
them use the doc's auth shape — an ``x-api-key`` header equal
to ``mock-api-key`` or a bearer JWT ``mock-jwt`` (minted by /unlock
for password ``mock-pw``); ``GET /settings`` accepts the API key
only, like the doc says. Every action hit is recorded to the JSON
state file named by the BEESKY_MOCK_DASHD_STATE env var (when set).

The v0.29 ops tail adds the remaining documented write endpoints:
bodyless ``POST /mining/pause|resume|restart`` (auth),
``POST /locate-miner`` (NO auth — the doc declares none; it toggles
an internal flag and replies ``{"is_enabled": ...}``),
``POST /mining/throttle`` (auth; percent outside the doc's 20..100
is a 400 ``{"err": ...}`` refusal; percent **55** is this mock's
magic value whose SaveConfigResult carries
``restart_required: true`` so the flags-surfacing path is testable),
``POST /autotune/reset`` + ``/reset-all`` (auth; bodies recorded),
``POST /apikeys`` + ``/apikeys/delete`` (auth; a key that is not
exactly 32 chars is a 400 refusal; re-adding a known key reports
``updated``), and the reads ``GET /perf-summary`` (no auth; the
current preset is ``perf-110``) + ``GET /autotune/presets`` (auth).
Every hit records WHICH auth won (``apikey`` / ``bearer``) so tests
assert the request shape, not just success.

Run directly to serve forever:  python3 tests/mock_dashd.py [host] [port]
"""

import hashlib
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.2"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 80

API_KEY = "mock-api-key"
UNLOCK_PASSWORD = "mock-pw"
JWT = "mock-jwt"
STATE_PATH = os.environ.get("BEESKY_MOCK_DASHD_STATE")

_POOLS = [
    {"url": "stratum+tcp://pool.example.com:3333", "user": "mockworker.001",
     "pass": "x", "use_tls": False},
    {"url": "stratum+tcp://backup.example.com:3333", "user": "mockworker.002",
     "pass": "x", "use_tls": False},
]
_ACTION_STATE = {"reboots": [], "switch_pools": [], "settings_posts": [],
                 "unlocks": 0, "active_pool": 0, "firmware_updates": [],
                 # v0.29 ops tail
                 "mining_posts": [], "locate_hits": 0, "locate_on": False,
                 "throttles": [], "autotune_resets": [],
                 "apikey_adds": [], "apikey_deletes": [],
                 "known_apikeys": []}

CURRENT_PRESET = {"name": "perf-110", "pretty": "Perf 110 TH/s",
                  "status": "tuned"}
AUTOTUNE_PRESETS = [
    {"name": "perf-110", "pretty": "Perf 110 TH/s", "status": "tuned",
     "tune_settings": None},
    {"name": "eco-95", "pretty": "Eco 95 TH/s", "status": "untuned",
     "tune_settings": None},
]


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


def _record_state() -> None:
    if not STATE_PATH:
        return
    snapshot = {**_ACTION_STATE, "pools": _POOLS}
    Path(STATE_PATH).write_text(json.dumps(snapshot), encoding="utf-8")


def settings_payload() -> dict:
    return {
        "miner": {
            "pools": _POOLS,
            "cooling": {"mode": "auto"},
            "misc": None,
            "overclock": None,
        },
        "network": {"dhcp": True},
        "password": {},
        "regional": {"lang": "en"},
        "ui": {"theme": "dark"},
    }

CHIPS_PER_BOARD = 114
DEAD_BOARD1 = (10, 55)  # 1-based chip positions, grade "red"
CHIP_HR = 0.321         # TH/s per healthy chip (S19 Pro class)


def _chips(board_idx: int, dead_positions: tuple[int, ...], temp_hi: float):
    chips = []
    for chip_id in range(CHIPS_PER_BOARD):
        dead = (chip_id + 1) in dead_positions
        # Spread chip temps from ~60 C up to the board's max.
        temp = 60.0 + (temp_hi - 60.0) * (chip_id / (CHIPS_PER_BOARD - 1))
        chips.append({
            "id": chip_id,
            "hr": 0.0 if dead else CHIP_HR,
            "freq": 500,
            "volt": 1300,
            "temp": round(temp, 1),
            "errs": 3 if dead else 0,
            "grade": "red" if dead else "grey",
            "throttled": False,
        })
    return chips


# board_id (0-based) -> (dead positions, chip temp max)
_BOARD_PLAN = {0: (DEAD_BOARD1, 74.0), 1: ((), 87.0), 2: ((), 69.0)}


def _board_chips(board_id: int) -> dict:
    dead, temp_hi = _BOARD_PLAN[board_id]
    chips = _chips(board_id, dead, temp_hi)
    alive = CHIPS_PER_BOARD - len(dead)
    return {
        "id": board_id,
        "status": {"state": "mining"},
        "hr_realtime": round(alive * CHIP_HR, 2),
        "hr_nominal": round(CHIPS_PER_BOARD * CHIP_HR, 2),
        "freq": 500.0,
        "sensors": [{"state": "ready", "board": board_id, "chip": 0, "loc": 0}],
        "chips": chips,
    }


def _board_summary(board_id: int) -> dict:
    dead, temp_hi = _BOARD_PLAN[board_id]
    alive = CHIPS_PER_BOARD - len(dead)
    return {
        "id": board_id,
        "frequency": 500.0,
        "voltage": 1300,
        "power_consumption": 1070,
        "hashrate_ideal": round(CHIPS_PER_BOARD * CHIP_HR, 2),
        "hashrate_rt": round(alive * CHIP_HR, 2),
        "hashrate_percentage": round(100.0 * alive / CHIPS_PER_BOARD, 1),
        "hr_error": 0.1,
        "hw_errors": len(dead),
        "pcb_temp": {"min": 45, "max": int(temp_hi) - 12},
        "chip_temp": {"min": 60, "max": int(temp_hi)},
        "chip_statuses": {
            "red": len(dead),
            "orange": 0,
            "grey": alive,
        },
        "status": {"state": "mining"},
    }


def summary_payload() -> dict:
    boards = [_board_summary(i) for i in range(3)]
    total_rt = round(sum(b["hashrate_rt"] for b in boards), 2)
    return {
        "miner": {
            "miner_status": {
                "miner_state": "mining",
                "throttled": 20,
                "miner_state_time": 5400,
            },
            "miner_type": "Antminer S19 Pro",
            "hr_stock": 110.0,
            "average_hashrate": total_rt * 1000.0,
            "instant_hashrate": total_rt * 1000.0,
            "hr_realtime": total_rt,
            "hr_nominal": 110.0,
            "hr_average": round(total_rt + 0.3, 2),
            "pcb_temp": {"min": 45, "max": 75},
            "chip_temp": {"min": 60, "max": 87},
            "power_consumption": 3210,
            "power_usage": 29.4,
            "power_efficiency": 29.4,
            "hw_errors_percent": 0.02,
            "hr_error": 0.1,
            "hw_errors": 2,
            "devfee_percent": 2.8,
            "devfee": 3.05,
            "pools": [{
                "id": 0,
                "url": "stratum+tcp://pool.example.com:3333",
                "pool_type": "stratum",
                "user": "mockworker.001",
                "use_tls": False,
                "status": "alive",
                "diff": "524288",
                "accepted": 2048,
                "rejected": 12,
                "stale": 1,
                "ls_diff": 524288.0,
                "ls_time": "0:00:07",
                "diffa": 524288.0,
                "ping": 42,
            }],
            "cooling": {
                "fan_num": 4,
                "fans": [
                    {"id": 0, "rpm": 4320, "status": "ok", "max_rpm": 6000},
                    {"id": 1, "rpm": 4380, "status": "ok", "max_rpm": 6000},
                    {"id": 2, "rpm": 4440, "status": "ok", "max_rpm": 6000},
                    {"id": 3, "rpm": 4500, "status": "ok", "max_rpm": 6000},
                ],
                "settings": {"mode": "auto"},
                "fan_duty": 62,
            },
            "chains": boards,
            "found_blocks": 0,
            "best_share": 123456789,
            "restart_count": 1,
            "psu": None,
        }
    }


def info_payload() -> dict:
    return {
        "miner": "Antminer S19 Pro",
        "model": "S19 Pro",
        "algorithm": "sha256",
        "hr_measure": "TH/s",
        "serial": "MOCKDASHD0001",
        "system": {"os": "Buildroot", "kernel": "4.4"},
        "fw_name": "vnish",
        "fw_version": "1.3.5",
    }


def model_payload() -> dict:
    return {
        "full_name": "Antminer S19 Pro",
        "model": "S19 Pro",
        "algorithm": "sha256",
        "series": "S19",
        "platform": "xilinx",
        "install_type": "nand",
        "hr_measure": "TH/s",
        "serial": "MOCKDASHD0001",
        "chain": {
            "chips_per_chain": CHIPS_PER_BOARD,
            "chips_per_domain": 3,
            "num_chains": 3,
            "topology": "series",
        },
        "cooling": {"min_fan_pwm": 10, "min_target_temp": 55, "max_target_temp": 75},
        "overclock": {"supported": True},
    }


_ROUTES = {
    "/api/v1/summary": summary_payload,
    "/api/v1/boards": lambda: [_board_chips(i) for i in range(3)],
    "/api/v1/info": info_payload,
    "/api/v1/model": model_payload,
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep test output clean
        pass

    def _send_json(self, code: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authed(self, api_key_only: bool = False) -> bool:
        return self._auth_kind(api_key_only) is not None

    def _auth_kind(self, api_key_only: bool = False):
        """Which credential won: "apikey" / "bearer" / None (v0.29 —
        the tail tests assert WHICH header carried the write)."""
        if self.headers.get("x-api-key") == API_KEY:
            return "apikey"
        if api_key_only:
            return None
        if self.headers.get("Authorization") == f"Bearer {JWT}":
            return "bearer"
        return None

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def do_GET(self):
        if self.path == "/api/v1/settings":
            # Per the api-doc, GET /settings is apikeyAuth-only.
            if not self._authed(api_key_only=True):
                self._send_json(401, {"err": "unauthorized"})
            else:
                self._send_json(200, settings_payload())
            return
        if self.path == "/api/v1/perf-summary":
            # The api-doc declares NO security for /perf-summary.
            self._send_json(200, {
                "current_preset": CURRENT_PRESET,
                "preset_switcher": {"enabled": False},
            })
            return
        if self.path == "/api/v1/autotune/presets":
            if not self._authed():
                self._send_json(401, {"err": "unauthorized"})
            else:
                self._send_json(200, AUTOTUNE_PRESETS)
            return
        payload_fn = _ROUTES.get(self.path)
        if payload_fn is None:
            self._send_json(404, {"error": "not found"})
        else:
            self._send_json(200, payload_fn())

    def _firmware_update(self):
        # POST /api/v1/firmware/update (api-doc): multipart file upload,
        # bearer/apikey auth, 200 -> RebootAfter {"after": N}. The raw
        # body is NOT JSON, so it bypasses _read_body entirely.
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""
        if not self._authed():
            self._send_json(401, {"err": "unauthorized"})
            return
        filename, content = _parse_multipart(self.headers, raw)
        _ACTION_STATE["firmware_updates"].append(
            {"filename": filename,
             "sha256": hashlib.sha256(content).hexdigest()})
        _record_state()
        self._send_json(200, {"after": 3})

    def do_POST(self):
        if self.path == "/api/v1/firmware/update":
            self._firmware_update()
            return
        body = self._read_body()
        if self.path == "/api/v1/unlock":
            if body.get("pw") == UNLOCK_PASSWORD:
                _ACTION_STATE["unlocks"] += 1
                _record_state()
                self._send_json(200, {"token": JWT})
            else:
                self._send_json(403, {"err": "invalid password"})
            return
        if self.path == "/api/v1/locate-miner":
            # The api-doc declares NO security for /locate-miner:
            # no auth gate here on purpose. Bodyless toggle; the
            # reply reports the resulting state (LocateMinerStatus).
            _ACTION_STATE["locate_hits"] += 1
            _ACTION_STATE["locate_on"] = not _ACTION_STATE["locate_on"]
            _record_state()
            self._send_json(200, {"is_enabled": _ACTION_STATE["locate_on"]})
            return
        if self.path in ("/api/v1/mining/pause", "/api/v1/mining/resume",
                         "/api/v1/mining/restart"):
            kind = self._auth_kind()
            if kind is None:
                self._send_json(401, {"err": "unauthorized"})
                return
            _ACTION_STATE["mining_posts"].append(
                {"path": self.path, "auth": kind})
            _record_state()
            self._send_json(200, {})
            return
        if self.path == "/api/v1/mining/throttle":
            kind = self._auth_kind()
            if kind is None:
                self._send_json(401, {"err": "unauthorized"})
                return
            percent = body.get("percent")
            if not isinstance(percent, int) or isinstance(percent, bool) \
                    or not 20 <= percent <= 100:
                self._send_json(400, {
                    "err": f"percent {percent!r} out of range 20..100"})
                return
            _ACTION_STATE["throttles"].append(
                {"percent": percent, "auth": kind})
            _record_state()
            # Magic value 55: the mock's SaveConfigResult asks for a
            # mining restart, so the flags path is testable.
            self._send_json(200, {
                "restart_required": percent == 55,
                "reboot_required": False})
            return
        if self.path in ("/api/v1/autotune/reset",
                         "/api/v1/autotune/reset-all"):
            kind = self._auth_kind()
            if kind is None:
                self._send_json(401, {"err": "unauthorized"})
                return
            if self.path.endswith("reset-all"):
                if not isinstance(body.get("restart"), bool):
                    self._send_json(400, {
                        "err": "restart (bool) is required"})
                    return
            elif not isinstance(body.get("presets"), list) \
                    or not isinstance(body.get("restart"), bool):
                self._send_json(400, {
                    "err": "presets (list) and restart (bool) "
                           "are required"})
                return
            _ACTION_STATE["autotune_resets"].append(
                {"path": self.path, "body": body, "auth": kind})
            _record_state()
            self._send_json(200, {})
            return
        if self.path in ("/api/v1/apikeys", "/api/v1/apikeys/delete"):
            kind = self._auth_kind()
            if kind is None:
                self._send_json(401, {"err": "unauthorized"})
                return
            key = body.get("key")
            if not isinstance(key, str) or len(key) != 32:
                self._send_json(400, {
                    "err": "key must be exactly 32 characters"})
                return
            if self.path.endswith("/delete"):
                _ACTION_STATE["apikey_deletes"].append(
                    {"key": key, "auth": kind})
                if key in _ACTION_STATE["known_apikeys"]:
                    _ACTION_STATE["known_apikeys"].remove(key)
                _record_state()
                self._send_json(200, {})
            else:
                status = "updated" if key in _ACTION_STATE[
                    "known_apikeys"] else "inserted"
                if status == "inserted":
                    _ACTION_STATE["known_apikeys"].append(key)
                _ACTION_STATE["apikey_adds"].append(
                    {"key": key,
                     "description": body.get("description"),
                     "auth": kind})
                _record_state()
                self._send_json(200, {"status": status})
            return
        if self.path in ("/api/v1/system/reboot",
                         "/api/v1/mining/switch-pool",
                         "/api/v1/settings"):
            if not self._authed():
                self._send_json(401, {"err": "unauthorized"})
                return
            if self.path == "/api/v1/system/reboot":
                _ACTION_STATE["reboots"].append(time.time())
                _record_state()
                self._send_json(200, {"after": 3})
            elif self.path == "/api/v1/mining/switch-pool":
                _ACTION_STATE["switch_pools"].append(body)
                if isinstance(body.get("pool_id"), int):
                    _ACTION_STATE["active_pool"] = body["pool_id"]
                _record_state()
                self._send_json(200, {})
            else:  # /api/v1/settings — full-config save
                _ACTION_STATE["settings_posts"].append(body)
                pools = (body.get("miner") or {}).get("pools")
                if isinstance(pools, list):
                    _POOLS[:] = [p for p in pools if isinstance(p, dict)]
                _record_state()
                self._send_json(200, {})
            return
        self._send_json(404, {"error": "not found"})


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"mock dashd listening on {HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
