$ErrorActionPreference = 'Stop'
$smokeRoot = Join-Path $env:RUNNER_TEMP 'beesky-install-smoke'
if (-not $env:RUNNER_TEMP) { throw 'Only run in the isolated build environment' }
New-Item -ItemType Directory -Force -Path $smokeRoot | Out-Null
foreach ($kind in @('Scanner', 'Agent')) {
    $pattern = if ($kind -eq 'Scanner') { 'dist/BeeSkySetup-*.exe' } else { 'dist/BeeSkyAgentSetup-*.exe' }
    $setup = (Get-ChildItem $pattern | Select-Object -First 1).FullName
    $installPath = Join-Path $smokeRoot $kind
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', '/NOICONS', ('/DIR="{0}"' -f $installPath))
    $installerProcess = Start-Process -FilePath $setup -ArgumentList $arguments -WindowStyle Hidden -PassThru -Wait
    if ($installerProcess.ExitCode -ne 0) { throw "$kind setup failed: $($installerProcess.ExitCode)" }
    if ($kind -eq 'Scanner') {
        if (Test-Path (Join-Path $installPath 'agent')) { throw 'Scanner still embeds Agent' }
        $legacyFixture = Join-Path $installPath 'beesky-groups.json'
        '{"fixture":"scanner-preserve-smoke"}' | Set-Content -LiteralPath $legacyFixture -Encoding UTF8
        $fontPath = Join-Path $installPath 'data/flutter_assets/assets/fonts/NotoSans-400.ttf'
        if (-not (Test-Path -LiteralPath $fontPath)) { throw 'Vietnamese font is missing' }
    }
    $uninstaller = Join-Path $installPath 'unins000.exe'
    $uninstallProcess = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') -WindowStyle Hidden -PassThru -Wait
    if ($uninstallProcess.ExitCode -ne 0) { throw "$kind uninstall failed: $($uninstallProcess.ExitCode)" }
    for ($attempt = 0; $attempt -lt 30 -and (Test-Path -LiteralPath $installPath); $attempt++) { Start-Sleep -Milliseconds 250 }
    if (Test-Path -LiteralPath $installPath) { throw "$kind left files in its installation folder" }
    if ($kind -eq 'Scanner') {
        $preserved = Join-Path $env:APPDATA 'BeeSky/beesky-groups.json'
        if (-not (Test-Path -LiteralPath $preserved)) { throw 'Uninstall lost user data' }
        if ((Get-Content -LiteralPath $preserved -Raw) -notmatch 'scanner-preserve-smoke') { throw 'Wrong preserved data' }
    }
    Write-Host "${kind}: install, font and clean uninstall passed"
}

