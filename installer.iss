; FieldFix IT — Inno Setup 6 installer script
; Build: ISCC installer.iss
; Output: installer_output/FieldFix_IT_Setup_x.y.z.exe

#define AppName        "FieldFix IT"
#define AppVersion     "0.1.0"
#define AppPublisher   "Radovan"
#define AppExeName     "FieldFix IT.exe"
#define AppId          "{{A7C3F21E-84B2-4D09-B6E5-3F8C91D2A047}"
#define BuildDir       "dist\FieldFix IT"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/
AppSupportURL=https://github.com/
AppUpdatesURL=https://github.com/

; Install to Program Files (64-bit)
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes

; Output
OutputDir=installer_output
OutputBaseFilename=FieldFix_IT_Setup_{#AppVersion}
SetupIconFile=app\resources\icons\fieldfix_icon.ico
WizardSmallImageFile=app\resources\icons\fieldfix_icon_64.png
WizardStyle=modern

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; 64-bit Windows only (our build is x64)
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

; Require at least Windows 10
MinVersion=10.0.17763

; Privileges: admin required (installing to Program Files)
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
; Settings are per-user (%APPDATA%) — uninstaller runs as same user, path is correct
UsedUserAreasWarning=no

; Uninstall info (visible in Windows Settings → Apps)
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; All files from the PyInstaller one-folder build
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop (optional — user decides during install)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove user settings from %APPDATA%\FieldFix IT
Type: filesandordirs; Name: "{userappdata}\FieldFix IT"
