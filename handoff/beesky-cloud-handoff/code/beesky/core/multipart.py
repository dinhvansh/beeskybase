"""Hand-rolled multipart/form-data body builder.

The stdlib has no multipart *client* helper (``email`` builds messages,
not form posts), so the firmware-upload paths (dashd ``/firmware/update``,
stock ``/cgi-bin/upgrade.cgi``) share this tiny builder.

A field is a ``(name, filename, data, content_type)`` tuple: ``filename``
and ``content_type`` are ``None`` for plain form fields (``data`` is then
the field value as bytes).
"""

from __future__ import annotations

import secrets


def build_multipart_body(fields: list[tuple],
                         boundary: str | None = None) -> tuple[bytes, str]:
    """Serialise *fields* into a multipart body; return (body, content_type).

    An explicit *boundary* is honoured verbatim — the recovered HashCore
    unlock recipe uses one dedicated boundary string for its .bmu uploads
    (see core/firmware.py); otherwise a random boundary is generated.
    """
    boundary = boundary or f"----BeeSkyFormBoundary{secrets.token_hex(12)}"
    out = bytearray()
    for name, filename, data, content_type in fields:
        out += f"--{boundary}\r\n".encode("ascii")
        disposition = f'Content-Disposition: form-data; name="{name}"'
        if filename is not None:
            disposition += f'; filename="{filename}"'
        out += (disposition + "\r\n").encode("utf-8")
        if content_type:
            out += f"Content-Type: {content_type}\r\n".encode("ascii")
        out += b"\r\n"
        out += data
        out += b"\r\n"
    out += f"--{boundary}--\r\n".encode("ascii")
    return bytes(out), f"multipart/form-data; boundary={boundary}"
