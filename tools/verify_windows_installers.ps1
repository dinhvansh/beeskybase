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
    $workerProcess = $null
    if ($kind -eq 'Agent') {
        $configDir = Join-Path $env:APPDATA 'BeeSky'
        New-Item -ItemType Directory -Force -Path $configDir | Out-Null
        $configFile = Join-Path $configDir 'agent-config.json'
        $fixtureConfig = @{ target='127.0.0.1'; cloud_url='http://127.0.0.1:1'; key='ci-inert-key-does-not-authenticate'; site='Isolated uninstall smoke'; interval=1; timeout=0.1; http_port=1; cgminer_port=1 } | ConvertTo-Json
        [System.IO.File]::WriteAllText($configFile, $fixtureConfig, (New-Object System.Text.UTF8Encoding($false)))
        $engine = Join-Path $installPath 'beesky-agent.exe'
        $workerProcess = Start-Process -FilePath $engine -ArgumentList @('run', '--background', '--config', ('"{0}"' -f $configFile)) -WindowStyle Hidden -PassThru
        $runtimeFile = Join-Path $configDir 'agent-config.runtime.json'
        for ($attempt = 0; $attempt -lt 60 -and -not (Test-Path -LiteralPath $runtimeFile); $attempt++) { Start-Sleep -Milliseconds 250 }
        if (-not (Test-Path -LiteralPath $runtimeFile)) { throw 'Installed Agent did not start its runtime' }
    }
    $uninstaller = Join-Path $installPath 'unins000.exe'
    $uninstallProcess = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') -WindowStyle Hidden -PassThru -Wait
    if ($uninstallProcess.ExitCode -ne 0) { throw "$kind uninstall failed: $($uninstallProcess.ExitCode)" }
    for ($attempt = 0; $attempt -lt 30 -and (Test-Path -LiteralPath $installPath); $attempt++) { Start-Sleep -Milliseconds 250 }
    if (Test-Path -LiteralPath $installPath) { throw "$kind left files in its installation folder" }
    if ($workerProcess) {
        if (-not $workerProcess.WaitForExit(15000)) { throw 'Uninstall did not stop the installed Agent worker' }
        if (Test-Path -LiteralPath $runtimeFile) { throw 'Uninstall left a live runtime control file' }
    }
    if ($kind -eq 'Scanner') {
        $preserved = Join-Path $env:APPDATA 'BeeSky/beesky-groups.json'
        if (-not (Test-Path -LiteralPath $preserved)) { throw 'Uninstall lost user data' }
        if ((Get-Content -LiteralPath $preserved -Raw) -notmatch 'scanner-preserve-smoke') { throw 'Wrong preserved data' }
    }
    Write-Host "${kind}: install, font and clean uninstall passed"
}

