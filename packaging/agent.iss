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
; Since v0.31 the Flutter bundle (beesky_agent_app.exe +
; flutter_windows.dll + data\, staged as dist\flutter-agent\) ships
; in the same folder: the "BeeSky Agent (Flutter)" shortcut is the
; new face of the config window, while the "BeeSky Agent" shortcut
; above keeps launching beesky-agent.exe exactly as before (the Tk
; window remains the fallback). An optional pairing page offers to
; write the agent config during install — see the [Code] section
; and docs/agent-app-mapping.md.
;
; Lands in %LocalAppData%\Programs\BeeSky Agent — a separate product
; from the main BeeSky install on purpose: a farm PC that only runs
; the agent doesn't need the scanner/toolbox, and the two installers
; upgrade independently (each exe also self-updates from the signed
; update manifest, docs/updating.md).
;
; Build (on Windows, after PyInstaller + the agent Flutter build
; have staged dist\beesky-agent.exe and dist\flutter-agent\):
;
;     iscc packaging\agent.iss
;
; Output: dist\BeeSkyAgentSetup-<version>.exe (built by
; .github/workflows/build-windows.yml — never by hand)

#define MyAppName "BeeSky Agent"
#define MyAppVersion "0.38.0"
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
Name: "{autoprograms}\BeeSky Agent"; Filename: "{app}\beesky-agent.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky-agent.exe"; \
  Comment: "BeeSky Agent - Cấu hình agent tại trại"
Name: "{autodesktop}\BeeSky Agent"; Filename: "{app}\beesky-agent.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky-agent.exe"; \
  Comment: "BeeSky Agent - Cấu hình agent tại trại"; \
  Tasks: desktopicon
Name: "{autoprograms}\BeeSky Agent (Flutter)"; Filename: "{app}\beesky_agent_app.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky_agent_app.exe"; \
  Comment: "BeeSky Agent (Flutter) - Cấu hình agent tại trại"

[Code]
{ --- Optional agent pairing page (v0.31) --------------------------
  The Pulse pattern (docs/agent-app-mapping.md §2): offer the
  agent's pairing values DURING install. Same implementation as
  the unified installer's page, minus the component check (this
  installer is agent-only). Optional — all three fields or none;
  writes the core's config file (legacy plain-text JSON form,
  ASCII-only via JsonEscape) ONLY when no config exists yet. }

var
  PairPage: TWizardPage;
  PairCloudEdit: TNewEdit;
  PairKeyEdit: TPasswordEdit;
  PairSiteEdit: TNewEdit;

function AgentConfigPath: String;
begin
  Result := ExpandConstant('{userappdata}\BeeSky\agent-config.json');
end;

function JsonEscape(const S: String): String;
var
  I, C: Integer;
begin
  Result := '';
  for I := 1 to Length(S) do
  begin
    C := Ord(S[I]);
    if C = 34 then
      Result := Result + '\"'
    else if C = 92 then
      Result := Result + '\\'
    else if C = 8 then
      Result := Result + '\b'
    else if C = 9 then
      Result := Result + '\t'
    else if C = 10 then
      Result := Result + '\n'
    else if C = 12 then
      Result := Result + '\f'
    else if C = 13 then
      Result := Result + '\r'
    else if (C < 32) or (C >= 128) then
      Result := Result + Format('\u%.4x', [C])
    else
      Result := Result + S[I];
  end;
end;

function PairShouldSkip(Page: TWizardPage): Boolean;
begin
  Result := FileExists(AgentConfigPath);
end;

function PairNextButton(Page: TWizardPage): Boolean;
var
  Filled: Integer;
begin
  Filled := 0;
  if Trim(PairCloudEdit.Text) <> '' then Filled := Filled + 1;
  if Trim(PairKeyEdit.Text) <> '' then Filled := Filled + 1;
  if Trim(PairSiteEdit.Text) <> '' then Filled := Filled + 1;
  Result := (Filled = 0) or (Filled = 3);
  if not Result then
    MsgBox('Kết nối agent: cần nhập đủ Cloud URL, Agent key và Tên trại '
      + '— hoặc để trống cả ba mục để cấu hình sau trong app BeeSky Agent.',
      mbError, MB_OK);
end;

procedure InitializeWizard;
var
  Lbl: TNewStaticText;
  TopPos: Integer;
begin
  PairPage := CreateCustomPage(wpSelectDir,
    'Kết nối BeeSky Agent (không bắt buộc)',
    'Điền sẵn Cloud URL + Agent key + Tên trại thì agent chạy ngay '
    + 'sau khi cài. Để trống cả ba mục nếu muốn cấu hình sau trong '
    + 'app BeeSky Agent.');
  TopPos := 0;
  Lbl := TNewStaticText.Create(PairPage);
  Lbl.Parent := PairPage.Surface;
  Lbl.Left := 0;
  Lbl.Top := TopPos;
  Lbl.Caption := 'Cloud URL:';
  PairCloudEdit := TNewEdit.Create(PairPage);
  PairCloudEdit.Parent := PairPage.Surface;
  PairCloudEdit.Left := 0;
  PairCloudEdit.Top := TopPos + ScaleY(18);
  PairCloudEdit.Width := PairPage.SurfaceWidth;
  TopPos := TopPos + ScaleY(52);
  Lbl := TNewStaticText.Create(PairPage);
  Lbl.Parent := PairPage.Surface;
  Lbl.Left := 0;
  Lbl.Top := TopPos;
  Lbl.Caption := 'Agent key (cloud cấp, chỉ hiện một lần lúc tạo agent):';
  PairKeyEdit := TPasswordEdit.Create(PairPage);
  PairKeyEdit.Parent := PairPage.Surface;
  PairKeyEdit.Left := 0;
  PairKeyEdit.Top := TopPos + ScaleY(18);
  PairKeyEdit.Width := PairPage.SurfaceWidth;
  TopPos := TopPos + ScaleY(52);
  Lbl := TNewStaticText.Create(PairPage);
  Lbl.Parent := PairPage.Surface;
  Lbl.Left := 0;
  Lbl.Top := TopPos;
  Lbl.Caption := 'Tên trại:';
  PairSiteEdit := TNewEdit.Create(PairPage);
  PairSiteEdit.Parent := PairPage.Surface;
  PairSiteEdit.Left := 0;
  PairSiteEdit.Top := TopPos + ScaleY(18);
  PairSiteEdit.Width := PairPage.SurfaceWidth;
  PairPage.OnShouldSkipPage := @PairShouldSkip;
  PairPage.OnNextButtonClick := @PairNextButton;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Content: String;
begin
  if CurStep <> ssPostInstall then
    Exit;
  if PairShouldSkip(PairPage) then
    Exit;
  if (Trim(PairCloudEdit.Text) = '') or (Trim(PairKeyEdit.Text) = '')
    or (Trim(PairSiteEdit.Text) = '') then
    Exit;
  ForceDirectories(ExpandConstant('{userappdata}\BeeSky'));
  Content :=
    '{' + #13#10
    + '  "target": "",' + #13#10
    + '  "cloud_url": "' + JsonEscape(Trim(PairCloudEdit.Text)) + '",' + #13#10
    + '  "key": "' + JsonEscape(Trim(PairKeyEdit.Text)) + '",' + #13#10
    + '  "key_protected": "",' + #13#10
    + '  "site": "' + JsonEscape(Trim(PairSiteEdit.Text)) + '",' + #13#10
    + '  "interval": 30,' + #13#10
    + '  "notify_config": null,' + #13#10
    + '  "auto_update": false' + #13#10
    + '}' + #13#10;
  SaveStringToFile(AgentConfigPath, Content, False);
end;
