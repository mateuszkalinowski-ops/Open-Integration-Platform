<#
.SYNOPSIS
    Interactive configuration wizard for Pinquark Nexo Agent (CLI version).

.DESCRIPTION
    Generates the .env configuration file through interactive prompts.
    Use this script if you need to reconfigure the agent after installation,
    or as an alternative to the GUI installer wizard.

.EXAMPLE
    .\configure-agent.ps1
    .\configure-agent.ps1 -OutputPath "C:\Program Files\Pinquark\NexoAgent\.env"
#>

param(
    [string]$OutputPath = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) ".env")
)

function Read-SecureInput {
    param([string]$Prompt)
    $secure = Read-Host -Prompt $Prompt -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    return [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
}

function Read-WithDefault {
    param([string]$Prompt, [string]$Default)
    $input = Read-Host -Prompt "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($input)) { return $Default }
    return $input
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Pinquark Nexo Agent — Konfiguracja" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- Agent ID ---
Write-Host "1/6 Identyfikacja agenta" -ForegroundColor Yellow
Write-Host "---"
$agentId = Read-WithDefault "  ID agenta" "nexo-agent-001"
Write-Host ""

# --- SQL Server ---
Write-Host "2/6 Połączenie z SQL Server" -ForegroundColor Yellow
Write-Host "---"
$sqlServer = Read-WithDefault "  Serwer SQL" "(local)\INSERTNEXO"
$sqlDatabase = Read-WithDefault "  Nazwa bazy danych" "Nexo_demo"
$sqlAuth = Read-WithDefault "  Uwierzytelnianie Windows (t/n)" "t"

$sqlAuthWindows = "true"
$sqlUsername = ""
$sqlPassword = ""

if ($sqlAuth -eq "n") {
    $sqlAuthWindows = "false"
    $sqlUsername = Read-Host "  Login SQL"
    $sqlPassword = Read-SecureInput "  Hasło SQL"
}
Write-Host ""

# --- Nexo Operator ---
Write-Host "3/6 Operator InsERT Nexo" -ForegroundColor Yellow
Write-Host "---"
$nexoLogin = Read-WithDefault "  Login operatora" "Admin"
$nexoPassword = Read-SecureInput "  Hasło operatora"
$nexoProduct = Read-WithDefault "  Moduł (Subiekt/Rachmistrz/Rewizor)" "Subiekt"
Write-Host ""

# --- SDK Path ---
Write-Host "4/6 Ścieżka do SDK" -ForegroundColor Yellow
Write-Host "---"
$sdkPath = Read-WithDefault "  Katalog Bin SDK" "C:\nexoSDK\Bin"

$requiredDll = Join-Path $sdkPath "InsERT.Moria.API.dll"
if (-not (Test-Path $requiredDll)) {
    Write-Host "  [UWAGA] Nie znaleziono InsERT.Moria.API.dll w $sdkPath" -ForegroundColor Yellow
}
Write-Host ""

# --- Warehouse ---
Write-Host "5/6 Domyślny magazyn i oddział" -ForegroundColor Yellow
Write-Host "---"
$warehouse = Read-WithDefault "  Symbol magazynu" "MAG"
$branch = Read-WithDefault "  Symbol oddziału" "CENTRALA"
Write-Host ""

# --- Cloud ---
Write-Host "6/6 Połączenie z Pinquark Cloud (opcjonalne)" -ForegroundColor Yellow
Write-Host "---"
$cloudUrl = Read-WithDefault "  URL platformy" "https://integrations.pinquark.com"
$cloudKey = Read-Host "  Klucz API (puste = brak)"
$syncInterval = Read-WithDefault "  Interwał sync (s)" "300"
$heartbeatInterval = Read-WithDefault "  Interwał heartbeat (s)" "60"
Write-Host ""

# --- Generate .env ---
Write-Host "Generowanie pliku konfiguracyjnego..." -ForegroundColor Yellow

$envContent = @"
# Pinquark Nexo Agent — configuration
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Agent
NEXO_AGENT_ID=$agentId

# SQL Server
NEXO_SQL_SERVER=$sqlServer
NEXO_SQL_DATABASE=$sqlDatabase
NEXO_SQL_AUTH_WINDOWS=$sqlAuthWindows
$(if ($sqlAuthWindows -eq "false") { "NEXO_SQL_USERNAME=$sqlUsername`nNEXO_SQL_PASSWORD=$sqlPassword" })

# Nexo operator
NEXO_OPERATOR_LOGIN=$nexoLogin
NEXO_OPERATOR_PASSWORD=$nexoPassword
NEXO_PRODUCT=$nexoProduct

# SDK
NEXO_SDK_BIN_PATH=$sdkPath

# Defaults
NEXO_AGENT_DEFAULT_WAREHOUSE=$warehouse
NEXO_AGENT_DEFAULT_BRANCH=$branch

# Cloud
CLOUD_PLATFORM_URL=$cloudUrl
CLOUD_API_KEY=$cloudKey

# Sync
NEXO_AGENT_SYNC_INTERVAL_SECONDS=$syncInterval
NEXO_AGENT_HEARTBEAT_INTERVAL_SECONDS=$heartbeatInterval

# Logging
NEXO_AGENT_LOG_LEVEL=INFO
"@

$envContent | Out-File -FilePath $OutputPath -Encoding utf8 -Force

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Konfiguracja zapisana: $OutputPath" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Następne kroki:" -ForegroundColor Cyan
Write-Host "  1. .\install-service.ps1   — zainstaluj jako usługę Windows" -ForegroundColor White
Write-Host "  2. start-agent.bat          — lub uruchom ręcznie" -ForegroundColor White
Write-Host ""
