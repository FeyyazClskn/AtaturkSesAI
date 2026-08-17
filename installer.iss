#define MyAppName "Atatürk TTS"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Atatürk TTS"
#define MyAppExeName "AtaturkTTS.exe"

[Setup]
AppId={{B7C7B90B-3B3C-4A8E-A6B0-7A7A7A7A7A01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\AtaturkTTS
DefaultGroupName={#MyAppName}
OutputDir=installer-output
OutputBaseFilename=AtaturkTTS-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "dist\AtaturkTTS.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Atatürk TTS"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Atatürk TTS"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Ek kısayollar:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Atatürk TTS'yi başlat"; Flags: nowait postinstall skipifsilent
