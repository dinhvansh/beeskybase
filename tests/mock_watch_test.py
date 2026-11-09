#!/usr/bin/env python3
"""v0.3 end-to-end watch test — events + notifications, no hardware.

Drives the real CLI (`python -m beesky watch 127.0.0.1 --once --state …`)
against tests/mock_watch_miner.py through a scripted life story:

  pass 1-3  healthy 110 TH/s        -> baseline builds, no events
  pass 4    hashrate drops to 66    -> HASHRATE_DROP ~40% (severity major)
  pass 5    still dropped           -> anti-flap: no second event
  pass 6    miner process killed    -> OFFLINE
  pass 7    still down              -> anti-flap: no second OFFLINE
  pass 8    miner back, healthy     -> BACK_ONLINE

A local HTTP receiver captures both notification channels: webhook
POSTs land on /hook, Telegram Bot API calls (api_base overridden to the
same receiver) land on /bot<token>/sendMessage. Assertions check the
captured payloads, the severity mapping and the logfile channel.

Prints PASS lines plus the captured webhook payloads; exit 1 on failure.
Run via tests/run_mock_test_v3.sh (which appends evidence to RESULTS.md).
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MINER_PORT = 14028
HOOK_PORT = 18777
HEALTHY = {"ghs": 110000.0, "temps": [65, 71, 74], "dead": {}}
DROPPED = {"ghs": 66000.0, "temps": [65, 71, 74], "dead": {}}

captured: list[dict] = []
_capture_lock = threading.Lock()
FAILURES: list[str] = []


class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8", "replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body}
        with _capture_lock:
            captured.append({"path": self.path, "json": payload})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def log_message(self, *_args):  # keep test output clean
        pass


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label} {extra}")
        FAILURES.append(label)


def wait_port(port: int, want_open: bool, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                if want_open:
                    return True
        except OSError:
            if not want_open:
                return True
        time.sleep(0.1)
    return False


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-watch-"))
    control = tmp / "miner.json"
    state = tmp / "state.json"
    logfile = tmp / "events.log"
    config = tmp / "notify.json"
    control.write_text(json.dumps(HEALTHY), encoding="utf-8")
    config.write_text(json.dumps({
        "thresholds": {"cooldown_s": 1, "baseline_min_samples": 2,
                       "baseline_window": 12},
        "channels": {
            "webhook": {"enabled": True,
                        "url": f"http://127.0.0.1:{HOOK_PORT}/hook"},
            "telegram": {"enabled": True, "bot_token": "TESTTOKEN",
                         "chat_id": "424242",
                         "api_base": f"http://127.0.0.1:{HOOK_PORT}"},
            "logfile": {"enabled": True, "path": str(logfile)},
        },
        "events": {
            "HASHRATE_DROP": {"channels": ["webhook", "telegram", "logfile"],
                              "min_severity": "info"},
            "OFFLINE": {"channels": ["webhook", "telegram", "logfile"],
                        "min_severity": "info"},
            "BACK_ONLINE": {"channels": ["webhook", "logfile"],
                            "min_severity": "info"},
        },
    }), encoding="utf-8")

    receiver = ThreadingHTTPServer(("127.0.0.1", HOOK_PORT), Receiver)
    threading.Thread(target=receiver.serve_forever, daemon=True).start()

    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    miner_cmd = [sys.executable, str(ROOT / "tests" / "mock_watch_miner.py"),
                 "--port", str(MINER_PORT), "--control", str(control)]

    def start_miner() -> subprocess.Popen:
        proc = subprocess.Popen(miner_cmd, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        assert wait_port(MINER_PORT, True), "mock miner did not start"
        return proc

    def run_pass() -> str:
        out = subprocess.run(
            [sys.executable, "-m", "beesky", "watch", "127.0.0.1",
             "--once", "--state", str(state), "--notify", str(config),
             "--interval", "1", "--timeout", "1.0",
             "--cgminer-port", str(MINER_PORT), "--http-port", "18099"],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            raise RuntimeError(f"watch pass failed:\n{out.stdout}\n{out.stderr}")
        return out.stdout

    def hooks(event_type: str) -> list[dict]:
        with _capture_lock:
            return [c["json"] for c in captured
                    if c["path"] == "/hook"
                    and c["json"].get("type") == event_type]

    def telegrams(fragment: str) -> list[dict]:
        with _capture_lock:
            return [c["json"] for c in captured
                    if c["path"].endswith("/sendMessage")
                    and fragment in str(c["json"].get("text", ""))]

    miner = start_miner()
    try:
        for _ in range(3):
            out = run_pass()
        check("healthy passes: no events while baseline builds",
              "EVENT" not in out, out)
        check("healthy passes: no notifications sent", not captured)

        control.write_text(json.dumps(DROPPED), encoding="utf-8")
        out = run_pass()
        drops = hooks("HASHRATE_DROP")
        check("hashrate drop pass: HASHRATE_DROP printed",
              "EVENT HASHRATE_DROP" in out, out)
        check("webhook received exactly one HASHRATE_DROP", len(drops) == 1,
              f"got {len(drops)}")
        if drops:
            ev = drops[0]
            check("drop payload shape (ip/model/type/severity/detail/data)",
                  ev.get("ip") == "127.0.0.1"
                  and ev.get("model") == "Antminer S19 Pro"
                  and ev.get("severity") == "major"  # 40% in the 30-50 step
                  and "dropped" in ev.get("detail", ""), json.dumps(ev))
            pct = (ev.get("data") or {}).get("drop_pct")
            check("drop payload: drop_pct ~= 40", pct is not None
                  and abs(pct - 40.0) < 0.6, f"drop_pct={pct}")
            check("drop payload: baseline 110 -> current 66 TH/s",
                  ev["data"].get("baseline_ths") == 110.0
                  and ev["data"].get("current_ths") == 66.0,
                  json.dumps(ev["data"]))
        tg = telegrams("HASHRATE_DROP")
        check("telegram sendMessage captured for the drop",
              len(tg) == 1 and str(tg[0].get("chat_id")) == "424242"
              and "40.0%" in str(tg[0].get("text", "")), json.dumps(tg))

        out = run_pass()
        check("still dropped: anti-flap, no duplicate HASHRATE_DROP",
              len(hooks("HASHRATE_DROP")) == 1 and "EVENT" not in out, out)

        miner.terminate()
        miner.wait(timeout=10)
        assert wait_port(MINER_PORT, False), "mock miner did not stop"
        out = run_pass()
        offs = hooks("OFFLINE")
        check("miner killed: OFFLINE printed + webhook received",
              "EVENT OFFLINE" in out and len(offs) == 1, out)
        if offs:
            check("OFFLINE payload: severity critical, model kept",
                  offs[0].get("severity") == "critical"
                  and offs[0].get("model") == "Antminer S19 Pro",
                  json.dumps(offs[0]))
        check("telegram captured for OFFLINE",
              len(telegrams("OFFLINE")) == 1)

        out = run_pass()
        check("still down: anti-flap, no duplicate OFFLINE",
              len(hooks("OFFLINE")) == 1 and "EVENT" not in out, out)

        control.write_text(json.dumps(HEALTHY), encoding="utf-8")
        miner = start_miner()
        out = run_pass()
        backs = hooks("BACK_ONLINE")
        check("miner back: BACK_ONLINE printed + webhook received",
              "EVENT BACK_ONLINE" in out and len(backs) == 1, out)

        logged = [json.loads(line) for line in
                  logfile.read_text(encoding="utf-8").splitlines()
                  if line.strip()]
        check("logfile channel recorded all three events",
              [e["type"] for e in logged]
              == ["HASHRATE_DROP", "OFFLINE", "BACK_ONLINE"],
              json.dumps([e.get("type") for e in logged]))
    finally:
        if miner.poll() is None:
            miner.terminate()
        receiver.shutdown()

    print()
    print("Captured webhook payloads:")
    with _capture_lock:
        for item in captured:
            if item["path"] == "/hook":
                print(json.dumps(item["json"], ensure_ascii=False))
    print()
    if FAILURES:
        print(f"WATCH TEST FAILED: {len(FAILURES)} assertion(s): {FAILURES}")
        return 1
    print("WATCH TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
