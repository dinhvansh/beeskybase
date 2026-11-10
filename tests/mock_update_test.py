#!/usr/bin/env python3
"""v0.10 hermetic test — signed self-update channel.

No network beyond 127.0.0.1, no hardware, no real release:

  * a throwaway RSA-2048 keypair is generated with openssl through
    the SHIPPED owner tool (tools/make_update_key.py, outputs
    redirected into a temp dir so the repo's update_key.py is never
    touched), and the test then points beesky.core.updater at that
    public key by overriding its module variables,
  * a local HTTP "release server" serves a hand-built
    update-manifest.json + update-manifest.sig + a fake new `beesky`
    binary whose SHA-256 the manifest pins,
  * assertions: --check semantics report the newer version with a
    verified signature; a tampered manifest is refused; a correctly
    signed manifest whose file hash is wrong is refused; applying
    onto a dummy exe copy replaces it, keeps a .old backup and the
    executable bit; a not-newer manifest is a no-op; with no key
    compiled in, the channel reports "not configured"; the CLI wires
    through (`update --check` / `update` exit codes).

Prints PASS lines; exit 1 on failure. Run via
tests/run_mock_test_v10.sh (which appends evidence to
tests/RESULTS.md).
"""

import functools
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import beesky  # noqa: E402
from beesky.core import updater  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'}: {label}"
          + (f" — {extra}" if extra else ""))
    if not condition:
        FAILURES.append(label)


def _openssl_sign(key: Path, manifest_file: Path, sig_file: Path) -> None:
    result = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", str(key),
         "-out", str(sig_file), str(manifest_file)],
        capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"openssl sign failed: {result.stderr}")


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # silence the server log
        pass


def _serve(directory: Path) -> tuple[ThreadingHTTPServer, str]:
    handler = functools.partial(_QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"


def _write_release(directory: Path, base: str, version: str,
                   exe_name: str, exe_bytes: bytes,
                   sha_override: str | None, key: Path) -> bytes:
    """Write exe + manifest + signature into *directory*; return the
    manifest bytes exactly as served."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / exe_name).write_bytes(exe_bytes)
    manifest = {
        "version": version,
        "published_at": "2026-11-10T00:00:00Z",
        "files": [{
            "name": exe_name,
            "url": base + exe_name,
            "sha256": sha_override or hashlib.sha256(exe_bytes).hexdigest(),
            "size": len(exe_bytes),
        }],
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
    manifest_file = directory / "update-manifest.json"
    manifest_file.write_bytes(manifest_bytes)
    _openssl_sign(key, manifest_file, directory / "update-manifest.sig")
    return manifest_bytes


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-update-"))
    servers: list[ThreadingHTTPServer] = []
    saved_n = updater.UPDATE_RSA_N_HEX
    try:
        # --- keypair via the shipped owner tool, into the temp dir
        spec = importlib.util.spec_from_file_location(
            "make_update_key", REPO / "tools" / "make_update_key.py")
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        key_file = tmp / "update-signing-key.pem"
        module_file = tmp / "update_key.py"
        n_hex = tool.generate(key_file, module_file)
        namespace: dict = {}
        exec(module_file.read_text(encoding="utf-8"), namespace)
        check("owner tool: module modulus matches generated key",
              namespace["UPDATE_RSA_N_HEX"] == n_hex
              and len(n_hex) == 512)
        check("owner tool: exponent fixed at 65537",
              namespace["UPDATE_RSA_E"] == 65537)
        updater.UPDATE_RSA_N_HEX = n_hex
        updater.UPDATE_RSA_E = 65537
        check("updater: channel enabled with a compiled-in key",
              updater.updates_enabled())

        # The "newer release" fixture is derived from the running
        # version (minor + 1) so this suite survives version bumps —
        # it previously hardcoded 0.11.0 and broke when BeeSky itself
        # reached 0.11.0 (v0.11 regression fix).
        _v = [int(p) for p in beesky.__version__.split(".")[:3]]
        newer = f"{_v[0]}.{_v[1] + 1}.0"
        new_bytes = f"BeeSky fake {newer} binary\n".encode() * 64
        old_bytes = (f"BeeSky fake {beesky.__version__} binary "
                     "(the dummy)\n").encode()

        # --- release A: newer version, honest hash
        dir_a = tmp / "rel-a"
        dir_a.mkdir()
        server_a, base_a = _serve(dir_a)
        servers.append(server_a)
        manifest_a = _write_release(dir_a, base_a, newer, "beesky",
                                    new_bytes, None, key_file)
        sig_a = (dir_a / "update-manifest.sig").read_bytes()

        check("verify: valid RSA signature over the manifest verifies",
              updater.verify_signature(manifest_a, sig_a))
        tampered = manifest_a[:20] + bytes([manifest_a[20] ^ 0x01]) \
            + manifest_a[21:]
        check("verify: one flipped manifest byte fails verification",
              not updater.verify_signature(tampered, sig_a))
        check("verify: truncated signature fails verification",
              not updater.verify_signature(manifest_a, sig_a[:-8]))

        res = updater.check(base_a)
        check("check: signed manifest accepted (ok + signature_ok)",
              res["ok"] and res["signature_ok"], json.dumps(
                  {k: res[k] for k in ("current", "latest",
                                       "update_available")}))
        check("check: newer version reported as update available",
              res["latest"] == newer and res["update_available"]
              and res["current"] == beesky.__version__)

        # tamper the SERVED manifest: the whole check must refuse
        (dir_a / "update-manifest.json").write_bytes(tampered)
        res = updater.check(base_a)
        check("check: tampered manifest refused end-to-end",
              not res["ok"] and not res["update_available"]
              and "signature" in (res["error"] or ""))
        (dir_a / "update-manifest.json").write_bytes(manifest_a)

        # --- apply: happy path onto a dummy exe copy (POSIX swap)
        farm = tmp / "farm"
        farm.mkdir()
        dummy = farm / "beesky"
        dummy.write_bytes(old_bytes)
        dummy.chmod(0o755)
        verdict = updater.apply(base_a, target_path=dummy)
        check("apply: newer signed release installs onto the dummy",
              verdict["ok"], verdict["message"])
        check("apply: dummy now holds the new binary bytes",
              dummy.read_bytes() == new_bytes)
        backup = farm / "beesky.old"
        check("apply: previous file kept as beesky.old backup",
              backup.exists() and backup.read_bytes() == old_bytes)
        check("apply: executable bit preserved on the new file",
              bool(dummy.stat().st_mode & 0o111))

        # --- release B: correctly signed, but the pinned hash is wrong
        dir_b = tmp / "rel-b"
        dir_b.mkdir()
        server_b, base_b = _serve(dir_b)
        servers.append(server_b)
        wrong_sha = hashlib.sha256(b"some other bytes entirely").hexdigest()
        _write_release(dir_b, base_b, newer, "beesky", new_bytes,
                       wrong_sha, key_file)
        # entry selection is by basename: the target is named "beesky"
        target_b = farm / "beesky"
        target_b.write_bytes(old_bytes)
        verdict = updater.apply(base_b, target_path=target_b)
        check("apply: wrong-hash download refused despite valid "
              "signature", not verdict["ok"]
              and "SHA-256" in verdict["message"])
        check("apply: refused download leaves the target untouched",
              target_b.read_bytes() == old_bytes)
        leftovers = [p.name for p in farm.iterdir()
                     if ".tmp" in p.name]
        check("apply: no staged temp files left behind after refusal",
              leftovers == [], f"leftovers={leftovers}")

        # --- release C: signed, but version == current -> no-op
        dir_c = tmp / "rel-c"
        dir_c.mkdir()
        server_c, base_c = _serve(dir_c)
        servers.append(server_c)
        _write_release(dir_c, base_c, beesky.__version__, "beesky",
                       new_bytes, None, key_file)
        res = updater.check(base_c)
        check("check: same-version manifest is not an update",
              res["ok"] and not res["update_available"])
        target_c = farm / "beesky"
        target_c.write_bytes(old_bytes)
        verdict = updater.apply(base_c, target_path=target_c)
        check("apply: not-newer release is a clean no-op",
              verdict["ok"] and verdict["up_to_date"]
              and target_c.read_bytes() == old_bytes)

        # --- unreachable channel: clean error, no exception
        res = updater.check("http://127.0.0.1:1/")
        check("check: unreachable update server -> ok=False + error",
              not res["ok"] and bool(res["error"]))

        # --- not configured: no key compiled in
        updater.UPDATE_RSA_N_HEX = None
        res = updater.check(base_a)
        check("disabled: no key -> channel reports not configured",
              not res["enabled"] and not res["ok"]
              and "not configured" in (res["error"] or ""))
        check("disabled: verify_signature is False without a key",
              not updater.verify_signature(manifest_a, sig_a))
        updater.UPDATE_RSA_N_HEX = n_hex

        # --- CLI wiring (repo build has NO key compiled in)
        proc = subprocess.run(
            [sys.executable, "-m", "beesky", "update", "--check",
             "--url-base", base_a],
            cwd=REPO, capture_output=True, text=True, timeout=60)
        check("cli: `update --check` reports the unconfigured channel",
              proc.returncode == 0 and "not configured" in proc.stdout,
              proc.stdout.strip().splitlines()[-1] if proc.stdout else "")
        proc = subprocess.run(
            [sys.executable, "-m", "beesky", "update"],
            cwd=REPO, capture_output=True, text=True, timeout=60)
        check("cli: bare `update` refuses cleanly (exit 2) when "
              "unconfigured", proc.returncode == 2
              and "refused" in proc.stdout)
    finally:
        updater.UPDATE_RSA_N_HEX = saved_n
        for server in servers:
            server.shutdown()
    print()
    if FAILURES:
        print(f"UPDATE TEST FAILED — {len(FAILURES)} assertion(s): "
              + "; ".join(FAILURES))
        return 1
    print("UPDATE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
