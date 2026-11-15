; BeeSky Scanner installer: scanner UI, diagnostics engine and Tk fallback.
; Agent is a separate installation. Saved scanner data lives in user AppData.
#define MyAppName "BeeSky"
#define MyAppVersion "0.42.0"
#define MyAppPublisher "BeeSkyBase"
#define MyAppExeName "beesky_app.exe"

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
AppMutex=Local\BeeSky.Scanner.UI
CloseApplications=yes
ChangesEnvironment=yes

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
Source: "..\dist\beesky-gui.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\flutter-main\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; The redesigned native UI is primary; keep Tk as the compatibility option.
Name: "{autoprograms}\BeeSky"; Filename: "{app}\beesky_app.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky_app.exe"; \
  Comment: "BeeSky - Quét & chẩn đoán máy đào"
Name: "{autodesktop}\BeeSky"; Filename: "{app}\beesky_app.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky_app.exe"; \
  Comment: "BeeSky - Quét & chẩn đoán máy đào"; \
  Tasks: desktopicon
Name: "{autoprograms}\BeeSky (Compatibility)"; Filename: "{app}\beesky-gui.exe"; \
  WorkingDir: "{app}"; IconFilename: "{app}\beesky-gui.exe"; \
  Comment: "BeeSky (Compatibility) - Quét & chẩn đoán máy đào"
; Power users: a console that stays open (/k) with beesky on PATH.
Name: "{autoprograms}\BeeSky Console"; Filename: "{cmd}"; Parameters: "/k"; \
  WorkingDir: "{userdocs}"; IconFilename: "{app}\beesky.exe"; \
  Comment: "BeeSky console - try: beesky scan 192.168.1.0/24"

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


procedure PreserveScannerFile(const Name: String);
var
  Source, Destination: String;
begin
  Source := ExpandConstant('{app}\') + Name;
  if not FileExists(Source) then Exit;
  if (Name = 'beesky-settings.json') or (Name = 'beesky-events.json') then
    Destination := ExpandConstant('{localappdata}\BeeSky\') + Name
  else
    Destination := ExpandConstant('{userappdata}\BeeSky\') + Name;
  if FileExists(Destination) then
    Destination := ExpandConstant('{userappdata}\BeeSky\LegacyBackups\')
      + GetDateTimeString('yyyymmdd-hhnnss', '', '') + '\' + Name;
  ForceDirectories(ExtractFileDir(Destination));
  if FileCopy(Source, Destination, True) then DeleteFile(Source);
end;

procedure PreserveScannerData;
var
  Destination, Source: String;
begin
  PreserveScannerFile('beesky-creds.json');
  PreserveScannerFile('beesky-groups.json');
  PreserveScannerFile('beesky-grid.json');
  PreserveScannerFile('beesky-history.json');
  PreserveScannerFile('beesky-notes.json');
  PreserveScannerFile('beesky-events.json');
  PreserveScannerFile('beesky-settings.json');
  PreserveScannerFile('beesky-ops-history.json');
  PreserveScannerFile('beesky-ops-job.json');
  PreserveScannerFile('beesky-ipreports.json');
  Source := ExpandConstant('{app}\tickets');
  if DirExists(Source) then begin
    Destination := ExpandConstant('{userappdata}\BeeSky\tickets');
    if DirExists(Destination) then
      Destination := ExpandConstant('{userappdata}\BeeSky\LegacyBackups\')
        + GetDateTimeString('yyyymmdd-hhnnss', '', '') + '\tickets';
    ForceDirectories(ExtractFileDir(Destination));
    RenameFile(Source, Destination);
  end;
end;
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then PreserveScannerData;
  if CurUninstallStep = usPostUninstall then
    RemoveFromPath(ExpandConstant('{app}'));
end;
