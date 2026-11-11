"""Worker pattern expansion for pool changes (v0.28).

The HashCore Toolkit's pool-change dialog lets the worker
field carry pattern variables, expanded per device when the
change-pools task runs (dissection: docs/presets-ipreport-
mapping.md §1.4 — the token set is VERIFIED from the AOT
help text AND the change_pool_pattern enum, quoted there).
This module is the core's expander; the Flutter editor
mirrors it in Dart for the live Preview, and both are pinned
to the same case table by the test suites.

Token semantics (mapping §1.4–§1.5):

    {account}        current pool user, before the first "."
    {worker}         current pool user, after the first "."
    {ip:.}           the device IP, "." as the octet divider
                     ({ip:<div>} generalises the divider)
    {ip1}..{ip4}     one octet of the device IP
    {n[:start[:step]]}    sequential number: start +
    {nn[…]}               (index) * step, zero-padded to
    {nnn[…]}              2 / 3 digits for nn / nnn
    {pool-host}      host of the device's current pool URL
    {port}           port of the device's current pool URL
    {proto-str}      scheme of the device's current pool URL
    {mac}            the device's MAC (no BeeSky source yet)
    {host} / {h}     the device's hostname (not carried)

The index behind {n} is the device's 0-based position in
the job's target list — a named BeeSky choice (the
original's counting is UNKNOWN). Tokens whose source data
is absent raise PatternError instead of expanding to a
guess: a wrong worker written to a miner is worse than an
honest per-device failure (mapping §1.5, divergence D3).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"\{([^{}]*)\}")

#: Tokens that read the device's CURRENT pool configuration
#: (the runner must fetch a record before expanding them).
CURRENT_POOL_TOKENS = ("account", "worker", "pool-host", "port",
                       "proto-str")


class PatternError(ValueError):
    """A worker pattern cannot be expanded for this device."""


@dataclass(frozen=True)
class PatternContext:
    """Everything an expansion may read for one device."""

    ip: str
    index: int = 0                    # 0-based position in the job
    current_user: str | None = None   # current pool-1 user/worker
    current_url: str | None = None    # current pool-1 URL
    mac: str | None = None            # not emitted by any adapter
    host: str | None = None           # not carried on records


def _parse_number_params(token: str, body: str) -> tuple[int, int]:
    """{n[:start[:step]]} parameters (defaults 1, 1)."""
    parts = body.split(":")
    if len(parts) > 3:
        raise PatternError(f"pattern {{{token}}}: too many ':' parts")
    try:
        start = int(parts[1]) if len(parts) > 1 and parts[1] else 1
        step = int(parts[2]) if len(parts) > 2 and parts[2] else 1
    except ValueError:
        raise PatternError(
            f"pattern {{{token}}}: start/step must be integers") \
            from None
    return start, step


def _current_url_parts(ctx: PatternContext, token: str) -> tuple[str, str, int]:
    """(scheme, host, port) of the current pool URL."""
    url = ctx.current_url
    if not url:
        raise PatternError(
            f"pattern {{{token}}} needs the device's current pool, "
            "and none is known for this device")
    scheme, sep, rest = url.partition("://")
    if not sep:
        scheme, rest = "", url
    hostport = rest.split("/", 1)[0]
    host, colon, port_s = hostport.rpartition(":")
    if not colon or not host:
        raise PatternError(
            f"pattern {{{token}}}: current pool URL {url!r} "
            "carries no host:port")
    try:
        port = int(port_s)
    except ValueError:
        raise PatternError(
            f"pattern {{{token}}}: current pool URL {url!r} "
            "carries no numeric port") from None
    return scheme, host, port


def _expand_token(token: str, ctx: PatternContext) -> str:
    body = token.strip()
    if body.startswith("ip:"):
        return ctx.ip.replace(".", body[3:] or ".")
    if body in ("ip1", "ip2", "ip3", "ip4"):
        octets = ctx.ip.split(".")
        if len(octets) != 4:
            raise PatternError(
                f"pattern {{{token}}}: {ctx.ip!r} is not an IPv4 "
                "address")
        return octets[int(body[2]) - 1]
    head = body.split(":", 1)[0]
    if head in ("n", "nn", "nnn"):
        start, step = _parse_number_params(token, body)
        value = start + ctx.index * step
        width = {"n": 0, "nn": 2, "nnn": 3}[head]
        return str(value).zfill(width) if width else str(value)
    if body == "account" or body == "worker":
        user = ctx.current_user
        if user is None:
            raise PatternError(
                f"pattern {{{token}}} needs the device's current "
                "pool worker, and none is known for this device")
        account, _, worker = user.partition(".")
        return account if body == "account" else worker
    if body in ("pool-host", "port", "proto-str"):
        scheme, host, port = _current_url_parts(ctx, token)
        return {"pool-host": host, "port": str(port),
                "proto-str": scheme}[body]
    if body == "mac":
        if not ctx.mac:
            raise PatternError(
                "pattern {mac} needs the device's MAC address, "
                "which BeeSky's scan data does not carry")
        return ctx.mac.replace(":", "").replace("-", "")
    if body in ("host", "h"):
        if not ctx.host:
            raise PatternError(
                f"pattern {{{token}}} needs the device's hostname, "
                "which BeeSky's scan data does not carry")
        return ctx.host
    raise PatternError(f"unknown pattern {{{token}}}")


def needs_current_pool(template: str) -> bool:
    """True when expanding *template* reads the current pool."""
    for match in _TOKEN_RE.finditer(template):
        if match.group(1).strip().split(":", 1)[0] \
                in CURRENT_POOL_TOKENS:
            return True
    return False


def expand_worker(template: str, ctx: PatternContext) -> str:
    """Expand every pattern token in a worker template.

    Literal text passes through untouched; a "{" that never
    closes is literal too (it forms no token). Raises
    PatternError on unknown/malformed tokens and on tokens
    whose source data the context does not carry.
    """
    return _TOKEN_RE.sub(
        lambda m: _expand_token(m.group(1), ctx), template)
