; Script Inno Setup pour Theme Manager.
; Compilé par le workflow GitHub Actions (.github/workflows/build-installer.yml) avec :
;   ISCC.exe installer\setup.iss /DAppVersion=1.0.0
; AppVersion a une valeur par défaut pour permettre une compilation manuelle locale.

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

[Setup]
AppId={{FBAB7E8A-A4F4-4572-AC2D-4FA87DF779F5}
AppName=Theme Manager
AppVersion={#AppVersion}
AppPublisher=Theme Manager
DefaultDirName={autopf}\ThemeManager
DefaultGroupName=Theme Manager
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist_installer
OutputBaseFilename=ThemeManagerSetup-{#AppVersion}
Compression=lzma
SolidCompression=yes
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\ThemeManager.exe
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\ThemeManager.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Theme Manager"; Filename: "{app}\ThemeManager.exe"
Name: "{group}\Désinstaller Theme Manager"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\ThemeManager.exe"; Description: "Lancer Theme Manager"; Flags: nowait postinstall skipifsilent
