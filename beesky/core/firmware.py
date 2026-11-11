"""Firmware install + EXPERIMENTAL locked-stock unlock (v0.11).

THỬ NGHIỆM / EXPERIMENTAL. Read docs/firmware.md before touching a real
miner, and always try a new firmware from an SD-card boot first — the
recovery path for a bad NAND flash is reinstalling the stock firmware
(or booting the stock SD image), so keep that media at hand.

What lives here:

``identify`` — what firmware is this miner running? Probes with the
usual adapter chain (discover.probe_host); for stock Bitmain it also
reads ``/cgi-bin/miner_type.cgi`` (digest auth) and, over SSH,
``cat /usr/bin/compile_time``. The verdict is one of four plain lines:

  * ``VNish/dashd — cài firmware qua API được``
  * ``stock cũ / đã mở SSH``       (SSH answers → not a locked build)
  * ``stock khoá (cần unlock)``   (web answers, SSH does not)
  * ``không rõ``

``install`` — two real paths, auto-picked by the probed source:

  * dashd/VNish: ``POST /api/v1/firmware/update`` — taken from the
    firmware's own OpenAPI document (api-doc.json): multipart/form-data,
    file field ``file`` (binary, required), optional plain field
    ``keep_settings`` ("true"/"false"), bearer JWT or ``x-api-key``
    auth; a 200 reply is a RebootAfter ``{"after": seconds}``.
  * stock Bitmain: multipart POST of the file to
    ``/cgi-bin/upgrade.cgi`` behind the stock digest auth (field
    ``file``, the stock upgrade form's field name).

``unlock`` — the locked-stock recipe recovered from the HashCore
Toolkit deep dive (research/hashcore/UNLOCK-DEEP.md), as a staged,
verified sequence that stops at the first failed stage:

  1. identify + version gate: miner_type.cgi over HTTP, compile_time
     over SSH — the Toolkit gates the stock build on its compile time;
     the exact supported-version window was NOT recovered, so BeeSky
     shows the compile time and refuses to continue without it, leaving
     the go/no-go to the operator's typed confirmation (CLI gate).
  2. upload ``update_first.bmu`` via /cgi-bin/upgrade.cgi while racing
     the signature check: over SSH, repeatedly ``kill -9`` the
     ``openssl dgst -sha256 -verify /etc/bitmain-adv.pub`` process for
     as long as the upload runs (--race-delay-ms before the first kill;
     no timing value was recovered — 0 by default, first real run is a
     calibration). The race retries at most 10 times — the bound was
     recovered from the Toolkit's Rust core in v0.35
     (docs/unlock-payload-mapping.md §2.1); the inter-attempt delay
     formula was not recoverable and stays UNKNOWN.
  3. upload ``update_second.bmu`` the same way.
  4. poll the success marker ``/cgi-bin/patch_success.cgi``.
  5. cleanup (best effort): remove /nvdata/update.log and /tmp/tmpfw —
     the recipe also restores the access files (/etc/passwd,
     /etc/sudoers.dist, /config/passwd); that step belongs to the
     payload, not to BeeSky, and is only noted here.

The .bmu payload files are owner-supplied (--payload-dir); BeeSky ships
NONE — they live inside firmware packages, and their container format
was not recovered either.

SSH: the stdlib has no SSH client, so SshRunner shells out to the
system ``ssh`` binary (key auth, BatchMode) — or to ``sshpass -e`` when
a password is supplied and sshpass exists. Credentials come only from
the CLI flags (--ssh-user / --ssh-password-env / --ssh-key); nothing is
hardcoded here. With no ssh binary on PATH, SSH-dependent commands say
so and stop.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from .bitmain import BitmainClient, BitmainError
from .dashd import DashdClient, DashdError
from .discover import probe_host

UPGRADE_CGI = "/cgi-bin/upgrade.cgi"
MINER_TYPE_CGI = "/cgi-bin/miner_type.cgi"
PATCH_SUCCESS_CGI = "/cgi-bin/patch_success.cgi"
DASHD_UPDATE_PATH = "/firmware/update"  # POST /api/v1/firmware/update
COMPILE_TIME_CMD = "cat /usr/bin/compile_time"
# The verify process the race kills, exactly as named in the deep dive.
VERIFY_PROCESS_PATTERN = "openssl dgst -sha256 -verify /etc/bitmain-adv.pub"
KILL_VERIFY_CMD = f"kill -9 $(pgrep -f '{VERIFY_PROCESS_PATTERN}')"
CLEANUP_CMD = "rm -f /nvdata/update.log; rm -rf /tmp/tmpfw"
# The dedicated multipart boundary the Toolkit's Rust unlock core uses
# for its .bmu uploads (btm-lib, unlock/upgrade_cgi.rs — UNLOCK-DEEP.md).
UNLOCK_BOUNDARY = "sshPayloadThenUpgradeCgiUnlockBoundary"
FIRST_BMU = "update_first.bmu"
SECOND_BMU = "update_second.bmu"

VERDICT_VNISH = "VNish/dashd — cài firmware qua API được"
VERDICT_STOCK_OPEN = "stock cũ / đã mở SSH"
VERDICT_STOCK_LOCKED = "stock khoá (cần unlock)"
VERDICT_UNKNOWN = "không rõ"


class FirmwareError(Exception):
    """A firmware operation cannot proceed (missing tool, bad payload…)."""


class SshUnavailable(FirmwareError):
    """No usable ssh client (or no sshpass for password auth)."""


# ---------------------------------------------------------------------------
# SSH runner (system ssh binary; shim-able in tests via PATH)
# ---------------------------------------------------------------------------

@dataclass
class SshResult:
    rc: int
    out: str
    err: str


class SshRunner:
    """Run one command on a miner over the system ``ssh`` binary."""

    def __init__(self, host: str, user: str = "root",
                 password: str | None = None, port: int = 22,
                 timeout: float = 15.0, key_file: str | None = None):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.timeout = timeout
        self.key_file = key_file

    @staticmethod
    def binary() -> str | None:
        return shutil.which("ssh")

    def available(self) -> bool:
        return self.binary() is not None

    def run(self, command: str, timeout: float | None = None) -> SshResult:
        ssh = self.binary()
        if not ssh:
            raise SshUnavailable(
                "không tìm thấy chương trình 'ssh' trên máy này — "
                "cài OpenSSH client rồi thử lại")
        argv: list[str] = []
        env = None
        if self.password:
            sshpass = shutil.which("sshpass")
            if not sshpass:
                raise SshUnavailable(
                    "đăng nhập SSH bằng mật khẩu cần chương trình 'sshpass' "
                    "(chưa có trên máy này) — dùng --ssh-key thay thế")
            argv += [sshpass, "-e"]
            env = dict(os.environ)
            env["SSHPASS"] = self.password
        limit = timeout if timeout is not None else self.timeout
        argv += [ssh,
                 "-o", "StrictHostKeyChecking=accept-new",
                 "-o", f"ConnectTimeout={max(1, int(limit))}"]
        if self.password:
            argv += ["-o", "NumberOfPasswordPrompts=1"]
        else:
            # Key/agent auth only — never block on an interactive prompt.
            argv += ["-o", "BatchMode=yes"]
        if self.key_file:
            argv += ["-i", self.key_file]
        argv += ["-p", str(self.port), f"{self.user}@{self.host}", command]
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=limit + 10, env=env)
        return SshResult(proc.returncode, proc.stdout.strip(),
                         proc.stderr.strip())


# ---------------------------------------------------------------------------
# identify
# ---------------------------------------------------------------------------

def identify(ip: str, *, http_port: int = 80, cgminer_port: int = 4028,
             user: str = "root", password: str = "root",
             api_key: str | None = None, token: str | None = None,
             ssh: SshRunner | None = None, timeout: float = 3.0) -> dict:
    """Identify one miner's firmware flavour; see the module docstring."""
    info: dict = {"ip": ip, "source": None, "model": None,
                  "miner_type": None, "compile_time": None,
                  "ssh": "not-tried", "verdict": VERDICT_UNKNOWN,
                  "notes": []}
    cand = probe_host(ip, timeout=timeout, http_port=http_port,
                      cgminer_port=cgminer_port, username=user,
                      password=password, api_key=api_key, token=token)
    if cand is None:
        info["notes"].append(
            "host không trả lời cgminer RPC / dashd / stock CGI nào")
        return info
    info["source"] = cand.source
    info["model"] = cand.model
    if cand.source == "vnish":
        info["verdict"] = VERDICT_VNISH
        return info
    if cand.source != "stock":
        info["notes"].append(
            f"chỉ thấy nguồn {cand.source} — không đủ thông tin để "
            "kết luận firmware")
        return info

    client = BitmainClient(ip, port=http_port, timeout=max(timeout, 2.0),
                           username=user, password=password)
    try:
        miner_type = client.get_text(MINER_TYPE_CGI).strip()
        if miner_type:
            info["miner_type"] = miner_type
            info["model"] = miner_type
    except BitmainError as exc:
        info["notes"].append(f"miner_type.cgi: {exc}")

    runner = ssh if ssh is not None else SshRunner(ip)
    if not runner.available():
        info["ssh"] = "no-binary"
        info["notes"].append(
            "không có ssh client trên máy này — không kết luận được "
            "stock khoá hay đã mở SSH")
        return info
    try:
        result = runner.run(COMPILE_TIME_CMD)
    except (SshUnavailable, subprocess.TimeoutExpired, OSError) as exc:
        info["ssh"] = "failed"
        info["verdict"] = VERDICT_STOCK_LOCKED
        info["notes"].append(f"SSH không vào được: {exc}")
        return info
    if result.rc == 0 and result.out:
        info["ssh"] = "ok"
        info["compile_time"] = result.out
        info["verdict"] = VERDICT_STOCK_OPEN
    else:
        info["ssh"] = "failed"
        info["verdict"] = VERDICT_STOCK_LOCKED
        detail = result.err or f"ssh thoát với mã {result.rc}"
        info["notes"].append(f"SSH không vào được: {detail}")
    return info


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------

def file_info(path: str | Path) -> tuple[int, str]:
    """(size_bytes, sha256_hex) of a local firmware file."""
    digest = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()


def install_dashd(ip: str, fw_path: str | Path, *, http_port: int = 80,
                  api_key: str | None = None, token: str | None = None,
                  dashd_password: str | None = None,
                  keep_settings: str | None = None,
                  timeout: float = 120.0) -> tuple[bool, str]:
    """Upload firmware to a VNish/dashd miner (documented endpoint)."""
    client = DashdClient(ip, port=http_port, timeout=timeout,
                         api_key=api_key, token=token)
    data = Path(fw_path).read_bytes()
    extra = {"keep_settings": keep_settings} if keep_settings else None
    try:
        reply = client.post_multipart(
            DASHD_UPDATE_PATH, "file", Path(fw_path).name, data,
            extra_fields=extra, password=dashd_password)
    except DashdError as exc:
        return False, f"dashd firmware update failed: {exc}"
    after = reply.get("after") if isinstance(reply, dict) else None
    if isinstance(after, (int, float)):
        return True, (f"dashd accepted the firmware "
                      f"(POST /api/v1/firmware/update -> 200, "
                      f"system reboots in {after:g}s)")
    return True, "dashd accepted the firmware (POST /api/v1/firmware/update -> 200)"


def install_stock(ip: str, fw_path: str | Path, *, http_port: int = 80,
                  user: str = "root", password: str = "root",
                  timeout: float = 120.0) -> tuple[bool, str]:
    """Upload firmware to a stock Bitmain miner via upgrade.cgi."""
    client = BitmainClient(ip, port=http_port, timeout=timeout,
                           username=user, password=password)
    data = Path(fw_path).read_bytes()
    try:
        status, body = client.post_multipart(
            UPGRADE_CGI, "file", Path(fw_path).name, data)
    except BitmainError as exc:
        return False, f"stock firmware upload failed: {exc}"
    if status == 200:
        return True, ("stock firmware accepted the upload "
                      "(POST /cgi-bin/upgrade.cgi -> 200); the miner "
                      "verifies and reboots on its own schedule")
    snippet = body.decode("utf-8", errors="replace").strip()[:200]
    return False, f"stock upgrade.cgi -> HTTP {status}" + \
        (f": {snippet}" if snippet else "")


def wait_back(ip: str, *, minutes: float, http_port: int = 80,
              cgminer_port: int = 4028, user: str = "root",
              password: str = "root", api_key: str | None = None,
              token: str | None = None, poll_s: float = 10.0,
              log=print) -> dict | None:
    """Poll until the miner answers again after an install (or time out).

    Returns the final probe summary ``{"source":..., "model":...}`` —
    with ``"went_down": bool`` — or None when the miner never answered.
    """
    if minutes <= 0:
        log("bỏ qua bước chờ máy lên lại (--wait-minutes 0)")
        return None
    deadline = time.time() + minutes * 60
    time.sleep(5)
    saw_down = False
    last: dict | None = None
    while time.time() < deadline:
        cand = probe_host(ip, timeout=2.0, http_port=http_port,
                          cgminer_port=cgminer_port, username=user,
                          password=password, api_key=api_key, token=token)
        if cand is None:
            if not saw_down:
                log("  …máy đã ngắt kết nối (đang reboot / nạp firmware)")
            saw_down = True
        else:
            last = {"source": cand.source, "model": cand.model,
                    "went_down": saw_down}
            if saw_down:
                log(f"  …máy đã trả lời lại: source={cand.source} "
                    f"model={cand.model}")
                return last
        time.sleep(poll_s)
    if last is not None:
        log("  …hết giờ chờ: máy vẫn trả lời nhưng không hề mất kết nối "
            "trong lúc chờ (có thể chưa reboot)")
    else:
        log("  …hết giờ chờ: máy vẫn chưa trả lời lại")
    return last


# ---------------------------------------------------------------------------
# unlock (EXPERIMENTAL) — staged sequence; see the module docstring
# ---------------------------------------------------------------------------

def payload_paths(payload_dir: str | Path) -> tuple[Path, Path]:
    base = Path(payload_dir)
    return base / FIRST_BMU, base / SECOND_BMU


def unlock(ip: str, payload_dir: str | Path, *, http_port: int = 80,
           user: str = "root", password: str = "root",
           ssh: SshRunner | None = None, race_delay_ms: int = 0,
           marker_timeout_s: float = 120.0,
           log=print) -> tuple[bool, list[tuple[str, bool, str]]]:
    """Run the recovered locked-stock unlock sequence, stage by stage.

    Returns (ok, stages) where each stage is (name, ok, message). Stops
    at the first failed stage. The caller (CLI) owns the hard gates —
    this function still re-checks the payload files before any I/O.
    """
    stages: list[tuple[str, bool, str]] = []

    def stage(name: str, ok: bool, message: str) -> bool:
        stages.append((name, ok, message))
        log(f"  [{'OK' if ok else 'FAIL'}] {name}: {message}")
        return ok

    first, second = payload_paths(payload_dir)
    missing = [p.name for p in (first, second) if not p.is_file()]
    if missing:
        stage("payload", False,
              f"thiếu file payload trong {payload_dir}: "
              f"{', '.join(missing)} — BeeSky không kèm sẵn file .bmu, "
              "chúng nằm trong gói firmware; xem docs/firmware.md")
        return False, stages

    runner = ssh if ssh is not None else SshRunner(ip)
    if not runner.available():
        stage("identify", False,
              "không có ssh client trên máy này — unlock cần SSH cho "
              "bước đua kill tiến trình kiểm chữ ký")
        return False, stages

    client = BitmainClient(ip, port=http_port, timeout=60.0,
                           username=user, password=password)

    # -- stage 1: identify + version gate ---------------------------------
    try:
        miner_type = client.get_text(MINER_TYPE_CGI).strip()
    except BitmainError as exc:
        stage("identify", False, f"không đọc được miner_type.cgi: {exc}")
        return False, stages
    if not miner_type:
        stage("identify", False, "miner_type.cgi trả về rỗng")
        return False, stages
    try:
        result = runner.run(COMPILE_TIME_CMD)
    except (SshUnavailable, subprocess.TimeoutExpired, OSError) as exc:
        stage("identify", False, f"SSH đọc compile_time thất bại: {exc}")
        return False, stages
    if result.rc != 0 or not result.out:
        detail = result.err or f"ssh thoát với mã {result.rc}"
        stage("identify", False,
              f"không lấy được compile_time qua SSH ({detail}) — "
              "cổng phiên bản (version gate) không qua được, dừng")
        return False, stages
    compile_time = result.out
    stage("identify", True,
          f"{miner_type}; compile_time = {compile_time} "
          "(cửa sổ phiên bản hỗ trợ chưa khôi phục được từ Toolkit — "
          "số này chỉ để đối chiếu, quyết định thuộc về người chạy)")

    # -- stage 2: upload update_first.bmu + the signature-check race ------
    box: dict = {}

    def _upload_first() -> None:
        try:
            box["result"] = client.post_multipart(
                UPGRADE_CGI, "file", first.name, first.read_bytes(),
                boundary=UNLOCK_BOUNDARY)
        except Exception as exc:  # noqa: BLE001 — reported as a stage fail
            box["error"] = exc

    thread = threading.Thread(target=_upload_first, daemon=True)
    thread.start()
    if race_delay_ms > 0:
        time.sleep(race_delay_ms / 1000.0)
    kills = 0
    while thread.is_alive() and kills < 200:
        try:
            runner.run(KILL_VERIFY_CMD, timeout=10)
        except Exception:  # noqa: BLE001 — the race is best-effort per shot
            pass
        kills += 1
        if thread.is_alive():
            time.sleep(0.25)
    thread.join()
    if "error" in box:
        stage("upload-first", False,
              f"upload {FIRST_BMU} thất bại: {box['error']}")
        return False, stages
    status, body = box["result"]
    if status != 200:
        snippet = body.decode("utf-8", errors="replace").strip()[:200]
        stage("upload-first", False,
              f"upgrade.cgi -> HTTP {status} khi nhận {FIRST_BMU}"
              + (f": {snippet}" if snippet else ""))
        return False, stages
    stage("upload-first", True,
          f"{FIRST_BMU} accepted (HTTP 200); race: kill tiến trình "
          f"kiểm chữ ký đã bắn {kills} lần trong lúc upload")

    # -- stage 3: upload update_second.bmu ---------------------------------
    try:
        status, body = client.post_multipart(
            UPGRADE_CGI, "file", second.name, second.read_bytes(),
            boundary=UNLOCK_BOUNDARY)
    except BitmainError as exc:
        stage("upload-second", False, f"upload {SECOND_BMU} thất bại: {exc}")
        return False, stages
    if status != 200:
        snippet = body.decode("utf-8", errors="replace").strip()[:200]
        stage("upload-second", False,
              f"upgrade.cgi -> HTTP {status} khi nhận {SECOND_BMU}"
              + (f": {snippet}" if snippet else ""))
        return False, stages
    stage("upload-second", True, f"{SECOND_BMU} accepted (HTTP 200)")

    # -- stage 4: poll the success marker -----------------------------------
    deadline = time.time() + marker_timeout_s
    while True:
        try:
            if client.get_status_code(PATCH_SUCCESS_CGI) == 200:
                break
        except BitmainError:
            pass
        if time.time() >= deadline:
            stage("marker", False,
                  f"{PATCH_SUCCESS_CGI} không xuất hiện sau "
                  f"{marker_timeout_s:g}s — unlock chưa thành công; "
                  "đừng rút điện, kiểm tra lại payload và thử lại, hoặc "
                  "nạp firmware gốc / boot SD để khôi phục")
            return False, stages
        time.sleep(1.0)
    stage("marker", True,
          f"{PATCH_SUCCESS_CGI} -> 200 (patch marker present)")

    # -- stage 5: cleanup (best effort, per the recovered recipe) -----------
    try:
        runner.run(CLEANUP_CMD, timeout=10)
        stage("cleanup", True,
              "đã dọn /nvdata/update.log và /tmp/tmpfw; việc khôi phục "
              "access files (/etc/passwd, /etc/sudoers.dist, "
              "/config/passwd) thuộc về payload theo recipe gốc")
    except Exception as exc:  # noqa: BLE001 — cleanup must not fail the run
        stage("cleanup", True, f"cleanup best-effort lỗi (bỏ qua): {exc}")
    return True, stages
