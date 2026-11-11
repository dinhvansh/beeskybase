; BeeSky Windows installer (Inno Setup 6) — the UNIFIED installer
; (v0.31: main app + farm agent in one setup, selectable components)
;
; Per-user install: lands in %LocalAppData%\Programs\BeeSky, needs NO
; admin rights (PrivilegesRequired=lowest) — a workshop PC can install
; it as-is. Adds the install dir to the *user* PATH so `beesky` works
; from any console. Two components, both selected by default:
;
;   main   the scanner/diagnostics app: beesky.exe (console CLI,
;          always installed — both Flutter faces drive it as their
;          sidecar/engine), beesky-gui.exe (the Tk window — the
;          "BeeSky" shortcut still points HERE; Tk stays the
;          default face until the Flutter app proves itself) and
;          the Flutter bundle (beesky_app.exe + flutter_windows.dll
;          + data\) in {app} itself, where its sidecar lookup finds
;          beesky.exe beside it.
;   agent  the farm agent, in {app}\agent\: beesky-agent.exe +
;          beesky-agentw.exe (the engine + its windowless twin)
;          and the Flutter agent bundle (beesky_agent_app.exe +
;          flutter_windows.dll + data\) beside them — its bridge
;          looks in its own folder, then one level up (for
;          beesky.exe's sysinfo).
;
; The standalone BeeSkyAgentSetup (packaging\agent.iss) keeps
; shipping for agent-only farm PCs; this installer is the one-box
; option. An optional pairing page (Pulse-style, v0.31) offers to
; write the agent config during install — see the [Code] section
; and docs/agent-app-mapping.md.
;
; Build (on Windows, after PyInstaller + the two Flutter builds
; have staged dist\beesky.exe, dist\flutter-main\ and
; dist\flutter-agent\):
;
;     iscc packaging\installer.iss
;
; Output: dist\BeeSkySetup-<version>.exe  (built by
; .github/workflows/build-windows.yml — never by hand)

#define MyAppName "BeeSky"
#define MyAppVersion "0.31.1"
#define MyAppPublisher "BeeSkyBase"
#define MyAppExeName "beesky-gui.exe"

[Setup]
AppId={{B71C77C2-9B8A-40D9-BE04-67E257472AE6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\BeeSky
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=BeeSkySetup-{#MyAppVersion}
SetupIconFile=assets\beesky-logo.ico
UninstallDisplayIcon={app}\beesky.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes

[Types]
Name: "full"; Description: "Đầy đủ (app chính + agent)"
Name: "compact"; Description: "Chỉ app chính"
Name: "custom"; Description: "Tự chọn"; Flags: iscustom

[Components]
Name: "main"; Description: "BeeSky — quét & chẩn đoán máy đào (app Flutter + bản Tk + dòng lệnh)"; \
  Types: full compact; Flags: disablenouninstallwarning
Name: "agent"; Description: "BeeSky Agent — agent tại trại (app cấu hình Flutter + agent chạy ngầm)"; \
  Types: full; Flags: disablenouninstallwarning

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
  GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Always: the CLI both Flutter faces drive, the icon, the readme.
Source: "..\dist\beesky.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\beesky-logo.ico"; DestDir: "{app}"; DestName: "beesky.ico"; Flags: ignoreversion
Source: "..\docs\notify.example.json"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
; Main component: the Tk window + the Flutter bundle (its data\
; folder must sit in {app} itself — the sidecar lives beside it).
Source: "..\dist\beesky-gui.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: main
Source: "..\dist\flutter-main\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs; Components: main
; Agent component: engine + windowless twin + the Flutter agent
; bundle, together in {app}\agent (their own data\ folder — no
; clash with the main bundle's).
Source: "..\dist\beesky-agent.exe"; DestDir: "{app}\agent"; Flags: ignoreversion; Components: agent
Source: "..\dist\beesky-agentw.exe"; DestDir: "{app}\agent"; Flags: ignoreversion; Components: agent
Source: "..\dist\flutter-agent\*"; DestDir: "{app}\agent"; \
  Flags: ignoreversion recursesubdirs createallsubdirs; Components: agent
Source: "..\docs\agent-app.md"; DestDir: "{app}\agent\docs"; Flags: ignoreversion; Components: agent

[Icons]
; The face of the tool: the windowed GUI (unchanged in v0.31 —
; the Flutter faces get their own shortcuts alongside).
Name: "{autoprograms}\BeeSky"; Filename: "{app}\beesky-gui.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky-gui.exe"; \
  Comment: "BeeSky - Quét & chẩn đoán máy đào"; Components: main
Name: "{autodesktop}\BeeSky"; Filename: "{app}\beesky-gui.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky-gui.exe"; \
  Comment: "BeeSky - Quét & chẩn đoán máy đào"; \
  Tasks: desktopicon; Components: main
Name: "{autoprograms}\BeeSky Flutter"; Filename: "{app}\beesky_app.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky_app.exe"; \
  Comment: "BeeSky (Flutter) - Quét & chẩn đoán máy đào"; Components: main
; Power users: a console that stays open (/k) with beesky on PATH.
Name: "{autoprograms}\BeeSky Console"; Filename: "{cmd}"; Parameters: "/k"; \
  WorkingDir: "{userdocs}"; IconFilename: "{app}\beesky.exe"; \
  Comment: "BeeSky console - try: beesky scan 192.168.1.0/24"
; The agent: bare beesky-agent.exe opens the (Tk) config window,
; exactly as in the standalone installer; the Flutter face is
; alongside it.
Name: "{autoprograms}\BeeSky Agent"; Filename: "{app}\agent\beesky-agent.exe"; \
  WorkingDir: "{app}\agent"; IconFilename: "{app}\agent\beesky-agent.exe"; \
  Comment: "BeeSky Agent - Cấu hình agent tại trại"; Components: agent
Name: "{autoprograms}\BeeSky Agent (Flutter)"; Filename: "{app}\agent\beesky_agent_app.exe"; \
  WorkingDir: "{app}\agent"; IconFilename: "{app}\agent\beesky_agent_app.exe"; \
  Comment: "BeeSky Agent (Flutter) - Cấu hình agent tại trại"; Components: agent

[Registry]
; Append {app} to the user PATH (only if not already there — see
; NeedsAddPath below; removal on uninstall is in RemoveFromPath).
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; \
  ValueName: "Path"; ValueData: "{olddata};{app}"; \
  Flags: preservestringtype; Check: NeedsAddPath(ExpandConstant('{app}'))

[Code]
const
  EnvKey = 'Environment';

function NeedsAddPath(AppDir: string): Boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, EnvKey, 'Path', OrigPath) then
  begin
    Result := True;
    Exit;
  end;
  { Bracket with ';' so "C:\BeeSky2" never matches "C:\BeeSky". }
  Result := Pos(';' + AppDir + ';', ';' + OrigPath + ';') = 0;
end;

procedure RemoveFromPath(AppDir: string);
var
  OrigPath: string;
  P: Integer;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, EnvKey, 'Path', OrigPath) then
    Exit;
  { Same padded search as NeedsAddPath: the match position in the
    padded string is where "<AppDir>;" (or the trailing ";") starts
    in the original, so deleting Length(AppDir)+1 chars removes the
    entry plus one separator. A leftover trailing ';' is trimmed. }
  P := Pos(';' + AppDir + ';', ';' + OrigPath + ';');
  if P = 0 then
    Exit;
  Delete(OrigPath, P, Length(AppDir) + 1);
  if (Length(OrigPath) > 0) and (OrigPath[Length(OrigPath)] = ';') then
    Delete(OrigPath, Length(OrigPath), 1);
  RegWriteExpandStringValue(HKEY_CURRENT_USER, EnvKey, 'Path', OrigPath);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RemoveFromPath(ExpandConstant('{app}'));
end;

{ --- Optional agent pairing page (v0.31) --------------------------
  The Pulse pattern (docs/agent-app-mapping.md §2): offer the
  agent's pairing values DURING install. Optional — all three
  fields or none. The wizard writes the core's config file itself
  (its legacy plain-text JSON form; ASCII-only via JsonEscape, so
  the byte encoding is unambiguous), ONLY when the agent component
  is selected and no config exists yet — an upgrade never clobbers
  a configured farm PC. The target stays empty on purpose: the
  app's first-run prefill (this machine's own subnet) fills it. }

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
      { Per UTF-16 code unit: a surrogate pair becomes two \uXXXX
        escapes, which is exactly valid JSON for astral chars. }
      Result := Result + Format('\u%.4x', [C])
    else
      Result := Result + S[I];
  end;
end;

function PairShouldSkip(Page: TWizardPage): Boolean;
begin
  Result := (not WizardIsComponentSelected('agent'))
    or FileExists(AgentConfigPath);
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
  PairPage := CreateCustomPage(wpSelectComponents,
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
