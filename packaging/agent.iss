; Standalone Agent: persistent background runtime and native configuration UI.
#define MyAppName "BeeSky Agent"
#define MyAppVersion "0.42.0"
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
AppMutex=Local\BeeSky.Agent.UI
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
  GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\beesky-agent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\beesky-agentw.exe"; DestDir: "{app}"; Flags: ignoreversion
; The Flutter config app (v0.31): its own data\ folder beside the
; engine exes — the layout its bridge resolves first.
Source: "..\dist\flutter-agent\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\beesky-logo.ico"; DestDir: "{app}"; DestName: "beesky.ico"; Flags: ignoreversion
Source: "..\docs\agent-app.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; No arguments = the config window. The agent loop itself is started
; by the Scheduled Task the window can create, not by a shortcut.
Name: "{autoprograms}\BeeSky Agent"; Filename: "{app}\beesky_agent_app.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky_agent_app.exe"; \
  Comment: "BeeSky Agent - Cấu hình agent tại xưởng"
Name: "{autodesktop}\BeeSky Agent"; Filename: "{app}\beesky_agent_app.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky_agent_app.exe"; \
  Comment: "BeeSky Agent - Cấu hình agent tại xưởng"; \
  Tasks: desktopicon
Name: "{autoprograms}\BeeSky Agent (Compatibility)"; Filename: "{app}\beesky-agent.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky-agent.exe"; \
  Comment: "BeeSky Agent (Compatibility) - Cấu hình agent tại xưởng"

[UninstallRun]
Filename: "{app}\beesky-agent.exe"; Parameters: "stop --config ""{userappdata}\BeeSky\agent-config.json"""; Flags: runhidden; RunOnceId: "StopBeeSkyAgent042"
Filename: "{app}\beesky-agent.exe"; Parameters: "remove-task --if-exe-dir ""{app}"""; Flags: runhidden; RunOnceId: "RemoveBeeSkyAgentStartup042"
