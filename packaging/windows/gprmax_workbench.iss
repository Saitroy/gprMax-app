#define MyAppName "GPRMax Workbench"
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
#ifndef SourceDir
  #error SourceDir must be defined from build_installer.ps1
#endif
#ifndef OutputDir
  #define OutputDir "..\\..\\dist\\installer"
#endif

[Setup]
AppId={{AEA5BB3B-D5A5-4F10-A0E9-6B0C565F3BB9}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher=Open-source contributors
DefaultDirName={autopf}\GPRMax Workbench
DefaultGroupName=GPRMax Workbench
UninstallDisplayIcon={app}\GPRMax Workbench.exe
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma
SolidCompression=yes
WizardStyle=modern
OutputDir={#OutputDir}
OutputBaseFilename=gprmax-workbench-{#AppVersion}-windows-x64
LicenseFile={#SourceDir}\licenses\GPRMax-Workbench-LICENSE.txt
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\GPRMax Workbench"; Filename: "{app}\GPRMax Workbench.exe"
Name: "{autodesktop}\GPRMax Workbench"; Filename: "{app}\GPRMax Workbench.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GPRMax Workbench.exe"; Description: "Launch GPRMax Workbench"; Flags: nowait postinstall skipifsilent
