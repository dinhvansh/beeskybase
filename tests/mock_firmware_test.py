#!/usr/bin/env python3
"""v0.11 firmware test — identify / install / gated unlock, hermetic.

No hardware, no network beyond loopback:

  * tests/mock_stock_fw.py on 127.0.0.5:18084 — digest-auth stock miner
    with miner_type.cgi, upgrade.cgi (records uploads) and a
    patch_success.cgi that flips to 200 only after BOTH .bmu uploads
    AND the race-kill marker file exist. Its update_first.bmu handler
    blocks until the marker appears, mimicking the real signature-
    verification window the race shoots into.
  * tests/mock_dashd.py on 127.0.0.6:18085 — implements the documented
    POST /api/v1/firmware/update.
  * a fake ``ssh`` shim on PATH — logs argv to the same event log the
    mock appends HTTP lines to, answers compile_time, and creates the
    marker file when it receives the kill command.

Asserts: identify verdicts (stock+SSH, stock without an ssh binary,
VNish); stock install uploads the exact bytes (sha256 match); dashd
install lands via the documented endpoint; unlock refuses with ZERO
HTTP requests when any hard gate is missing (no flag / no env / wrong
typed IP / missing payload files); unlock with all gates runs the
recovered sequence in order (identify -> first.bmu -> kill ->
second.bmu -> patch marker -> success).

Prints PASS lines; exit 1 on failure. Run via tests/run_mock_test_v11.sh
(which appends evidence to tests/RESULTS.md).
"""

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOCK_IP, STOCK_PORT = "127.0.0.5", 18084
DASHD_IP, DASHD_PORT = "127.0.0.6", 18085
DEAD_CGMINER = "14095"  # nothing listens there; probes must skip cgminer

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}: {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)


def wait_port(ip: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((ip, port), timeout=1):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"{ip}:{port} never came up")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-fw-test-"))
    log_path = tmp / "events.log"
    marker_path = tmp / "race-marker"
    dashd_state = tmp / "dashd-state.json"
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    empty_bin = tmp / "empty-bin"
    empty_bin.mkdir()

    shim = bin_dir / "ssh"
    shim.write_text(
        "#!/bin/sh\n"
        'echo "ssh:$*" >> "$BEESKY_MOCK_FW_LOG"\n'
        'case "$*" in\n'
        '  *compile_time*) echo "Fri Nov 29 11:11:11 CST 2024" ;;\n'
        '  *kill*) : > "$BEESKY_MOCK_FW_MARKER" ;;\n'
        "esac\n"
        "exit 0\n", encoding="utf-8")
    shim.chmod(0o755)

    base_env = dict(os.environ)
    base_env["BEESKY_MOCK_FW_LOG"] = str(log_path)
    base_env["BEESKY_MOCK_FW_MARKER"] = str(marker_path)
    shim_env = dict(base_env)
    shim_env["PATH"] = f"{bin_dir}{os.pathsep}{base_env.get('PATH', '')}"

    servers = []
    try:
        stock_env = dict(base_env)
        servers.append(subprocess.Popen(
            [sys.executable, str(ROOT / "tests" / "mock_stock_fw.py"),
             STOCK_IP, str(STOCK_PORT)],
            env=stock_env, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL))
        dashd_env = dict(base_env)
        dashd_env["BEESKY_MOCK_DASHD_STATE"] = str(dashd_state)
        servers.append(subprocess.Popen(
            [sys.executable, str(ROOT / "tests" / "mock_dashd.py"),
             DASHD_IP, str(DASHD_PORT)],
            env=dashd_env, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL))
        wait_port(STOCK_IP, STOCK_PORT)
        wait_port(DASHD_IP, DASHD_PORT)

        def run_cli(argv, env, stdin_text=""):
            return subprocess.run(
                [sys.executable, "-m", "beesky"] + argv,
                cwd=ROOT, env=env, input=stdin_text,
                capture_output=True, text=True, timeout=180)

        def log_lines():
            if not log_path.exists():
                return []
            return log_path.read_text(encoding="utf-8").splitlines()

        # -- 1. identify: stock miner, SSH answers via the shim ----------
        proc = run_cli(["fw", "identify", STOCK_IP,
                        "--http-port", str(STOCK_PORT),
                        "--cgminer-port", DEAD_CGMINER], shim_env)
        check("identify stock: exit 0", proc.returncode == 0,
              proc.stderr.strip()[:200])
        check("identify stock: miner_type.cgi read",
              "Antminer S19 Pro" in proc.stdout)
        check("identify stock: compile_time via ssh shim",
              "Fri Nov 29 11:11:11 CST 2024" in proc.stdout)
        check("identify stock: verdict stock cũ / đã mở SSH",
              "stock cũ / đã mở SSH" in proc.stdout)

        # -- 2. identify: no ssh binary on PATH -> verdict không rõ ------
        nossh_env = dict(base_env)
        nossh_env["PATH"] = str(empty_bin)
        proc = run_cli(["fw", "identify", STOCK_IP,
                        "--http-port", str(STOCK_PORT),
                        "--cgminer-port", DEAD_CGMINER], nossh_env)
        check("identify no-ssh: verdict không rõ + note",
              "Kết luận:" in proc.stdout and "không rõ" in proc.stdout
              and "ssh" in proc.stdout.lower())

        # -- 3. identify: VNish miner -------------------------------------
        proc = run_cli(["fw", "identify", DASHD_IP,
                        "--http-port", str(DASHD_PORT),
                        "--cgminer-port", DEAD_CGMINER], shim_env)
        check("identify vnish: verdict cài firmware qua API được",
              proc.returncode == 0
              and "VNish/dashd — cài firmware qua API được" in proc.stdout,
              proc.stdout.strip().splitlines()[-1] if proc.stdout else "")

        # -- 4. install: stock path uploads the exact bytes ---------------
        fw_bytes = b"beesky-test-firmware-image\n" * 8
        fw_file = tmp / "fw-image.tar.gz"
        fw_file.write_bytes(fw_bytes)
        fw_sha = hashlib.sha256(fw_bytes).hexdigest()
        proc = run_cli(["fw", "install", STOCK_IP, str(fw_file),
                        "--http-port", str(STOCK_PORT),
                        "--cgminer-port", DEAD_CGMINER,
                        "--yes", "--wait-minutes", "0"], shim_env)
        check("install stock: exit 0", proc.returncode == 0,
              (proc.stdout + proc.stderr).strip()[-200:])
        check("install stock: mock received the exact bytes (sha256)",
              f"upload:fw-image.tar.gz:{fw_sha}" in log_lines())

        # -- 5. install: dashd path via the documented endpoint -----------
        proc = run_cli(["fw", "install", DASHD_IP, str(fw_file),
                        "--http-port", str(DASHD_PORT),
                        "--cgminer-port", DEAD_CGMINER,
                        "--api-key", "mock-api-key",
                        "--yes", "--wait-minutes", "0"], shim_env)
        check("install dashd: exit 0", proc.returncode == 0,
              (proc.stdout + proc.stderr).strip()[-200:])
        state = json.loads(dashd_state.read_text(encoding="utf-8"))
        updates = state.get("firmware_updates") or []
        check("install dashd: /firmware/update got the exact bytes",
              bool(updates) and updates[-1]["filename"] == "fw-image.tar.gz"
              and updates[-1]["sha256"] == fw_sha,
              json.dumps(updates[-1]) if updates else "no updates recorded")

        # -- unlock fixtures ----------------------------------------------
        payload_dir = tmp / "payload"
        payload_dir.mkdir()
        first_bytes = b"first-bmu-payload\n" * 4
        second_bytes = b"second-bmu-payload\n" * 4
        (payload_dir / "update_first.bmu").write_bytes(first_bytes)
        (payload_dir / "update_second.bmu").write_bytes(second_bytes)
        first_sha = hashlib.sha256(first_bytes).hexdigest()
        second_sha = hashlib.sha256(second_bytes).hexdigest()
        empty_payload = tmp / "payload-empty"
        empty_payload.mkdir()
        unlock_argv = ["fw", "unlock", STOCK_IP,
                       "--http-port", str(STOCK_PORT),
                       "--cgminer-port", DEAD_CGMINER]

        def unlock_refused(label, argv, env, stdin_text):
            before = len(log_lines())
            proc = run_cli(argv, env, stdin_text)
            after = len(log_lines())
            check(f"unlock refused ({label}): exit != 0",
                  proc.returncode != 0, proc.stderr.strip()[:160])
            check(f"unlock refused ({label}): ZERO requests hit the mock",
                  after == before, f"log lines {before} -> {after}")

        # 6a. no --experimental-unlock flag
        unlock_refused("no flag",
                       unlock_argv + ["--payload-dir", str(payload_dir)],
                       shim_env, STOCK_IP + "\n")
        # 6b. flag but no BEESKY_ALLOW_UNLOCK=1
        unlock_refused("no env",
                       unlock_argv + ["--payload-dir", str(payload_dir),
                                      "--experimental-unlock"],
                       shim_env, STOCK_IP + "\n")
        # 6c. flag + env but typed confirmation does not match the IP
        env_gate = dict(shim_env)
        env_gate["BEESKY_ALLOW_UNLOCK"] = "1"
        unlock_refused("wrong typed IP",
                       unlock_argv + ["--payload-dir", str(payload_dir),
                                      "--experimental-unlock"],
                       env_gate, "khong-phai-ip-nay\n")
        # 6d. flag + env + typed IP but payload files missing
        proc = run_cli(unlock_argv + ["--payload-dir", str(empty_payload),
                                      "--experimental-unlock"],
                       env_gate, STOCK_IP + "\n")
        check("unlock refused (missing payload): clear error, no requests",
              proc.returncode != 0 and "update_first.bmu" in proc.stderr)

        # -- 7. unlock: all gates -> the recovered sequence, in order -----
        base = len(log_lines())
        proc = run_cli(unlock_argv + ["--payload-dir", str(payload_dir),
                                      "--experimental-unlock"],
                       env_gate, STOCK_IP + "\n")
        check("unlock full: exit 0 + success banner",
              proc.returncode == 0 and "UNLOCK THÀNH CÔNG" in proc.stdout,
              (proc.stdout + proc.stderr).strip()[-300:])
        lines = log_lines()[base:]

        def idx(pred, start=0):
            for i in range(start, len(lines)):
                if pred(lines[i]):
                    return i
            return -1

        i_ident = idx(lambda l: l == "http:GET /cgi-bin/miner_type.cgi")
        i_first = idx(lambda l: l == f"upload:update_first.bmu:{first_sha}")
        i_kill = idx(lambda l: l.startswith("ssh:") and "kill" in l)
        i_second = idx(lambda l: l == f"upload:update_second.bmu:{second_sha}")
        i_marker = idx(lambda l: l == "http:patch_success:ok")
        check("unlock order: identify -> first.bmu -> kill -> second.bmu "
              "-> patch marker",
              -1 < i_ident < i_first < i_kill < i_second < i_marker,
              f"indices ident={i_ident} first={i_first} kill={i_kill} "
              f"second={i_second} marker={i_marker}")
        check("unlock race: kill landed inside the first-upload window",
              "first-upload-window:marker" in lines)
    finally:
        for server in servers:
            server.terminate()
        for server in servers:
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()

    if FAILURES:
        print(f"\nFIRMWARE TEST FAILED ({len(FAILURES)}): {FAILURES}")
        return 1
    print("\nFIRMWARE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
