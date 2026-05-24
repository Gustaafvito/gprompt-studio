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

[Messages]
; Texto del prompt en español para la pregunta de limpieza.
spanish.ConfirmUninstall=¿Desea desinstalar G-Prompt Studio y todos sus componentes?

[CustomMessages]
spanish.AskWipeData=¿Quieres borrar TAMBIÉN tus datos personales?%n%nEsto eliminará:%n  • API keys cifradas%n  • Historial de prompts%n  • Favoritos y estrellas%n  • Plantillas y backups%n  • Personajes y LoRAs%n%nUbicación: %s%n%nResponde NO si vas a reinstalar más tarde y quieres conservar tu configuración.
english.AskWipeData=Do you want to ALSO delete your personal data?%n%nThis will remove:%n  • Encrypted API keys%n  • Prompt history%n  • Favorites and stars%n  • Templates and backups%n  • Characters and LoRAs%n%nLocation: %s%n%nAnswer NO if you plan to reinstall later and want to keep your settings.

spanish.WipeDone=Datos personales eliminados.
english.WipeDone=Personal data removed.

spanish.WipeKeyringHint=Tip: si configuraste API keys vía Windows Credential Manager, ábrelo y borra las entradas que empiecen por "GPromptStudio_" o "arquitecto_prompts".
english.WipeKeyringHint=Tip: if you stored API keys in Windows Credential Manager, open it and delete entries starting with "GPromptStudio_" or "arquitecto_prompts".

[Code]
function GetUserDataDir(Param: String): String;
begin
  Result := ExpandConstant('{%USERPROFILE}\.arquitecto_prompts');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserDataDir: String;
  Response: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    UserDataDir := GetUserDataDir('');
    if DirExists(UserDataDir) then
    begin
      Response := MsgBox(
        Format(CustomMessage('AskWipeData'), [UserDataDir]),
        mbConfirmation,
        MB_YESNO or MB_DEFBUTTON2);
      if Response = IDYES then
      begin
        DelTree(UserDataDir, True, True, True);
        MsgBox(CustomMessage('WipeDone') + #13#10#13#10 + CustomMessage('WipeKeyringHint'),
               mbInformation, MB_OK);
      end;
    end;
  end;
end;
