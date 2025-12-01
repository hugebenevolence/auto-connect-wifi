; Inno Setup script to create an installer for Auto_login_wifi
; Put this file next to the built executable `AutoWifiHelperGUI.exe` and compile with ISCC.exe

[Setup]
AppName=Auto_login_wifi
AppVersion=1.0
DefaultDirName={pf}\Auto_login_wifi
DefaultGroupName=Auto_login_wifi
DisableProgramGroupPage=yes
Compression=lzma
SolidCompression=yes
OutputDir=.
OutputBaseFilename=Auto_login_wifi_Setup
PrivilegesRequired=admin
AllowNoIcons=yes

[Files]
Source: "AutoWifiHelperGUI.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Auto_login_wifi"; Filename: "{app}\AutoWifiHelperGUI.exe"
Name: "{autodesktop}\Auto_login_wifi"; Filename: "{app}\AutoWifiHelperGUI.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
; Optionally run the application after install
Filename: "{app}\AutoWifiHelperGUI.exe"; Description: "Launch Auto_login_wifi"; Flags: nowait postinstall skipifsilent
