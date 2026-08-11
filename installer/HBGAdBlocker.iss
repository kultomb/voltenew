; HBG AdBlocker — Windows Setup (Inno Setup 6)
; Chay build_installer.bat de dong goi EXE + file cai dat.

#include "build_defines.iss"

#define MyAppId "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"
#define MyAppExeName HBGExeBaseName + ".exe"
#define MySetupExeName "HBGAdBlocker_Setup_v" + HBGAppVersion

[Setup]
AppId={#MyAppId}
AppName={#HBGAppName}
AppVersion={#HBGAppVersion}
AppPublisher={#HBGAppPublisher}
DefaultDirName={autopf}\{#HBGAppName}
DefaultGroupName={#HBGAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\releases
OutputBaseFilename={#MySetupExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\icons\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#HBGAppVersion}
VersionInfoCompany={#HBGAppPublisher}
VersionInfoDescription={#HBGAppName} — Xoa quang cao, don rac
VersionInfoProductName={#HBGAppName}
VersionInfoProductVersion={#HBGAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tao shortcut tren Desktop"; GroupDescription: "Shortcut:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#HBGAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#HBGAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Mo {#HBGAppName}"; Flags: nowait postinstall skipifsilent
