# BeeSky signed self-update channel

> Tóm tắt: chủ repo chạy `tools/make_update_key.py` MỘT lần, bỏ
> private key vào GitHub secret `UPDATE_SIGNING_KEY`, commit file
> public key. Từ đó mỗi bản release tự ký `update-manifest.json`;
> máy khách (`beesky update`, agent) kiểm tra chữ ký + SHA-256 rồi
> mới tự cập nhật. Chưa cấu hình thì kênh này tắt, mọi thứ chạy như
> cũ.

Since v0.10 BeeSky can update itself through a *signed* channel:
releases carry a manifest describing their files, the manifest is
signed with an owner-held RSA key, and clients refuse anything that
does not verify. This is the Pulse pattern (their agent updates use
manifest + detached signature too), with RSA-2048 / PKCS#1 v1.5 /
SHA-256.

## How it works

Every GitHub Release built from a `v*` tag can carry two extra
assets:

| asset | content |
|---|---|
| `update-manifest.json` | `{version, published_at, files: [{name, url, sha256, size}]}` for `beesky.exe`, `beesky-gui.exe`, `BeeSkySetup-<version>.exe` |
| `update-manifest.sig` | detached RSA signature over the manifest bytes |

The release workflow (`.github/workflows/build-windows.yml`) builds
the manifest over the **final** files — after any eSigner
Authenticode signing, so the pinned hashes match what ships — and
signs it with `openssl dgst -sha256 -sign`, then self-checks the
signature with the matching public key before uploading.

Clients (`beesky/core/updater.py`):

1. fetch manifest + signature (default:
   `https://github.com/dinhvansh/beeskybase/releases/latest/download/`,
   overridable with `--url-base` / env `BEESKY_UPDATE_URL`),
2. verify the RSA signature against the public key compiled into
   the build (`beesky/core/update_key.py`) — pure-Python RSA verify,
   byte-exact PKCS#1 v1.5 block check; **any mismatch = refuse**,
3. compare `manifest.version` with the running version,
4. on apply: download the file whose name matches the running
   executable, verify its **size and SHA-256** against the signed
   manifest, and only then swap it in, keeping the previous file as
   `<name>.old`. On Windows the swap is finished by a
   `beesky-swap.bat` helper that waits for the old process to exit,
   moves the verified file over (restoring the backup on failure),
   and optionally relaunches the same command line. On POSIX the
   replace is atomic in place.

## Owner one-time setup

```bash
python3 tools/make_update_key.py
```

That generates an RSA-2048 keypair with openssl, writes the
**private** key to `update-signing-key.pem` and the **public** half
into `beesky/core/update_key.py`. Then:

1. Repo → Settings → Secrets and variables → Actions → New
   repository secret: name `UPDATE_SIGNING_KEY`, value = the entire
   contents of `update-signing-key.pem`.
2. Move the private key file into a password manager / offline
   backup and **delete it from the working tree — never commit it**.
3. Commit the public half: `git add beesky/core/update_key.py`.
4. Push a `v*` tag. From now on releases self-sign their manifest
   (2 extra assets on the Release page). Without the secret, nothing
   changes: no manifest is produced and clients report the channel
   as "not configured".

If the key is ever lost or leaked: generate a new pair, replace the
secret and the committed public key, ship a release. Clients on the
old key will refuse new manifests (they fail verification) — they
keep running their current version and can be updated once by hand
with the installer.

## Client usage

```bash
beesky update --check     # current vs latest + signature status
beesky update             # check, download, verify, swap this exe
beesky update --url-base http://127.0.0.1:8000/   # mirror / testing
beesky update --force-file ./beesky.exe           # update a file copy
```

`beesky update` updates the *frozen executable it runs as*; running
from Python source is refused (there is no single file to swap).
`--force-file PATH` updates a specific file instead, using the
manifest entry that matches its name.

### Agent behaviour

Farm agents check the channel daily (first check 60 s after start,
then every 24 h):

* a newer signed release → an `UPDATE_AVAILABLE` event (severity
  `info`) in the cloud event feed, once per version;
* applying is **opt-in**: only an agent started with `--auto-update`
  installs it. It swaps in the verified binary and exits so the
  swap helper can relaunch the exact same agent command line.
  Default is OFF — a farm agent never restarts itself uninvited.

## Security model

* The manifest is the root of trust: signed with a key that exists
  only as a CI secret; the public half is compiled into the client.
* File hashes are pinned *inside* the signed manifest, so a
  compromised download mirror cannot substitute binaries.
* Clients verify **before** parsing versions and **before**
  executing anything; tampered manifests and wrong-hash downloads
  are refused with the staged file deleted.
* Updates only ever replace the file that is already running (or an
  explicit `--force-file` target) — no arbitrary paths from the
  manifest are honoured.

## Not the same as Authenticode

This channel is BeeSky's own — it proves "this file is the one the
owner's release pipeline published". It does **not** affect Windows
SmartScreen warnings; that reputation comes from Authenticode
signing, which is the separate SSL.com eSigner feature
(docs/signing.md). The two compose: eSigner signs the binaries for
Windows' benefit, the update manifest signs the release for
BeeSky's own updater.
