; ============================================================================
;  installer.iss — NetPuff Windows 安装包（Inno Setup 6）
;  构建：ISCC.exe app\installer.iss
;  产物：dist\NetPuff-<版本>-Setup.exe（按用户安装，无需管理员）
; ============================================================================
#define MyAppName "NetPuff"
#define MyAppVersion "1.2.0"
#define MyAppExeName "NetPuff.exe"
#define MyAppPublisher "hengjunguo35-oss"
#define MyAppURL "https://github.com/hengjunguo35-oss/NetPuff"

[Setup]
AppId={{B7E1D2A4-6C3F-4B7E-9D2A-1F5C8E3A9B60}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=NetPuff-{#MyAppVersion}-Setup
SetupIconFile=netpuff.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务："; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README-Windows.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 NetPuff"; Flags: nowait postinstall skipifsilent
