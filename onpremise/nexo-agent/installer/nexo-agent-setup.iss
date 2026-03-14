; ============================================================================
; InsERT Nexo Agent — Inno Setup Installer Script
;
; Creates a Windows installer with wizard pages for:
;   1. Prerequisites check (Python 3.12, .NET 8.0 Runtime)
;   2. Nexo SDK path selection
;   3. SQL Server connection configuration
;   4. Nexo operator credentials
;   5. Warehouse & branch defaults
;   6. Pinquark Cloud connection
;   7. Sync & service settings
;   8. Windows Service installation
;
; Build:  iscc nexo-agent-setup.iss
; Output: Output/PinquarkNexoAgentSetup_1.0.0.exe
; ============================================================================

#define AppName      "Pinquark Nexo Agent"
#define AppVersion   "1.0.0"
#define AppPublisher "Pinquark.com"
#define AppURL       "https://pinquark.com"
#define AppExeName   "start-agent.bat"

[Setup]
AppId={{B7A3E5F2-4D1C-4E8F-9A2B-6C3D7E8F1A2B}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\Pinquark\NexoAgent
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=PinquarkNexoAgentSetup_{#AppVersion}
SetupIconFile=assets\pinquark-nexo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
MinVersion=10.0
LicenseFile=..\..\..\LICENSE
WizardImageFile=assets\wizard-banner.bmp
WizardSmallImageFile=assets\wizard-small.bmp
UninstallDisplayIcon={app}\assets\pinquark-nexo.ico

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Application files
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\gunicorn.conf.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\connector.yaml"; DestDir: "{app}"; Flags: ignoreversion

; Installer scripts
Source: "scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs

; Service wrapper
Source: "service\nexo-agent-service.xml"; DestDir: "{app}\service"; Flags: ignoreversion
Source: "service\WinSW.exe"; DestDir: "{app}\service"; DestName: "nexo-agent-service.exe"; Flags: ignoreversion

; Assets
Source: "assets\pinquark-nexo.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

; Batch launchers
Source: "scripts\start-agent.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "scripts\stop-agent.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\pinquark-nexo.ico"
Name: "{group}\{#AppName} — Dokumentacja API"; Filename: "http://localhost:8000/docs"
Name: "{group}\Odinstaluj {#AppName}"; Filename: "{uninstallexe}"

; ============================================================================
; Custom wizard pages (Pascal Script)
; ============================================================================

[Code]

var
  // Page references
  PagePrerequisites: TWizardPage;
  PageSdkPath: TInputDirWizardPage;
  PageSqlServer: TInputQueryWizardPage;
  PageNexoCredentials: TInputQueryWizardPage;
  PageWarehouse: TInputQueryWizardPage;
  PageCloud: TInputQueryWizardPage;
  PageService: TInputOptionWizardPage;

  // Status labels for prerequisites
  LblPythonStatus: TNewStaticText;
  LblDotnetStatus: TNewStaticText;
  LblSdkStatus: TNewStaticText;
  BtnInstallPython: TNewButton;
  BtnInstallDotnet: TNewButton;

// ---- Utility functions ----

function IsPythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/c python --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function IsDotnetInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/c dotnet --list-runtimes', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function IsNexoSdkPresent(Path: String): Boolean;
begin
  Result := FileExists(Path + '\InsERT.Moria.API.dll') and
            FileExists(Path + '\InsERT.Moria.Sfera.dll') and
            FileExists(Path + '\InsERT.Moria.ModelDanych.dll');
end;

procedure UpdatePrerequisiteStatus;
begin
  if IsPythonInstalled then
  begin
    LblPythonStatus.Caption := '   Python 3.12+     ✓ zainstalowany';
    LblPythonStatus.Font.Color := clGreen;
    BtnInstallPython.Enabled := False;
  end
  else
  begin
    LblPythonStatus.Caption := '   Python 3.12+     ✗ brak';
    LblPythonStatus.Font.Color := clRed;
    BtnInstallPython.Enabled := True;
  end;

  if IsDotnetInstalled then
  begin
    LblDotnetStatus.Caption := '   .NET 8.0 Runtime  ✓ zainstalowany';
    LblDotnetStatus.Font.Color := clGreen;
    BtnInstallDotnet.Enabled := False;
  end
  else
  begin
    LblDotnetStatus.Caption := '   .NET 8.0 Runtime  ✗ brak';
    LblDotnetStatus.Font.Color := clRed;
    BtnInstallDotnet.Enabled := True;
  end;
end;

procedure BtnInstallPythonClick(Sender: TObject);
var
  ResultCode: Integer;
begin
  MsgBox('Zostanie pobrana i uruchomiona instalacja Python 3.12.'#13#10 +
         'Po zainstalowaniu kliknij "Odśwież" aby sprawdzić ponownie.',
         mbInformation, MB_OK);
  ShellExec('open', 'https://www.python.org/downloads/', '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
end;

procedure BtnInstallDotnetClick(Sender: TObject);
var
  ResultCode: Integer;
begin
  MsgBox('Zostanie otwarta strona pobierania .NET 8.0 Runtime.'#13#10 +
         'Zainstaluj "ASP.NET Core Runtime 8.0" lub ".NET Runtime 8.0".',
         mbInformation, MB_OK);
  ShellExec('open', 'https://dotnet.microsoft.com/en-us/download/dotnet/8.0', '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
end;

procedure BtnRefreshClick(Sender: TObject);
begin
  UpdatePrerequisiteStatus;
end;

// ---- Page creation ----

procedure CreatePrerequisitesPage;
var
  LblTitle: TNewStaticText;
  BtnRefresh: TNewButton;
begin
  PagePrerequisites := CreateCustomPage(wpSelectDir,
    'Wymagania systemowe',
    'Sprawdzanie wymaganych komponentów systemu');

  LblTitle := TNewStaticText.Create(PagePrerequisites);
  LblTitle.Parent := PagePrerequisites.Surface;
  LblTitle.Caption := 'Agent wymaga następujących komponentów:';
  LblTitle.Top := 10;
  LblTitle.Font.Style := [fsBold];

  // Python status
  LblPythonStatus := TNewStaticText.Create(PagePrerequisites);
  LblPythonStatus.Parent := PagePrerequisites.Surface;
  LblPythonStatus.Top := 45;
  LblPythonStatus.Left := 10;
  LblPythonStatus.Font.Size := 10;

  BtnInstallPython := TNewButton.Create(PagePrerequisites);
  BtnInstallPython.Parent := PagePrerequisites.Surface;
  BtnInstallPython.Caption := 'Pobierz Python';
  BtnInstallPython.Top := 40;
  BtnInstallPython.Left := 340;
  BtnInstallPython.Width := 120;
  BtnInstallPython.OnClick := @BtnInstallPythonClick;

  // .NET status
  LblDotnetStatus := TNewStaticText.Create(PagePrerequisites);
  LblDotnetStatus.Parent := PagePrerequisites.Surface;
  LblDotnetStatus.Top := 80;
  LblDotnetStatus.Left := 10;
  LblDotnetStatus.Font.Size := 10;

  BtnInstallDotnet := TNewButton.Create(PagePrerequisites);
  BtnInstallDotnet.Parent := PagePrerequisites.Surface;
  BtnInstallDotnet.Caption := 'Pobierz .NET 8.0';
  BtnInstallDotnet.Top := 75;
  BtnInstallDotnet.Left := 340;
  BtnInstallDotnet.Width := 120;
  BtnInstallDotnet.OnClick := @BtnInstallDotnetClick;

  // SDK info
  LblSdkStatus := TNewStaticText.Create(PagePrerequisites);
  LblSdkStatus.Parent := PagePrerequisites.Surface;
  LblSdkStatus.Top := 115;
  LblSdkStatus.Left := 10;
  LblSdkStatus.Font.Size := 10;
  LblSdkStatus.Caption := '   InsERT Nexo SDK   → wybierzesz na następnej stronie';
  LblSdkStatus.Font.Color := clGray;

  // Refresh button
  BtnRefresh := TNewButton.Create(PagePrerequisites);
  BtnRefresh.Parent := PagePrerequisites.Surface;
  BtnRefresh.Caption := 'Odśwież';
  BtnRefresh.Top := 160;
  BtnRefresh.Left := 10;
  BtnRefresh.Width := 100;
  BtnRefresh.OnClick := @BtnRefreshClick;
end;

procedure CreateSdkPathPage;
begin
  PageSdkPath := CreateInputDirPage(PagePrerequisites.ID,
    'Ścieżka do InsERT Nexo SDK',
    'Wskaż katalog Bin z plikami SDK (DLL)',
    'Wybierz folder zawierający pliki InsERT.Moria.API.dll, InsERT.Moria.Sfera.dll itp.'#13#10 +
    'Zwykle jest to: C:\nexoSDK\Bin lub C:\Program Files\InsERT\nexoSDK\Bin',
    False, '');
  PageSdkPath.Add('');
  PageSdkPath.Values[0] := 'C:\nexoSDK\Bin';
end;

procedure CreateSqlServerPage;
begin
  PageSqlServer := CreateInputQueryPage(PageSdkPath.ID,
    'Połączenie z SQL Server',
    'Konfiguracja połączenia z bazą danych InsERT Nexo',
    'Podaj dane połączenia z SQL Serverem, na którym zainstalowana jest baza Nexo.');
  PageSqlServer.Add('Serwer SQL (np. (local)\INSERTNEXO):', False);
  PageSqlServer.Add('Nazwa bazy danych:', False);
  PageSqlServer.Add('Login SQL (puste = Windows Auth):', False);
  PageSqlServer.Add('Hasło SQL (puste = Windows Auth):', True);
  PageSqlServer.Values[0] := '(local)\INSERTNEXO';
  PageSqlServer.Values[1] := 'Nexo_demo';
end;

procedure CreateNexoCredentialsPage;
begin
  PageNexoCredentials := CreateInputQueryPage(PageSqlServer.ID,
    'Operator InsERT Nexo',
    'Dane logowania operatora systemu Nexo',
    'Podaj login i hasło operatora Nexo, który będzie używany przez agenta.'#13#10 +
    'Operator musi mieć uprawnienia do modułu Subiekt.');
  PageNexoCredentials.Add('Login operatora Nexo:', False);
  PageNexoCredentials.Add('Hasło operatora Nexo:', True);
  PageNexoCredentials.Add('Moduł Nexo:', False);
  PageNexoCredentials.Values[0] := 'Admin';
  PageNexoCredentials.Values[2] := 'Subiekt';
end;

procedure CreateWarehousePage;
begin
  PageWarehouse := CreateInputQueryPage(PageNexoCredentials.ID,
    'Domyślny magazyn i oddział',
    'Konfiguracja kontekstu operacji w Nexo',
    'Podaj domyślny symbol magazynu i oddziału.'#13#10 +
    'Te wartości będą używane jako domyślne dla operacji dokumentów.');
  PageWarehouse.Add('Symbol magazynu (np. MAG):', False);
  PageWarehouse.Add('Symbol oddziału (np. CENTRALA):', False);
  PageWarehouse.Add('ID agenta (unikalna nazwa tego agenta):', False);
  PageWarehouse.Values[0] := 'MAG';
  PageWarehouse.Values[1] := 'CENTRALA';
  PageWarehouse.Values[2] := 'nexo-agent-001';
end;

procedure CreateCloudPage;
begin
  PageCloud := CreateInputQueryPage(PageWarehouse.ID,
    'Połączenie z Pinquark Cloud',
    'Konfiguracja połączenia z platformą integracyjną (opcjonalne)',
    'Podaj adres URL i klucz API platformy Pinquark.'#13#10 +
    'Jeśli nie korzystasz z chmury, pozostaw puste — agent będzie działał lokalnie.');
  PageCloud.Add('URL platformy Pinquark:', False);
  PageCloud.Add('Klucz API (API Key):', True);
  PageCloud.Add('Interwał synchronizacji (sekundy):', False);
  PageCloud.Add('Interwał heartbeat (sekundy):', False);
  PageCloud.Values[0] := 'http://localhost:8080';
  PageCloud.Values[2] := '300';
  PageCloud.Values[3] := '60';
end;

procedure CreateServicePage;
begin
  PageService := CreateInputOptionPage(PageCloud.ID,
    'Tryb uruchomienia',
    'Jak agent powinien być uruchamiany?',
    'Wybierz sposób uruchamiania agenta na tym komputerze.',
    True, False);
  PageService.Add('Zainstaluj jako usługę Windows (zalecane — autostart z systemem)');
  PageService.Add('Uruchamiaj ręcznie (skrót w menu Start)');
  PageService.SelectedValueIndex := 0;
end;

// ---- Initialization ----

procedure InitializeWizard;
begin
  CreatePrerequisitesPage;
  CreateSdkPathPage;
  CreateSqlServerPage;
  CreateNexoCredentialsPage;
  CreateWarehousePage;
  CreateCloudPage;
  CreateServicePage;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = PagePrerequisites.ID then
    UpdatePrerequisiteStatus;
end;

// ---- Validation ----

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  if CurPageID = PageSdkPath.ID then
  begin
    if not IsNexoSdkPresent(PageSdkPath.Values[0]) then
    begin
      if MsgBox('W wybranym folderze nie znaleziono plików SDK InsERT Nexo.'#13#10 +
                'Szukano: InsERT.Moria.API.dll, InsERT.Moria.Sfera.dll, InsERT.Moria.ModelDanych.dll'#13#10#13#10 +
                'Czy chcesz kontynuować mimo to?',
                mbConfirmation, MB_YESNO) = IDNO then
        Result := False;
    end;
  end;

  if CurPageID = PageSqlServer.ID then
  begin
    if (PageSqlServer.Values[0] = '') or (PageSqlServer.Values[1] = '') then
    begin
      MsgBox('Serwer SQL i nazwa bazy danych są wymagane.', mbError, MB_OK);
      Result := False;
    end;
  end;

  if CurPageID = PageNexoCredentials.ID then
  begin
    if (PageNexoCredentials.Values[0] = '') or (PageNexoCredentials.Values[1] = '') then
    begin
      MsgBox('Login i hasło operatora Nexo są wymagane.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

// ---- Generate .env configuration file ----

procedure GenerateEnvFile;
var
  Lines: TStringList;
  SqlAuthWindows: String;
begin
  Lines := TStringList.Create;
  try
    Lines.Add('# Pinquark Nexo Agent — auto-generated configuration');
    Lines.Add('# Generated by installer on ' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':'));
    Lines.Add('');

    Lines.Add('# Agent');
    Lines.Add('NEXO_AGENT_ID=' + PageWarehouse.Values[2]);
    Lines.Add('');

    Lines.Add('# SQL Server');
    Lines.Add('NEXO_SQL_SERVER=' + PageSqlServer.Values[0]);
    Lines.Add('NEXO_SQL_DATABASE=' + PageSqlServer.Values[1]);

    if (PageSqlServer.Values[2] = '') then
      SqlAuthWindows := 'true'
    else
      SqlAuthWindows := 'false';

    Lines.Add('NEXO_SQL_AUTH_WINDOWS=' + SqlAuthWindows);

    if SqlAuthWindows = 'false' then
    begin
      Lines.Add('NEXO_SQL_USERNAME=' + PageSqlServer.Values[2]);
      Lines.Add('NEXO_SQL_PASSWORD=' + PageSqlServer.Values[3]);
    end;

    Lines.Add('');
    Lines.Add('# Nexo operator');
    Lines.Add('NEXO_OPERATOR_LOGIN=' + PageNexoCredentials.Values[0]);
    Lines.Add('NEXO_OPERATOR_PASSWORD=' + PageNexoCredentials.Values[1]);
    Lines.Add('NEXO_PRODUCT=' + PageNexoCredentials.Values[2]);
    Lines.Add('');

    Lines.Add('# SDK');
    Lines.Add('NEXO_SDK_BIN_PATH=' + PageSdkPath.Values[0]);
    Lines.Add('');

    Lines.Add('# Defaults');
    Lines.Add('NEXO_AGENT_DEFAULT_WAREHOUSE=' + PageWarehouse.Values[0]);
    Lines.Add('NEXO_AGENT_DEFAULT_BRANCH=' + PageWarehouse.Values[1]);
    Lines.Add('');

    Lines.Add('# Cloud');
    Lines.Add('CLOUD_PLATFORM_URL=' + PageCloud.Values[0]);
    Lines.Add('CLOUD_API_KEY=' + PageCloud.Values[1]);
    Lines.Add('');

    Lines.Add('# Sync');
    Lines.Add('NEXO_AGENT_SYNC_INTERVAL_SECONDS=' + PageCloud.Values[2]);
    Lines.Add('NEXO_AGENT_HEARTBEAT_INTERVAL_SECONDS=' + PageCloud.Values[3]);
    Lines.Add('');

    Lines.Add('# Logging');
    Lines.Add('NEXO_AGENT_LOG_LEVEL=INFO');
    Lines.Add('');

    Lines.Add('# Offline queue');
    Lines.Add('NEXO_QUEUE_DB=' + ExpandConstant('{app}') + '\data\nexo_agent_queue.db');

    Lines.SaveToFile(ExpandConstant('{app}') + '\.env');
  finally
    Lines.Free;
  end;
end;

// ---- Post-install actions ----

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  DataDir: String;
  LogsDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Create data and logs directories
    DataDir := ExpandConstant('{app}') + '\data';
    LogsDir := ExpandConstant('{app}') + '\logs';
    ForceDirectories(DataDir);
    ForceDirectories(LogsDir);

    // Generate .env file from wizard inputs
    GenerateEnvFile;

    // Install Python dependencies
    WizardForm.StatusLabel.Caption := 'Instalowanie zależności Python...';
    Exec('cmd.exe',
      '/c cd /d "' + ExpandConstant('{app}') + '" && python -m pip install --no-cache-dir -r requirements.txt',
      '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

    // Install as Windows Service if selected
    if PageService.SelectedValueIndex = 0 then
    begin
      WizardForm.StatusLabel.Caption := 'Instalowanie usługi Windows...';
      Exec('cmd.exe',
        '/c cd /d "' + ExpandConstant('{app}') + '\service" && nexo-agent-service.exe install',
        '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

      // Start the service
      WizardForm.StatusLabel.Caption := 'Uruchamianie usługi...';
      Exec('cmd.exe',
        '/c net start PinquarkNexoAgent',
        '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;

// ---- Uninstall ----

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Stop and uninstall service
    Exec('cmd.exe', '/c net stop PinquarkNexoAgent', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('cmd.exe',
      '/c cd /d "' + ExpandConstant('{app}') + '\service" && nexo-agent-service.exe uninstall',
      '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

[Run]
Filename: "http://localhost:8000/docs"; Description: "Otwórz dokumentację API (Swagger UI)"; Flags: postinstall shellexec nowait skipifsilent unchecked
Filename: "{app}\{#AppExeName}"; Description: "Uruchom agenta teraz"; Flags: postinstall nowait skipifsilent unchecked
