"""BeeSky Agent — the standalone farm-agent app (v0.14).

    beesky-agent                 open the config window
    beesky-agent run             run the agent loop from the saved
                                 config (CLI flags override fields)
    beesky-agent test            one ingest cycle from the config;
                                 prints OK/FAIL, exit code follows
    beesky-agent install-task    Windows: Scheduled Task "BeeSky
    beesky-agent remove-task     Agent" running `beesky-agent run`
                                 at startup (schtasks)

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
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from .agent_config import AgentConfig, default_config_path

TASK_NAME = "BeeSky Agent"

USAGE = """\
BeeSky Agent — agent tại trại (đẩy số liệu lên BeeSky Cloud)

  beesky-agent                 mở cửa sổ cấu hình
  beesky-agent run             chạy agent theo cấu hình đã lưu
                               (cờ dòng lệnh ghi đè từng trường)
  beesky-agent test            chạy thử một vòng đẩy số liệu,
                               in OK/FAIL (mã thoát 0/1)
  beesky-agent install-task    bật tự khởi động (Windows Scheduled
  beesky-agent remove-task     Task "BeeSky Agent"); gỡ bằng remove-task

Cấu hình: beesky/agent_config.py — mặc định %APPDATA%\\BeeSky\\
agent-config.json trên Windows, ~/.beesky/agent-config.json nơi khác,
hoặc $BEESKY_AGENT_CONFIG. Xem docs/agent-app.md.
"""


# ---------------------------------------------------------------------------
# service construction — one path for run/test (and the GUI's test button)
# ---------------------------------------------------------------------------

def build_service(cfg: AgentConfig):
    """AgentService for *cfg*, scanning through the CLI pipeline.

    Mirrors cli.cmd_agent's construction (same scan namespace, same
    creds dict) so config-driven and command-line agents are the
    same agent.
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
                        update_url_base=cfg.update_url)


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
    return parser


def _resolve(args: argparse.Namespace) -> AgentConfig:
    cfg = _overlay(_load_config(args.config), args)
    return cfg


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = _resolve(args)
    missing = cfg.missing_fields()
    if missing:
        print("agent: chưa đủ cấu hình — còn thiếu: "
              + ", ".join(missing)
              + "\nMở `beesky-agent` (không tham số) để cấu hình "
                "trong cửa sổ, hoặc truyền đủ cờ dòng lệnh.",
              file=sys.stderr)
        return 2
    service = build_service(cfg)
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


def agent_command(config_path: str | Path | None = None) -> str:
    """The command line the Scheduled Task runs at startup.

    The config path is baked in explicitly: an ONSTART task does not
    run as the operator, so its %APPDATA% would NOT be the folder the
    config window wrote to. Frozen: the exe itself; from source: the
    interpreter + module.
    """
    parts: list[str] = []
    if getattr(sys, "frozen", False):
        parts.append(f'"{sys.executable}"')
    else:
        parts += [f'"{sys.executable}"', "-m", "beesky.agent_app"]
    parts.append("run")
    if config_path is not None:
        parts.append(f'--config "{Path(config_path)}"')
    return " ".join(parts)


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
    "với cùng dòng lệnh.")


def install_task(config_path: str | Path | None = None) -> tuple[bool, str]:
    """Create/update the ONSTART task; (ok, message).

    ONSTART task creation usually needs an elevated prompt on
    Windows — schtasks' own error is surfaced verbatim so the
    operator sees exactly that.
    """
    if not _is_windows():
        return False, _NON_WINDOWS_TASK_NOTE
    cfg_path = Path(config_path) if config_path is not None \
        else default_config_path()
    command = agent_command(cfg_path)
    result = subprocess.run(
        ["schtasks", "/Create", "/TN", TASK_NAME, "/TR", command,
         "/SC", "ONSTART", "/F"],
        capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return False, (f"schtasks thất bại: {detail}\n"
                       "Gợi ý: tạo tác vụ lúc khởi động máy thường "
                       "cần quyền admin — mở app bằng 'Run as "
                       "administrator' rồi bấm lại.")
    note = ""
    if not cfg_path.exists():
        note = (f"\nLưu ý: chưa có file cấu hình tại {cfg_path} — "
                "mở app và Lưu cấu hình trước khi khởi động lại máy.")
    return True, (f"Đã tạo Scheduled Task {TASK_NAME!r}: {command}"
                  f"{note}")


def remove_task() -> tuple[bool, str]:
    """Delete the ONSTART task; (ok, message)."""
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
    ok, message = install_task(args.config)
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
    # Same cp1252 guard as beesky.cli.main: Vietnamese output must
    # not crash a legacy-codepage Windows console.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
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
