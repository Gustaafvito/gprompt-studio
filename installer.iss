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
; AppId con escape doble `{{...}}` — sintaxis OBLIGATORIA de Inno Setup
; cuando el AppId contiene llaves (GUID). Sin el escape, Inno intenta
; interpretar `{...}` como constante (tipo {app}/{group}) y rompe la
; compilación.
;
; Consecuencia: la clave de registro queda como `{...}}_is1` (1 llave
; inicial, 2 finales). No es un bug, es comportamiento documentado de
; Inno. El código de detección en [Code] busca esa forma directamente
; vía GetRegKeyLegacy (con `}}_is1`), y también la forma alternativa
; GetRegKeyClean por si Inno cambia su comportamiento en una futura
; versión.
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
SetupIconFile=assets\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName} {#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Cerrar la app si está corriendo antes de instalar (evita "archivo en uso")
CloseApplications=force
RestartApplications=no

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

; Mensaje del diálogo "ya está instalado" — 3 opciones (Reparar/Desinstalar/Cancelar)
spanish.AlreadyInstalledTitle=G-Prompt Studio ya está instalado
english.AlreadyInstalledTitle=G-Prompt Studio is already installed
spanish.AlreadyInstalled=Ya tienes G-Prompt Studio %s instalado en:%n  %s%n%n¿Qué quieres hacer?%n%n  • Sí = REINSTALAR / REPARAR (sobre la instalación actual, conserva tus datos)%n  • No = DESINSTALAR (te llevará al desinstalador)%n  • Cancelar = Salir sin tocar nada
english.AlreadyInstalled=G-Prompt Studio %s is already installed in:%n  %s%n%nWhat do you want to do?%n%n  • Yes = REINSTALL / REPAIR (over current install, keeps your data)%n  • No = UNINSTALL (launches the uninstaller)%n  • Cancel = Exit without changes

spanish.LaunchingUninstaller=Lanzando el desinstalador…
english.LaunchingUninstaller=Launching uninstaller…

[Code]
function GetUserDataDir(Param: String): String;
begin
  Result := ExpandConstant('{%USERPROFILE}\.arquitecto_prompts');
end;

// ─────────────────────────────────────────────────────────────────────
// Detección de instalación previa
//
// Inno Setup registra cada instalación bajo
//   HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\{AppId}_is1
// o en HKCU si se instaló sin privilegios (PrivilegesRequired=lowest).
//
// IMPORTANTE: este installer tiene un AppId histórico que en el preprocesador
// usa escape `{{...}}` y Inno lo registra como `{...}}_is1` (UNA llave inicial,
// DOS finales). Buscamos AMBOS por compatibilidad: la entrada con doble llave
// final (legacy) y la entrada limpia con una sola (si algún día se arregla).
// ─────────────────────────────────────────────────────────────────────

function GetRegKeyLegacy(): String;
begin
  // Hardcoded con la forma que aparece realmente en el registro
  Result := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' +
            '{B3F8E2A1-7C4D-4F90-8B12-D5E9C3A6F841}}_is1';
end;

function GetRegKeyClean(): String;
begin
  // Forma "limpia" que tendría una entrada nueva sin el escape problemático
  Result := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' +
            '{B3F8E2A1-7C4D-4F90-8B12-D5E9C3A6F841}_is1';
end;

function TryReadStringFromAllRoots(Key, ValueName: String; var OutVal: String): Boolean;
begin
  Result := True;
  if RegQueryStringValue(HKCU, Key, ValueName, OutVal) then Exit;
  if RegQueryStringValue(HKLM, Key, ValueName, OutVal) then Exit;
  if IsWin64() then
    if RegQueryStringValue(HKLM64, Key, ValueName, OutVal) then Exit;
  Result := False;
end;

function ReadInstalledValue(ValueName: String): String;
begin
  Result := '';
  // Probar primero la forma legacy (la que está realmente en el registro hoy)
  if TryReadStringFromAllRoots(GetRegKeyLegacy(), ValueName, Result) then Exit;
  // Fallback a la forma limpia
  TryReadStringFromAllRoots(GetRegKeyClean(), ValueName, Result);
end;

function GetInstalledVersion(): String;
begin
  Result := ReadInstalledValue('DisplayVersion');
end;

function GetInstalledPath(): String;
begin
  Result := ReadInstalledValue('InstallLocation');
end;

function GetUninstallerPath(): String;
begin
  Result := ReadInstalledValue('UninstallString');
end;

function RunUninstaller(): Boolean;
var
  UninstStr: String;
  ResultCode: Integer;
begin
  Result := False;
  UninstStr := GetUninstallerPath();
  if UninstStr = '' then
    Exit;
  // Quitar comillas si las tiene
  UninstStr := RemoveQuotes(UninstStr);
  // Lanza el desinstalador y espera a que termine
  if Exec(UninstStr, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
    Result := (ResultCode = 0);
end;

function InitializeSetup(): Boolean;
var
  InstalledVer: String;
  InstalledPath: String;
  Msg: String;
  Response: Integer;
begin
  Result := True;
  InstalledVer := GetInstalledVersion();
  if InstalledVer = '' then
    Exit;  // No hay instalación previa, continuar setup normal

  InstalledPath := GetInstalledPath();
  if InstalledPath = '' then
    InstalledPath := '?';

  Msg := Format(CustomMessage('AlreadyInstalled'), [InstalledVer, InstalledPath]);
  Response := MsgBox(Msg, mbConfirmation, MB_YESNOCANCEL or MB_DEFBUTTON1);

  case Response of
    IDYES:
      // Reinstalar / reparar: continuar con el setup normal
      Result := True;
    IDNO:
      begin
        // Desinstalar
        MsgBox(CustomMessage('LaunchingUninstaller'), mbInformation, MB_OK);
        RunUninstaller();
        Result := False;  // Salir del setup tras lanzar el uninstaller
      end;
    IDCANCEL:
      // Cancelar: salir sin tocar nada
      Result := False;
  end;
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
