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

Run directly to serve forever:  python3 tests/mock_dashd.py [host] [port]
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.2"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 80

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

    def do_GET(self):
        payload_fn = _ROUTES.get(self.path)
        if payload_fn is None:
            body = json.dumps({"error": "not found"}).encode()
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
    print(f"mock dashd listening on {HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
