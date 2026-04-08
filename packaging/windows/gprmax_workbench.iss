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
Name: "advanced\install_vs_build_tools"; Description: "Download and run Microsoft Visual Studio Build Tools for C++ (optional)"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\GPRMax Workbench"; Filename: "{app}\GPRMax Workbench.exe"
Name: "{autodesktop}\GPRMax Workbench"; Filename: "{app}\GPRMax Workbench.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GPRMax Workbench.exe"; Description: "Launch GPRMax Workbench"; Flags: nowait postinstall skipifsilent
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\support\install_vs_build_tools.ps1"""; Description: "Download and start Microsoft Visual Studio Build Tools for C++"; Flags: postinstall skipifsilent waituntilterminated; Tasks: advanced\install_vs_build_tools

[Code]
var
  VsBuildToolsPage: TWizardPage;
  VsBuildToolsInfo: TNewStaticText;

procedure InitializeWizard;
begin
  VsBuildToolsPage := CreateCustomPage(
    wpSelectDir,
    'Optional Visual Studio Build Tools',
    'Advanced gprMax engine prerequisites'
  );

  VsBuildToolsInfo := TNewStaticText.Create(VsBuildToolsPage);
  VsBuildToolsInfo.Parent := VsBuildToolsPage.Surface;
  VsBuildToolsInfo.AutoSize := False;
  VsBuildToolsInfo.Left := 0;
  VsBuildToolsInfo.Top := 0;
  VsBuildToolsInfo.Width := VsBuildToolsPage.SurfaceWidth;
  VsBuildToolsInfo.Height := ScaleY(140);
  VsBuildToolsInfo.WordWrap := True;
  VsBuildToolsInfo.Caption :=
    'The bundled application can run without Microsoft Visual Studio Build Tools.' + #13#10#13#10 +
    'However, gprMax engine rebuild or repair workflows on this machine require the C++ Build Tools workload.' + #13#10#13#10 +
    'On the next installer page you can optionally choose to download and launch the Microsoft Build Tools installer with the Desktop C++ workload.';
end;
