# Code signing (SSL.com eSigner) — owner checklist

> **Tóm tắt:** Mua chứng thư ký số của SSL.com (nên chọn EV) + gói
> eSigner, lấy 4 thông tin đăng nhập (username / password / TOTP
> secret / credential ID), nhập vào GitHub repo ở mục Settings →
> Secrets and variables → Actions với đúng 4 tên ở bước 3. Xong xuôi
> cứ đẩy tag `v*` như bình thường — bản release sẽ **tự ký số** cả
> `beesky.exe` lẫn file cài `BeeSkySetup-*.exe` (2 lượt ký / 1 bản,
> gói eSigner rẻ nhất là đủ). Chưa có secrets thì mọi thứ vẫn build
> không ký như hiện tại, không lỗi gì.

## Why

Windows shows a SmartScreen warning ("Windows protected your PC")
for unsigned executables, and the warning comes back for every new
file even if an older build was already trusted. A code-signing
signature gives the installer a verified publisher name and a
timestamp, so trust can accumulate instead of resetting per build.

Signing is wired into `.github/workflows/build-windows.yml`. It is
**optional and automatic**: the workflow probes for the secrets and
signs only when they exist — and only on tag builds, because eSigner
pricing tiers meter the *number of signings* (cheapest tier is
roughly 20 signings/month; one release = 3 signings).

## Checklist

### 1. Buy the certificate + eSigner (SSL.com)

- Order a **code-signing certificate** — EV is recommended for a
  product you hand to customers.
- Complete SSL.com's identity/business validation (this is the slow
  part; it can take a few days and may ask for business documents).
- Subscribe to **eSigner** (cloud signing) for that certificate.
  No USB token is needed — signing happens from GitHub Actions.
- Pick the cheapest eSigner tier: a release uses exactly **3
  signings** (the CLI exe + the GUI exe + the installer), so ~20/month is plenty.

### 2. Collect the four eSigner values

From your SSL.com / eSigner account you need:

| Value | Where |
|---|---|
| **Username** | your SSL.com account username |
| **Password** | your SSL.com account password |
| **TOTP secret** | the secret shown when you enable the eSigner TOTP (scan-the-QR step — copy the text secret, not just the QR) |
| **Credential ID** | eSigner dashboard → your signing credential's ID (one certificate = one credential) |

Keep these out of chat, email, and the repo — they go only into
GitHub secrets (next step).

### 3. Add the four GitHub repo secrets

On GitHub: **beeskybase → Settings → Secrets and variables →
Actions → New repository secret**, four times, with these **exact**
names (the workflow looks for precisely these):

```
ESIGNER_USERNAME
ESIGNER_PASSWORD
ESIGNER_TOTP_SECRET
ESIGNER_CREDENTIAL_ID
```

### 4. Release as usual

```bash
git tag v0.5.1
git push origin v0.5.1
```

The tag build now, in order: builds `beesky.exe` → **signs it** →
Inno Setup embeds the signed exe → **signs `BeeSkySetup-*.exe`** →
prints `Get-AuthenticodeSignature` results in the log → attaches
both signed files to the GitHub Release.

Notes:

- Manual runs (Actions tab → "Build Windows installer") stay
  **unsigned on purpose**, even after the secrets exist — they
  would only burn signing quota.
- If a signing step fails on a tag build (wrong password, stale
  TOTP secret…), the build fails and no unsigned release slips
  out. Fix the secret and re-push the tag.
- Until the secrets exist, nothing changes: builds and releases
  work exactly as before, just unsigned.

### 5. About SmartScreen — honest expectations

Historically an EV certificate cleared SmartScreen warnings
immediately. Microsoft changed that policy in 2024: a brand-new
certificate (EV included) may still show warnings until the files
build download reputation over time. Signing is still worth it —
the warning shows your verified publisher name instead of
"unknown publisher", signatures stay valid after the certificate
expires thanks to timestamping, and reputation is no longer reset
by a certificate change. But don't expect the warning to vanish
on day one.

## Verify a downloaded file yourself

- **Explorer:** right-click the file → **Properties** →
  **Digital Signatures** tab → select the signature → **Details**
  ("This digital signature is OK").
- **PowerShell:**
  ```powershell
  Get-AuthenticodeSignature .\BeeSkySetup-0.5.0.exe
  ```
  `Status` should read `Valid`, and `SignerCertificate` should
  show the BeeSkyBase certificate.
