"""Pure-Python MD5-crypt (``$1$``) — no stdlib shortcut exists.

Why this file exists: MicroBT's Whatsminer API manuals document
their token flow with ``openssl passwd -1`` as the reference
implementation (docs/vendor-docs-mapping.md §1.3) — that is
MD5-crypt, Poul-Henning Kamp's algorithm, NOT plain MD5. The
manuals' prose says ``md5(salt + password)`` but the reference
code governs: ``key = md5crypt(password, salt)`` and
``sign = md5crypt(key + last4(time), newsalt)``, taking the
checksum field of each ``$1$salt$checksum`` string.

CPython's ``crypt`` module (which offers METHOD_MD5) does not
exist on Windows — BeeSky's main target — and is deprecated
since 3.11, so the algorithm is implemented here from the
public spec on stdlib ``hashlib.md5`` only.

Verified against the manuals' own worked example (OpenSSL
3.0.13, ``openssl passwd -1``): see tests/mock_vendors2_test.py
— ``md5crypt("admin", "BQ5hoXV9")`` must give the checksum
``RxmaDUO33TS7O26yeMHZ81`` and
``md5crypt("RxmaDUO33TS7O26yeMHZ81" + "5626", "jbzkfQls")``
must give ``w.BNbkCV6n1aNWgiBWLzT/``.
"""

from __future__ import annotations

import hashlib

_CRYPT_ALPHABET = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
# The digest bytes are encoded in this order (the classic
# crypt $1$ permutation): five 3-byte groups, then the last byte.
_ENCODE_ORDER = ((0, 6, 12), (1, 7, 13), (2, 8, 14), (3, 9, 15),
                 (4, 10, 5), (11,))


def _to64(value: int, length: int) -> str:
    """Encode *length* base-64 digits of *value*, low bits first."""
    out = []
    for _ in range(length):
        out.append(_CRYPT_ALPHABET[value & 0x3F])
        value >>= 6
    return "".join(out)


def _encode_digest(digest: bytes) -> str:
    """The 22-character checksum of a 16-byte MD5-crypt digest.

    Byte order is the classic one: the FIRST byte of each group
    is the MOST significant (``(d[0]<<16)|(d[6]<<8)|d[12]``) —
    the low 6 bits emitted first therefore belong to the LAST
    byte of the group. Reversing this silently produces a valid
    looking but wrong checksum (caught by the openssl vectors).
    """
    out = []
    for group in _ENCODE_ORDER:
        value = 0
        for index in group:
            value = (value << 8) | digest[index]
        out.append(_to64(value, len(group) + 1))
    return "".join(out)


def _clean_salt(salt: str) -> str:
    """A raw salt string, normalised: strip a ``$1$`` prefix and
    anything after a following ``$``; MD5-crypt uses at most 8 chars."""
    if salt.startswith("$1$"):
        salt = salt[3:]
    if "$" in salt:
        salt = salt.split("$", 1)[0]
    return salt[:8]


def md5crypt(password: str, salt: str) -> str:
    """Full ``$1$<salt>$<checksum>`` string for *password*/*salt*.

    Both arguments are ASCII in every real use (miner passwords
    and the miner's own random salts); UTF-8 encoding keeps the
    function total for anything else.
    """
    pw = password.encode("utf-8")
    salt = _clean_salt(salt)
    salt_b = salt.encode("utf-8")

    # Initial mix: password + "$1$" + salt, then the digest of
    # (password + salt + password) folded in by password length.
    ctx = pw + b"$1$" + salt_b
    alt = hashlib.md5(pw + salt_b + pw).digest()
    for i in range(len(pw)):
        ctx += alt[i % 16:i % 16 + 1]
    # Bit-mixing: for each bit of the password length, append NUL
    # (bit set) or the password's first byte (bit clear).
    length = len(pw)
    while length:
        ctx += b"\x00" if length & 1 else pw[:1]
        length >>= 1
    final = hashlib.md5(ctx).digest()

    # 1000 rounds of the documented mixing schedule.
    for i in range(1000):
        block = bytearray()
        block += pw if i & 1 else final
        if i % 3:
            block += salt_b
        if i % 7:
            block += pw
        block += final if i & 1 else pw
        final = hashlib.md5(bytes(block)).digest()

    return f"$1${salt}${_encode_digest(final)}"


def md5crypt_checksum(password: str, salt: str) -> str:
    """Just the 22-character checksum field of ``md5crypt(...)``.

    This is the value MicroBT's token flow uses as ``key`` and
    ``sign`` (the manuals' reference code pipes the full
    ``openssl passwd -1`` output through ``cut -f 4 -d '$'``).
    """
    return md5crypt(password, salt).split("$")[3]
