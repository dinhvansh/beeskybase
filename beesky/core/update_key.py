"""BeeSky update-channel public key (compile-time constant).

The values here are the PUBLIC half of the RSA-2048 keypair whose
private half signs ``update-manifest.json`` on every GitHub Release
(see docs/updating.md). Clients verify release manifests against this
modulus before trusting a single byte of them.

``UPDATE_RSA_N_HEX is None`` is the "not configured" state: the owner
has not generated a keypair yet, and the self-update channel is
disabled (``beesky update`` says so instead of guessing). To enable
it, the owner runs ``tools/make_update_key.py`` ONCE, which rewrites
this file with the real modulus, stores the private key as the
GitHub Actions secret ``UPDATE_SIGNING_KEY`` (never in this repo),
and commits this file.
"""

# RSA modulus (hex, no 0x prefix) of the update-signing public key,
# or None while the channel is not configured.
UPDATE_RSA_N_HEX: str | None = None

# RSA public exponent. Fixed by tools/make_update_key.py.
UPDATE_RSA_E = 65537
