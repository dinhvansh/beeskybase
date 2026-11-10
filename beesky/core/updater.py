"""Signed self-update channel (v0.10).

Every GitHub Release carries two extra assets next to the exes:

  * ``update-manifest.json`` — {version, published_at, files:
    [{name, url, sha256, size}]} describing that release, and
  * ``update-manifest.sig`` — an RSA PKCS#1 v1.5 / SHA-256 signature
    over the manifest bytes, made in CI with the owner's private key
    (GitHub secret ``UPDATE_SIGNING_KEY``; setup in docs/updating.md).

This module is the client half:

  * :func:`verify_signature` checks a manifest against the public
    key compiled into :mod:`beesky.core.update_key`. BeeSky is
    stdlib-only, so the RSA verification is hand-rolled pure Python:
    ``m = pow(sig, e, n)`` plus a byte-exact check of the PKCS#1
    v1.5 block (``00 01 FF.. 00 || DigestInfo(SHA-256) || digest``).
    RSA *verification* with a small public exponent is cheap and
    safe to implement; nothing here ever signs.
  * :func:`check` fetches manifest + signature, verifies FIRST, and
    only then compares versions. A tampered or unsigned manifest is
    refused, never parsed for decisions.
  * :func:`apply` downloads the file matching the running
    executable's name, verifies size + SHA-256 against the signed
    manifest, and only then swaps it in — the old file is kept as
    ``<name>.old`` until the swap has succeeded. On Windows a running
    exe cannot be overwritten, so the swap is finished by a
    ``beesky-swap.bat`` helper that waits for this process to exit,
    moves the verified file over, and optionally relaunches the exact
    same argv. On POSIX ``os.replace`` over the running binary is
    atomic and fine.

If ``update_key.UPDATE_RSA_N_HEX`` is None the channel is *not
configured*: every entry point reports that plainly instead of
fetching anything. Fetches connect directly (proxy env ignored),
like the rest of BeeSky's outbound calls — the URL is explicit
operator configuration.

Note: this manifest is BeeSky's OWN update channel. It is unrelated
to Windows Authenticode/SmartScreen reputation — that is the
separate eSigner code-signing feature (docs/signing.md).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .. import __version__ as CURRENT_VERSION
from . import update_key as _update_key

# Re-exported so tests (and only tests) can substitute a throwaway
# keypair at runtime; production code reads the compiled-in module.
UPDATE_RSA_N_HEX = _update_key.UPDATE_RSA_N_HEX
UPDATE_RSA_E = _update_key.UPDATE_RSA_E

DEFAULT_URL_BASE = ("https://github.com/dinhvansh/beeskybase"
                    "/releases/latest/download/")
ENV_URL_BASE = "BEESKY_UPDATE_URL"
MANIFEST_NAME = "update-manifest.json"
SIG_NAME = "update-manifest.sig"
FETCH_TIMEOUT_S = 15

# DER prefix of a DigestInfo wrapping a SHA-256 digest (RFC 8017):
# SEQUENCE { SEQUENCE { OID sha256, NULL }, OCTET STRING (32) }.
_SHA256_DER_PREFIX = bytes.fromhex(
    "3031300d060960864801650304020105000420")


# ---------------------------------------------------------------------------
# signature verification (pure-Python RSA verify)
# ---------------------------------------------------------------------------

def updates_enabled() -> bool:
    """True when a signing public key is compiled into this build."""
    return bool(UPDATE_RSA_N_HEX)


def verify_signature(manifest_bytes: bytes, sig_bytes: bytes) -> bool:
    """RSA PKCS#1 v1.5 / SHA-256 verify, byte-exact, pure Python.

    Returns False for *any* irregularity — wrong key state, wrong
    length, bad padding, digest mismatch — never raises.
    """
    if not updates_enabled():
        return False
    try:
        n = int(UPDATE_RSA_N_HEX, 16)
        e = int(UPDATE_RSA_E)
        k = (n.bit_length() + 7) // 8
        if len(sig_bytes) != k:
            return False
        sig_int = int.from_bytes(sig_bytes, "big")
        if sig_int >= n:
            return False
        em = pow(sig_int, e, n).to_bytes(k, "big")
        tail = _SHA256_DER_PREFIX + hashlib.sha256(manifest_bytes).digest()
        if len(tail) + 11 > k:  # need at least 8 bytes of FF padding
            return False
        expected = (b"\x00\x01" + b"\xff" * (k - len(tail) - 3)
                    + b"\x00" + tail)
        return hmac.compare_digest(em, expected)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# fetching + checking
# ---------------------------------------------------------------------------

def resolve_url_base(url_base: str | None = None) -> str:
    """The release directory URL: argument > env > built-in default."""
    base = url_base or os.environ.get(ENV_URL_BASE) or DEFAULT_URL_BASE
    return base.rstrip("/") + "/"


def _fetch(url: str, timeout: float = FETCH_TIMEOUT_S) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": f"BeeSky/{CURRENT_VERSION}",
                      "Accept": "*/*"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        return response.read()


def version_tuple(version: str) -> tuple[int, ...]:
    """'0.10.0' -> (0, 10, 0); junk parts degrade to 0, never raise."""
    parts = []
    for chunk in str(version).strip().lstrip("v").split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


def _is_newer(candidate: str, current: str) -> bool:
    a, b = version_tuple(candidate), version_tuple(current)
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) > b + (0,) * (width - len(b))


def check(url_base: str | None = None) -> dict:
    """Fetch + verify the release manifest; compare with our version.

    Returns a dict: {enabled, ok, error, current, latest,
    update_available, signature_ok, manifest, url_base}. ``ok`` is
    only True once the signature has verified — an unsigned or
    tampered manifest yields ok=False with the refusal in ``error``.
    """
    result: dict = {"enabled": updates_enabled(), "ok": False,
                    "error": None, "current": CURRENT_VERSION,
                    "latest": None, "update_available": False,
                    "signature_ok": False, "manifest": None,
                    "url_base": resolve_url_base(url_base)}
    if not result["enabled"]:
        result["error"] = ("self-update not configured: no update "
                           "signing key is compiled into this build "
                           "(owner setup: docs/updating.md)")
        return result
    base = result["url_base"]
    if base.endswith(MANIFEST_NAME):  # a direct manifest URL was given
        manifest_url = base
        base = base[: -len(MANIFEST_NAME)]
        result["url_base"] = base
    else:
        manifest_url = base + MANIFEST_NAME
    try:
        manifest_bytes = _fetch(manifest_url)
        sig_bytes = _fetch(base + SIG_NAME)
    except (urllib.error.URLError, OSError) as exc:
        result["error"] = f"cannot fetch update manifest: {exc}"
        return result
    if not verify_signature(manifest_bytes, sig_bytes):
        result["error"] = ("update manifest signature verification "
                           "FAILED — refusing to trust it")
        return result
    result["signature_ok"] = True
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        latest = str(manifest["version"])
        files = manifest["files"]
        if not isinstance(files, list) or not files:
            raise ValueError("manifest has no files")
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        result["error"] = f"signed manifest is malformed: {exc}"
        return result
    result["ok"] = True
    result["manifest"] = manifest
    result["latest"] = latest
    result["update_available"] = _is_newer(latest, CURRENT_VERSION)
    return result


def _find_entry(manifest: dict, name: str) -> dict | None:
    for entry in manifest.get("files") or []:
        if isinstance(entry, dict) and entry.get("name") == name:
            return entry
    return None


# ---------------------------------------------------------------------------
# applying an update
# ---------------------------------------------------------------------------

def _stream_download(url: str, dest: Path) -> tuple[int, str]:
    """Download *url* to *dest*, returning (size, sha256 hex)."""
    digest = hashlib.sha256()
    size = 0
    request = urllib.request.Request(
        url, headers={"User-Agent": f"BeeSky/{CURRENT_VERSION}"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=FETCH_TIMEOUT_S) as response, \
            open(dest, "wb") as out:
        while True:
            chunk = response.read(1 << 16)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
            out.write(chunk)
    return size, digest.hexdigest()


def _write_swap_bat(directory: Path, target: Path, staged: Path,
                    pid: int, relaunch_argv: list[str] | None) -> Path:
    """The Windows finisher: wait for *pid*, then swap staged->target.

    The running exe stays locked until it exits, so beesky-swap.bat
    waits for the PID to disappear, backs the old file up to
    ``<name>.old``, moves the verified new file over (restoring the
    backup if the move fails), and — only when *relaunch_argv* is
    given — restarts exactly that command line.
    """
    backup = target.with_name(target.name + ".old")
    lines = [
        "@echo off",
        "rem BeeSky self-update finisher — waits for the old process",
        "rem to exit, then swaps in the verified new executable.",
        f'powershell -NoProfile -Command "Wait-Process -Id {pid} '
        '-ErrorAction SilentlyContinue"',
        f'copy /y "{target}" "{backup}" >nul',
        f'move /y "{staged}" "{target}"',
        "if errorlevel 1 (",
        f'  copy /y "{backup}" "{target}" >nul',
        "  exit /b 1",
        ")",
    ]
    if relaunch_argv:
        lines.append(f'start "" {subprocess.list2cmdline(relaunch_argv)}')
    lines.append("(goto) 2>nul & del \"%~f0\"")  # delete self when done
    bat = directory / "beesky-swap.bat"
    bat.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return bat


def _spawn_swap_bat(bat: Path) -> None:
    flags = 0
    if os.name == "nt":  # detach so the bat outlives this process
        flags = (subprocess.DETACHED_PROCESS
                 | subprocess.CREATE_NEW_PROCESS_GROUP)
    subprocess.Popen(["cmd", "/c", str(bat)], creationflags=flags,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True)


def apply(url_base: str | None = None, *, target_path=None,
          relaunch: bool = False,
          argv: list[str] | None = None) -> dict:
    """Check, download, verify and swap in the matching release file.

    ``target_path`` replaces a specific local file (its basename
    selects the manifest entry) — used by ``update --force-file``
    and tests. Without it, the running *frozen* executable is the
    target; running from Python source is refused (updating the
    interpreter's script tree is not a thing).

    Returns {ok, message, up_to_date, restart_scheduled, target}.
    Nothing is ever deleted before its replacement is verified.
    """
    verdict: dict = {"ok": False, "message": "", "up_to_date": False,
                     "restart_scheduled": False, "target": None}
    res = check(url_base)
    if not res["ok"]:
        verdict["message"] = f"update refused: {res['error']}"
        return verdict
    if not res["update_available"]:
        verdict["ok"] = True
        verdict["up_to_date"] = True
        verdict["message"] = (f"BeeSky {CURRENT_VERSION} is already "
                              f"the latest version ({res['latest']})")
        return verdict
    manifest = res["manifest"]

    if target_path is not None:
        target = Path(target_path)
    elif getattr(sys, "frozen", False):
        target = Path(sys.executable)
    else:
        verdict["message"] = ("update refused: running from Python "
                              "source, not a frozen BeeSky executable "
                              "— pass --force-file <path> to update a "
                              "specific file")
        return verdict
    verdict["target"] = str(target)
    entry = _find_entry(manifest, target.name)
    if entry is None:
        verdict["message"] = (f"update refused: release "
                              f"{res['latest']} has no file named "
                              f"{target.name!r}")
        return verdict
    if not entry.get("url"):
        verdict["message"] = "update refused: manifest entry has no url"
        return verdict

    staged = target.with_name(f"{target.name}.new-{os.getpid()}.tmp")
    try:
        size, sha256 = _stream_download(str(entry["url"]), staged)
    except (urllib.error.URLError, OSError) as exc:
        verdict["message"] = f"update refused: download failed: {exc}"
        staged.unlink(missing_ok=True)
        return verdict
    expected_sha = str(entry.get("sha256") or "").lower()
    expected_size = entry.get("size")
    if expected_size is not None and size != int(expected_size):
        verdict["message"] = (f"update refused: downloaded size {size} "
                              f"!= manifest size {expected_size}")
        staged.unlink(missing_ok=True)
        return verdict
    if sha256 != expected_sha:
        verdict["message"] = ("update refused: downloaded file SHA-256 "
                              "does not match the signed manifest")
        staged.unlink(missing_ok=True)
        return verdict

    # The staged file is verified against the signed manifest. Swap.
    backup = target.with_name(target.name + ".old")
    if os.name == "nt":
        relaunch_argv = None
        if relaunch:
            relaunch_argv = list(argv) if argv else [str(target)]
            relaunch_argv[0] = str(target)
        bat = _write_swap_bat(target.parent, target, staged,
                              os.getpid(), relaunch_argv)
        try:
            _spawn_swap_bat(bat)
        except OSError as exc:
            verdict["message"] = (f"update refused: cannot start the "
                                  f"swap helper: {exc}")
            staged.unlink(missing_ok=True)
            return verdict
        verdict["ok"] = True
        verdict["restart_scheduled"] = True
        verdict["message"] = (
            f"BeeSky {res['latest']} downloaded + verified; the swap "
            "helper finishes the update as soon as this process "
            "exits — restart to run the new version"
            + (" (it relaunches itself)" if relaunch else ""))
        return verdict

    # POSIX: atomic replace over the running binary is safe. Keep the
    # previous file as <name>.old (rollback aid) until the replace
    # has succeeded; restore it if the replace somehow fails.
    try:
        if target.exists():
            shutil.copy2(target, backup)
            mode = target.stat().st_mode
        else:
            mode = None
        os.replace(staged, target)
        if mode is not None:
            os.chmod(target, mode)
    except OSError as exc:
        if backup.exists():
            try:
                os.replace(backup, target)
            except OSError:
                pass
        verdict["message"] = f"update refused: swap failed: {exc}"
        staged.unlink(missing_ok=True)
        return verdict
    verdict["ok"] = True
    verdict["message"] = (f"updated {target.name} to BeeSky "
                          f"{res['latest']} (previous file kept as "
                          f"{backup.name}) — restart to run it")
    if relaunch:
        # Agent --auto-update path: restart the exact same argv once
        # this process lets go (the caller exits right after apply).
        relaunch_argv = list(argv) if argv else [str(target)]
        try:
            subprocess.Popen(
                ["/bin/sh", "-c",
                 "sleep 1; exec " + shlex.join(relaunch_argv)],
                start_new_session=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            verdict["restart_scheduled"] = True
            verdict["message"] += "; relaunch scheduled"
        except OSError as exc:
            verdict["message"] += f"; relaunch failed to schedule: {exc}"
    return verdict
