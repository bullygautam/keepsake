#define MyAppName "Keepsake Studio"
#define MyAppVersion "5.2"
#define MyAppExeName "KeepsakeStudio.exe"
[Setup]
AppId={{7E2D4C7F-A5CE-472C-B0DE-5E72911AA4CD}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Keepsake Studio
DefaultGroupName=Keepsake Studio
OutputDir=installer
OutputBaseFilename=KeepsakeStudio_Setup_5_2
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
[Files]
Source: "dist\KeepsakeStudio\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
[Icons]
Name: "{autoprograms}\Keepsake Studio"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Keepsake Studio"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Keepsake Studio"; Flags: nowait postinstall skipifsilent
