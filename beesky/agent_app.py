"""BeeSky Agent — the standalone farm-agent app (v0.14).

    beesky-agent                 open the config window
    beesky-agent run             run the agent loop from the saved
                                 config (CLI flags override fields)
    beesky-agent test            one ingest cycle from the config;
                                 prints OK/FAIL, exit code follows
    beesky-agent install-task    Windows: Scheduled Task "BeeSky
    beesky-agent remove-task     Agent" (v2 — see below)

Until v0.13 the farm agent existed only as a subcommand of the main
tool (``beesky agent ...``) — same code path, still supported. This
app gives the agent its own exe + installer so a farm PC can run
*just* the agent: configure it once in the window (cloud URL, agent
key, site, scan target), test the uplink, flip on auto-start, and
forget it. Settings live in one JSON file — see
:mod:`beesky.agent_config` for the format, the default locations and
the security note (the file holds the agent key; it IS the
credential).

The loop itself is unchanged: :class:`beesky.agent.AgentService`
scanning through the shared CLI pipeline, so a config-driven agent
behaves byte-for-byte like the equivalent `beesky agent` command
(same ingest, events, remote actions and signed self-update channel
— the updater matches on the exe name, so ``beesky-agent.exe``
updates itself from the same signed manifest as ``beesky.exe``).

BACKGROUND MODEL (v0.16): the agent is meant to run *unattended*,
not in a console someone can close. The installer therefore ships a
windowless twin, ``beesky-agentw.exe`` (same code, ``console=False``),
and ``install-task`` registers the task from generated XML: SYSTEM
principal, BootTrigger (+30 s) and a LogonTrigger, hidden, restart
on failure every minute (×5). A background run:

  * never opens the config GUI (a bare ``beesky-agentw`` invocation
    with no arguments runs the agent instead of opening a window),
  * writes everything it would print to ``agent.log`` next to the
    config file (rotated at ~1 MB, one ``.old`` backup), scrubbed
    of the agent key — console runs mirror the same redacted output
    to the console AND the log,
  * rewrites ``agent-status.json`` next to the config after EVERY
    cycle ({ts, ok, miners, error, cloud_url, site}) — that file
    is what the config window's "Trạng thái chạy ngầm" card reads,
  * warns once per run when the cloud URL is plain ``http://`` to a
    non-local host (the key then travels unencrypted — use https).
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import xml.sax.saxutils
from pathlib import Path

from .agent import redact
from .agent_config import AgentConfig, default_config_path

TASK_NAME = "BeeSky Agent"
LOG_FILENAME = "agent.log"
STATUS_FILENAME = "agent-status.json"
LOG_CAP_BYTES = 1_000_000

USAGE = """\
BeeSky Agent — agent tại trại (đẩy số liệu lên BeeSky Cloud)

  beesky-agent                 mở cửa sổ cấu hình
  beesky-agent run             chạy agent theo cấu hình đã lưu
                               (cờ dòng lệnh ghi đè từng trường)
  beesky-agent run --background
                               chạy ngầm: không cửa sổ, ghi vào
                               agent.log cạnh file cấu hình (chế độ
                               của beesky-agentw.exe / Scheduled Task)
  beesky-agent test            chạy thử một vòng đẩy số liệu,
                               in OK/FAIL (mã thoát 0/1)
  beesky-agent install-task    bật tự khởi động (Windows Scheduled
  beesky-agent remove-task     Task "BeeSky Agent"); gỡ bằng remove-task
                               (install-task --console: tác vụ trỏ
                               vào bản console để gỡ lỗi tại trại)

Cấu hình: beesky/agent_config.py — mặc định %APPDATA%\\BeeSky\\
agent-config.json trên Windows, ~/.beesky/agent-config.json nơi khác,
hoặc $BEESKY_AGENT_CONFIG. Xem docs/agent-app.md.
"""


# ---------------------------------------------------------------------------
# service construction — one path for run/test (and the GUI's test button)
# ---------------------------------------------------------------------------

def build_service(cfg: AgentConfig, status_hook=None):
    """AgentService for *cfg*, scanning through the CLI pipeline.

    Mirrors cli.cmd_agent's construction (same scan namespace, same
    creds dict) so config-driven and command-line agents are the
    same agent. *status_hook* (v0.16) is forwarded to the service
    and called after every pass as hook(ok, miners, error).
    """
    from .agent import AgentService
    from .cli import _scan_records

    scan_args = argparse.Namespace(
        target=cfg.target, timeout=cfg.timeout, workers=cfg.workers,
        user=cfg.user, password=cfg.password, api_key=cfg.api_key,
        token=cfg.token, http_port=cfg.http_port,
        cgminer_port=cfg.cgminer_port)
    creds = {"user": cfg.user, "password": cfg.password,
             "api_key": cfg.api_key, "token": cfg.token,
             "http_port": cfg.http_port,
             "cgminer_port": cfg.cgminer_port,
             "timeout": max(cfg.timeout, 2.0)}
    return AgentService(lambda: _scan_records(scan_args),
                        cloud_url=cfg.cloud_url, key=cfg.key,
                        site=cfg.site, interval=cfg.interval,
                        notify_config=cfg.notify_config or {},
                        creds=creds, auto_update=cfg.auto_update,
                        update_url_base=cfg.update_url,
                        status_hook=status_hook)


def test_ingest(cfg: AgentConfig) -> tuple[bool, str]:
    """One real ingest cycle: scan once, push the snapshot.

    Returns (ok, human-readable verdict). This is the `test`
    subcommand and the config window's "Chạy thử" button — the
    cheapest end-to-end truth about URL + key + network there is.
    """
    missing = cfg.missing_fields()
    if missing:
        return False, ("chưa đủ cấu hình — còn thiếu: "
                       + ", ".join(missing))
    service = build_service(cfg)
    try:
        records = service._scan_fn()
    except Exception as exc:  # noqa: BLE001 — verdict, not a crash
        return False, f"quét thất bại: {exc}"
    if service._deliver_snapshot(records):
        return True, (f"đã đẩy snapshot {len(records)} máy "
                      f"lên {cfg.cloud_url} (site {cfg.site!r})")
    return False, ("cloud không nhận snapshot — kiểm tra Cloud URL, "
                   "agent key và đường mạng từ trại")


# ---------------------------------------------------------------------------
# background run support — status file, redacted log, https warning
# ---------------------------------------------------------------------------

def status_file_path(config_path: str | Path) -> Path:
    """agent-status.json lives next to the active config file."""
    return Path(config_path).parent / STATUS_FILENAME


def log_file_path(config_path: str | Path) -> Path:
    """agent.log lives next to the active config file."""
    return Path(config_path).parent / LOG_FILENAME


def read_status(config_path: str | Path) -> dict | None:
    """The last written cycle status, or None (never ran / broken)."""
    try:
        data = json.loads(
            status_file_path(config_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_status(config_path: str | Path, cfg: AgentConfig,
                 ok: bool, miners: int, error: str | None) -> None:
    """Rewrite agent-status.json atomically (temp file + replace).

    Called after EVERY agent cycle through the service's status
    hook. A failed write is swallowed: status reporting must never
    take the monitoring loop down with it.
    """
    payload = {
        "ts": time.time(),
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ok": bool(ok),
        "miners": int(miners),
        "error": error,
        "cloud_url": cfg.cloud_url,
        "site": cfg.site,
    }
    path = status_file_path(config_path)
    tmp = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(payload, ensure_ascii=False,
                                  indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


def make_status_hook(cfg: AgentConfig, config_path: Path):
    def hook(ok: bool, miners: int, error: str | None) -> None:
        write_status(config_path, cfg, ok, miners, error)
    return hook


class _LogSink:
    """The shared agent.log appender with ~1 MB rotation.

    One sink per run: stdout and stderr writers share it, so the
    file is opened once and rotation (rename to agent.log.old,
    start fresh) cannot race between the two streams. All failures
    are swallowed — an unwritable log must not kill the agent.
    """

    def __init__(self, path: Path):
        self._path = Path(path)
        self._file = None
        self._open()

    def _open(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            if self._path.exists() \
                    and self._path.stat().st_size > LOG_CAP_BYTES:
                os.replace(self._path,
                           self._path.with_name(
                               self._path.name + ".old"))
            self._file = open(self._path, "a", encoding="utf-8",
                              errors="replace")
        except OSError:
            self._file = None

    def write(self, text: str) -> None:
        if self._file is None:
            return
        try:
            self._file.write(text)
            if self._file.tell() > LOG_CAP_BYTES:
                self._file.close()
                os.replace(self._path,
                           self._path.with_name(
                               self._path.name + ".old"))
                self._file = open(self._path, "a", encoding="utf-8",
                                  errors="replace")
        except (OSError, ValueError):
            pass

    def flush(self) -> None:
        if self._file is not None:
            try:
                self._file.flush()
            except (OSError, ValueError):
                pass


class _RedactingStream:
    """A sys.stdout/sys.stderr stand-in for `run` mode.

    Every write is scrubbed of the agent's secrets (the key itself
    and the full ``Bearer <key>`` header value), then mirrored to
    the shared agent.log sink and — in console mode — echoed to the
    real console stream. In background mode there is no echo: the
    log is the only output, so nothing can pop a console window.
    """

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, sink: _LogSink, secrets: list[str],
                 echo=None):
        self._sink = sink
        self._secrets = [s for s in secrets if s]
        self._echo = echo

    def write(self, text: str) -> int:
        if not text:
            return 0
        text = redact(text, *self._secrets)
        if self._echo is not None:
            try:
                self._echo.write(text)
            except Exception:  # noqa: BLE001 — output is best-effort
                pass
        self._sink.write(text)
        return len(text)

    def flush(self) -> None:
        if self._echo is not None:
            try:
                self._echo.flush()
            except Exception:  # noqa: BLE001
                pass
        self._sink.flush()

    def reconfigure(self, **_kwargs) -> None:
        pass  # encoding is fixed; main()'s cp1252 guard is a no-op

    def isatty(self) -> bool:
        return bool(self._echo is not None
                    and getattr(self._echo, "isatty", None)
                    and self._echo.isatty())


def _install_run_streams(cfg: AgentConfig, config_path: Path,
                         background: bool) -> None:
    """Route stdout/stderr through the redacting log machinery."""
    secrets = [cfg.key, f"Bearer {cfg.key}"]
    sink = _LogSink(log_file_path(config_path))
    if background:
        writer = _RedactingStream(sink, secrets)
        sys.stdout = writer
        sys.stderr = writer
    else:
        sys.stdout = _RedactingStream(sink, secrets, echo=sys.stdout)
        sys.stderr = _RedactingStream(sink, secrets, echo=sys.stderr)


def _running_windowed_exe() -> bool:
    """True when running frozen AS beesky-agentw (the windowless twin)."""
    if not getattr(sys, "frozen", False):
        return False
    return Path(sys.executable).stem.lower() == "beesky-agentw"


def _background_requested(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "background", False)) \
        or _running_windowed_exe()


_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def insecure_cloud_warning(cfg: AgentConfig) -> str | None:
    """Warning text when the cloud URL sends the key unencrypted.

    Plain ``http://`` to a non-local host means the agent key (and
    all farm telemetry) crosses the network in the clear. Advisory
    only — the agent still runs (a LAN-only cloud on http is a
    legitimate farm setup); the config window shows the same hint.
    """
    url = (cfg.cloud_url or "").strip()
    if not url.lower().startswith("http://"):
        return None
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    if host in _LOCAL_HOSTS:
        return None
    return ("Cloud URL dùng http:// không mã hoá — agent key sẽ đi "
            "qua mạng dạng rõ; nên dùng https:// cho cloud.")


# ---------------------------------------------------------------------------
# config loading + CLI overlay
# ---------------------------------------------------------------------------

def _load_config(path: str | None) -> AgentConfig:
    """Config from *path* (or the default location).

    A missing file is NOT an error by itself: start from an empty
    config so a full set of CLI flags can still drive `run`/`test`
    exactly like the old command line. A present-but-broken file is.
    """
    cfg_path = Path(path) if path else default_config_path()
    if not cfg_path.exists():
        return AgentConfig()
    return AgentConfig.load(cfg_path)


def _overlay(cfg: AgentConfig, args: argparse.Namespace) -> AgentConfig:
    """Apply the run/test CLI flags on top of *cfg* (None = keep)."""
    data = cfg.to_dict()
    mapping = {
        "target": "target", "cloud": "cloud_url", "key": "key",
        "site": "site", "interval": "interval", "timeout": "timeout",
        "workers": "workers", "user": "user", "password": "password",
        "api_key": "api_key", "token": "token",
        "http_port": "http_port", "cgminer_port": "cgminer_port",
        "update_url": "update_url", "auto_update": "auto_update",
    }
    for attr, field_name in mapping.items():
        value = getattr(args, attr, None)
        if value is not None:
            data[field_name] = value
    if getattr(args, "notify", None):
        from .cli import _load_notify_config
        notify = _load_notify_config(args.notify)
        if notify is None:
            raise ValueError(f"cannot read notify config {args.notify}")
        data["notify_config"] = notify
    return AgentConfig.from_dict(data)


def _run_parser(mode: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"beesky-agent {mode}",
        description=f"BeeSky Agent — {mode} theo cấu hình đã lưu "
                    "(cờ ghi đè từng trường của file cấu hình)")
    parser.add_argument("--config", metavar="FILE",
                        help="file cấu hình (mặc định: vị trí chuẩn "
                             "theo hệ điều hành / $BEESKY_AGENT_CONFIG)")
    parser.add_argument("target", nargs="?",
                        help="IP, CIDR hoặc dải IP (ghi đè cấu hình)")
    parser.add_argument("--cloud", metavar="URL", help="cloud base URL")
    parser.add_argument("--key", metavar="KEY", help="agent key")
    parser.add_argument("--site", metavar="NAME", help="tên trại")
    parser.add_argument("--interval", type=float,
                        help="giây giữa hai vòng quét")
    parser.add_argument("--notify", metavar="CONFIG",
                        help="file JSON kênh cảnh báo tại trại")
    parser.add_argument("--auto-update", action="store_true",
                        default=None,
                        help="tự áp bản cập nhật đã ký (mặc định lấy "
                             "theo cấu hình)")
    parser.add_argument("--update-url", metavar="URL",
                        help="base URL của kênh cập nhật")
    parser.add_argument("--timeout", type=float,
                        help="timeout mỗi lần dò máy (giây)")
    parser.add_argument("--workers", type=int, help="số luồng dò tối đa")
    parser.add_argument("--user", help="user web firmware gốc")
    parser.add_argument("--password", help="mật khẩu web firmware gốc")
    parser.add_argument("--api-key", metavar="KEY",
                        help="header x-api-key cho dashd (VNish)")
    parser.add_argument("--token", metavar="JWT",
                        help="bearer token cho dashd (VNish)")
    parser.add_argument("--http-port", type=int,
                        help="cổng HTTP của API máy đào")
    parser.add_argument("--cgminer-port", type=int,
                        help="cổng RPC cgminer")
    if mode == "run":
        parser.add_argument("--once", action="store_true",
                            help="chạy đúng một vòng rồi thoát")
        parser.add_argument("--background", action="store_true",
                            help="chạy ngầm: không console, mọi "
                                 "output vào agent.log (mặc định "
                                 "khi chạy bằng beesky-agentw.exe)")
    return parser


def _resolve(args: argparse.Namespace) -> AgentConfig:
    cfg = _overlay(_load_config(args.config), args)
    return cfg


def _config_path_for(args: argparse.Namespace) -> Path:
    return Path(args.config) if getattr(args, "config", None) \
        else default_config_path()


def _cmd_run(args: argparse.Namespace) -> int:
    cfg_path = _config_path_for(args)
    cfg = _resolve(args)
    background = _background_requested(args)
    # Streams FIRST: in background mode every message from here on
    # (missing-config errors included) must land in agent.log, not
    # in a console that does not exist.
    _install_run_streams(cfg, cfg_path, background)
    missing = cfg.missing_fields()
    if missing:
        print("agent: chưa đủ cấu hình — còn thiếu: "
              + ", ".join(missing)
              + "\nMở `beesky-agent` (không tham số) để cấu hình "
                "trong cửa sổ, hoặc truyền đủ cờ dòng lệnh.",
              file=sys.stderr)
        return 2
    warning = insecure_cloud_warning(cfg)
    if warning:
        print(f"agent: CẢNH BÁO {warning}", file=sys.stderr,
              flush=True)
    service = build_service(
        cfg, status_hook=make_status_hook(cfg, cfg_path))
    service.run(once=args.once)
    return 0


def _cmd_test(args: argparse.Namespace) -> int:
    cfg = _resolve(args)
    ok, verdict = test_ingest(cfg)
    stamp = time.strftime("%H:%M:%S")
    print(f"TEST {'OK' if ok else 'FAIL'} [{stamp}]: {verdict}")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Windows auto-start — Scheduled Task via schtasks
# ---------------------------------------------------------------------------

def _is_windows() -> bool:
    return sys.platform.startswith("win")


def _task_command_parts(config_path: str | Path | None = None,
                        windowed: bool = False,
                        exe_path: str | Path | None = None
                        ) -> tuple[str, str]:
    """(command, arguments) the Scheduled Task action runs.

    The config path is baked in explicitly: the task runs as
    SYSTEM, so its %APPDATA% would NOT be the folder the config
    window wrote to. *windowed* selects the windowless twin
    (frozen: beesky-agentw.exe next to beesky-agent.exe; from
    source on Windows: pythonw.exe next to python.exe) so the
    background agent never opens a console. *exe_path* is
    injectable for tests.
    """
    exe = Path(exe_path) if exe_path is not None \
        else Path(sys.executable)
    args: list[str] = []
    if getattr(sys, "frozen", False):
        if windowed and exe.stem.lower() == "beesky-agent":
            exe = exe.with_name(exe.stem + "w" + exe.suffix)
        command = str(exe)
    else:
        command = str(exe)
        if windowed and exe.stem.lower() == "python":
            command = str(exe.with_name("pythonw.exe"))
        args += ["-m", "beesky.agent_app"]
    args.append("run")
    if config_path is not None:
        args.append(f'--config "{Path(config_path)}"')
    return command, " ".join(args)


def agent_command(config_path: str | Path | None = None,
                  windowed: bool = False) -> str:
    """The full command line form of :func:`_task_command_parts`."""
    command, arguments = _task_command_parts(
        config_path, windowed=windowed)
    return f'"{command}" {arguments}'


def task_xml(config_path: str | Path | None = None,
             console: bool = False,
             exe_path: str | Path | None = None) -> str:
    """The Task Scheduler XML for the v2 background task.

    Registered via ``schtasks /Create /XML`` (the flat /TR form
    cannot express any of this): SYSTEM principal at the highest
    run level, a BootTrigger delayed 30 s plus the installing
    user's LogonTrigger, hidden, no execution time limit, restart
    on failure every minute up to 5 times, and battery settings
    that never stop the agent on a laptop. The action points at
    the WINDOWLESS exe — *console=True* is the farm-debugging
    escape hatch that points it at the console build instead.
    """
    cfg_path = Path(config_path) if config_path is not None \
        else default_config_path()
    command, arguments = _task_command_parts(
        cfg_path, windowed=not console, exe_path=exe_path)
    esc = xml.sax.saxutils.escape
    return f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>BeeSky Agent — quét máy đào tại trại, đẩy số liệu lên BeeSky Cloud. Chạy nền (ẩn) bằng beesky-agentw, tự khởi động lại khi lỗi; log + trạng thái nằm cạnh file cấu hình (agent.log, agent-status.json).</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT30S</Delay>
    </BootTrigger>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>5</Count>
    </RestartOnFailure>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{esc(command)}</Command>
      <Arguments>{esc(arguments)}</Arguments>
    </Exec>
  </Actions>
</Task>
'''


def task_installed() -> bool:
    """True when the "BeeSky Agent" task exists (Windows only)."""
    if not _is_windows():
        return False
    result = subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME],
                            capture_output=True)
    return result.returncode == 0


_NON_WINDOWS_TASK_NOTE = (
    "Tự khởi động bằng Scheduled Task chỉ có trên Windows.\n"
    "Trên Linux, dùng systemd, ví dụ /etc/systemd/system/"
    "beesky-agent.service:\n"
    "  [Service]\n"
    "  ExecStart=beesky-agent run --config <đường-dẫn-agent-config.json>\n"
    "  Restart=always\n"
    "  [Install]\n"
    "  WantedBy=multi-user.target\n"
    "rồi `systemctl enable --now beesky-agent` — hoặc cron @reboot "
    "với cùng dòng lệnh. (Trên Windows tác vụ trỏ vào "
    "beesky-agentw.exe — bản chạy ngầm không cửa sổ.)")


def install_task(config_path: str | Path | None = None,
                 console: bool = False) -> tuple[bool, str]:
    """Create/update the background task from XML; (ok, message).

    The task runs as SYSTEM, so registration needs an elevated
    prompt on Windows — schtasks' own error is surfaced verbatim
    so the operator sees exactly that. *console* points the task
    at the console exe (visible logs) for debugging at the farm.
    """
    if not _is_windows():
        return False, _NON_WINDOWS_TASK_NOTE
    cfg_path = Path(config_path) if config_path is not None \
        else default_config_path()
    xml_path = Path(tempfile.gettempdir()) / "beesky-agent-task.xml"
    try:
        # schtasks /XML expects the file in UTF-16 (as declared).
        xml_path.write_text(task_xml(cfg_path, console=console),
                            encoding="utf-16")
        result = subprocess.run(
            ["schtasks", "/Create", "/TN", TASK_NAME,
             "/XML", str(xml_path), "/F"],
            capture_output=True, text=True)
    finally:
        try:
            xml_path.unlink()
        except OSError:
            pass
    command = agent_command(cfg_path, windowed=not console)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return False, (f"schtasks thất bại: {detail}\n"
                       "Gợi ý: đăng ký tác vụ chạy bằng SYSTEM "
                       "thường cần quyền admin — mở app bằng 'Run "
                       "as administrator' rồi bấm lại.")
    note = ""
    if not cfg_path.exists():
        note = (f"\nLưu ý: chưa có file cấu hình tại {cfg_path} — "
                "mở app và Lưu cấu hình trước khi khởi động lại máy.")
    return True, (f"Đã tạo Scheduled Task {TASK_NAME!r} (SYSTEM, "
                  f"chạy ngầm, tự khởi động lại khi lỗi): {command}"
                  f"{note}")


def remove_task() -> tuple[bool, str]:
    """Delete the background task; (ok, message)."""
    if not _is_windows():
        return False, _NON_WINDOWS_TASK_NOTE
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return False, f"schtasks thất bại: {detail}"
    return True, f"Đã gỡ Scheduled Task {TASK_NAME!r}."


def _cmd_install_task(args: argparse.Namespace) -> int:
    ok, message = install_task(args.config,
                               console=getattr(args, "console", False))
    print(message)
    return 0 if ok or not _is_windows() else 1


def _cmd_remove_task(args: argparse.Namespace) -> int:
    ok, message = remove_task()
    print(message)
    return 0 if ok or not _is_windows() else 1


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    # A windowed frozen exe (beesky-agentw) has NO console streams:
    # sys.stdout/sys.stderr are None there, and any print would
    # crash. Stand-ins keep help/errors harmless until `run`
    # installs the real (log) streams.
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()
    # Same cp1252 guard as beesky.cli.main: Vietnamese output must
    # not crash a legacy-codepage Windows console.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        if _running_windowed_exe():
            # The windowless twin never opens the config GUI: a
            # bare launch IS the background agent (default config).
            return _cmd_run(_run_parser("run").parse_args([]))
        from .agent_gui import run_config_gui
        return run_config_gui()
    mode, rest = argv[0], argv[1:]
    try:
        if mode == "run":
            return _cmd_run(_run_parser("run").parse_args(rest))
        if mode == "test":
            return _cmd_test(_run_parser("test").parse_args(rest))
        if mode in ("install-task", "remove-task"):
            parser = argparse.ArgumentParser(
                prog=f"beesky-agent {mode}")
            parser.add_argument("--config", metavar="FILE",
                                  help="file cấu hình ghi vào tác vụ "
                                       "(mặc định: vị trí chuẩn)")
            if mode == "install-task":
                parser.add_argument(
                    "--console", action="store_true",
                    help="tác vụ trỏ vào beesky-agent.exe (console, "
                         "thấy log) thay vì bản chạy ngầm "
                         "beesky-agentw.exe — để gỡ lỗi tại trại")
            args = parser.parse_args(rest)
            if mode == "install-task":
                return _cmd_install_task(args)
            return _cmd_remove_task(args)
    except ValueError as exc:
        print(f"agent: {exc}", file=sys.stderr)
        return 2
    if mode in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    print(f"agent: unknown mode {mode!r}\n\n{USAGE}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
