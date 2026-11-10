; BeeSky Agent Windows installer (Inno Setup 6)
;
; The standalone farm agent (v0.14): TWO executables with the same
; payload, installed per-user like the main BeeSky installer (no
; admin rights needed):
;
;   beesky-agent.exe  double-click opens the config window
;                     (cloud URL + agent key + site + scan target);
;                     `beesky-agent run` runs the agent loop with a
;                     visible console (handy for debugging).
;   beesky-agentw.exe the windowless twin (v0.16) — this is what
;                     the "BeeSky Agent" Scheduled Task (created
;                     from the config window) launches at startup:
;                     no console window ever, output to agent.log
;                     next to the config file.
;
; Lands in %LocalAppData%\Programs\BeeSky Agent — a separate product
; from the main BeeSky install on purpose: a farm PC that only runs
; the agent doesn't need the scanner/toolbox, and the two installers
; upgrade independently (each exe also self-updates from the signed
; update manifest, docs/updating.md).
;
; Build (on Windows, after PyInstaller has produced
; dist\beesky-agent.exe — the same spec run as the main installer):
;
;     iscc packaging\agent.iss
;
; Output: dist\BeeSkyAgentSetup-0.14.0.exe (built by
; .github/workflows/build-windows.yml — never by hand)

#define MyAppName "BeeSky Agent"
#define MyAppVersion "0.16.0"
#define MyAppPublisher "BeeSkyBase"
#define MyAppExeName "beesky-agent.exe"

[Setup]
AppId={{A1B557EB-72A4-470B-8E80-698051EDDD84}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\BeeSky Agent
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=BeeSkyAgentSetup-{#MyAppVersion}
SetupIconFile=assets\beesky-logo.ico
UninstallDisplayIcon={app}\beesky.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
  GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\beesky-agent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\beesky-agentw.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\beesky-logo.ico"; DestDir: "{app}"; DestName: "beesky.ico"; Flags: ignoreversion
Source: "..\docs\agent-app.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; No arguments = the config window. The agent loop itself is started
; by the Scheduled Task the window can create, not by a shortcut.
Name: "{autoprograms}\BeeSky Agent"; Filename: "{app}\beesky-agent.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky-agent.exe"; \
  Comment: "BeeSky Agent - Cấu hình agent tại trại"
Name: "{autodesktop}\BeeSky Agent"; Filename: "{app}\beesky-agent.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky-agent.exe"; \
  Comment: "BeeSky Agent - Cấu hình agent tại trại"; \
  Tasks: desktopicon
