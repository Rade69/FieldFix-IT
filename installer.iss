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
SetupIconFile=branding\installer_icon.ico
WizardImageFile=branding\wizard_panel.bmp
WizardSmallImageFile=branding\wizard_icon_64.bmp
WizardStyle=classic

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
; Branding used by the custom header on inner wizard pages
Source: "branding\wizard_classic_banner.bmp"; Flags: dontcopy

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

; Context: agent_reports/2026-07-01_installer-header-banner.md
[Code]
var
  HeaderBanner: TBitmapImage;

function IsInnerWizardPage(PageID: Integer): Boolean;
begin
  Result :=
    (PageID <> wpWelcome) and
    (PageID <> wpPreparing) and
    (PageID <> wpInstalling) and
    (PageID <> wpFinished);
end;

procedure UpdateHeaderBanner(PageID: Integer);
begin
  if HeaderBanner = nil then
  begin
    Exit;
  end;

  HeaderBanner.Visible := IsInnerWizardPage(PageID);
  if HeaderBanner.Visible then
  begin
    HeaderBanner.BringToFront;
  end;
end;

procedure InitializeWizard;
begin
  ExtractTemporaryFile('wizard_classic_banner.bmp');

  WizardForm.MainPanel.Height := ScaleY(128);
  WizardForm.InnerNotebook.Top := WizardForm.MainPanel.Top + WizardForm.MainPanel.Height;
  WizardForm.InnerNotebook.Height := WizardForm.Bevel.Top - WizardForm.InnerNotebook.Top;

  HeaderBanner := TBitmapImage.Create(WizardForm);
  HeaderBanner.Parent := WizardForm.MainPanel;
  HeaderBanner.AutoSize := False;
  HeaderBanner.Stretch := True;
  HeaderBanner.SetBounds(0, 0, WizardForm.MainPanel.Width, ScaleY(72));
  HeaderBanner.Bitmap.LoadFromFile(ExpandConstant('{tmp}\wizard_classic_banner.bmp'));
  HeaderBanner.Visible := False;

  WizardForm.PageNameLabel.Left := ScaleX(24);
  WizardForm.PageNameLabel.Top := ScaleY(78);
  WizardForm.PageNameLabel.Width := WizardForm.MainPanel.Width - ScaleX(48);
  WizardForm.PageDescriptionLabel.Left := ScaleX(24);
  WizardForm.PageDescriptionLabel.Top := ScaleY(101);
  WizardForm.PageDescriptionLabel.Width := WizardForm.MainPanel.Width - ScaleX(48);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  UpdateHeaderBanner(CurPageID);
end;
