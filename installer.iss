; Inno Setup script for G-Prompt Studio
; Requiere Inno Setup 6 (https://jrsoftware.org/isinfo.php)
;
; Uso:
;   1. Generar primero el .exe con:  python build.py
;   2. Compilar este script:         ISCC.exe installer.iss
;      (o desde build.py: python build.py --installer)
;   3. Resultado: dist/installer/GPromptStudio-Setup-X.Y.Z.exe

#define MyAppName "G-Prompt Studio"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Gustaafvito"
#define MyAppURL "https://github.com/gustaafvito/gprompt-studio"
#define MyAppExeName "GPromptStudio.exe"
#define MyAppId "{{B3F8E2A1-7C4D-4F90-8B12-D5E9C3A6F841}}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist\installer
OutputBaseFilename=GPromptStudio-Setup-{#MyAppVersion}
SetupIconFile=
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName} {#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; \
    OnlyBelowVersion: 6.1

[Files]
; Distribuir TODO el contenido de dist\GPromptStudio (output del PyInstaller en modo onedir)
Source: "dist\GPromptStudio\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpiar carpeta de usuario al desinstalar (datos, no las keys)
; Comentado por defecto — descomenta si quieres limpieza total al desinstalar:
; Type: filesandordirs; Name: "{userappdata}\arquitecto_prompts"
