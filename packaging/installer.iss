; BeeSky Windows installer (Inno Setup 6)
;
; Per-user install: lands in %LocalAppData%\Programs\BeeSky, needs NO
; admin rights (PrivilegesRequired=lowest) — a workshop PC can install
; it as-is. Adds the install dir to the *user* PATH so `beesky` works
; from any console, and creates a Start Menu "BeeSky" shortcut that
; opens a console ready for commands like:
;
;     beesky scan 192.168.1.0/24
;     beesky watch 192.168.1.0/24 --notify notify.json
;
; Build (on Windows, after PyInstaller has produced dist\beesky.exe):
;
;     iscc packaging\installer.iss
;
; Output: dist\BeeSkySetup-0.3.0.exe  (built by
; .github/workflows/build-windows.yml — never by hand)

#define MyAppName "BeeSky"
#define MyAppVersion "0.3.0"
#define MyAppPublisher "BeeSkyBase"
#define MyAppExeName "beesky.exe"

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
SetupIconFile=beesky.ico
UninstallDisplayIcon={app}\beesky.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
  GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\beesky.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "beesky.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\notify.example.json"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; A console that stays open (/k) with beesky on PATH.
Name: "{autoprograms}\BeeSky"; Filename: "{cmd}"; Parameters: "/k"; \
  WorkingDir: "{userprofile}"; IconFilename: "{app}\beesky.exe"; \
  Comment: "BeeSky console - try: beesky scan 192.168.1.0/24"
Name: "{autodesktop}\BeeSky"; Filename: "{cmd}"; Parameters: "/k"; \
  WorkingDir: "{userprofile}"; IconFilename: "{app}\beesky.exe"; \
  Comment: "BeeSky console - try: beesky scan 192.168.1.0/24"; \
  Tasks: desktopicon

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
