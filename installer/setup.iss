[Setup]
AppName=FieldFix IT
AppVersion=0.1.0
DefaultDirName={autopf}\FieldFix IT
DefaultGroupName=FieldFix IT
OutputBaseFilename=FieldFixIT_Setup_v0.1.0
SetupIconFile=..\asset\icons\fieldfix_icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "..\dist\FieldFix IT.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\FieldFix IT"; Filename: "{app}\FieldFix IT.exe"
Name: "{commondesktop}\FieldFix IT"; Filename: "{app}\FieldFix IT.exe"
