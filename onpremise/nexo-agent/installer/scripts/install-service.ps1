<#
.SYNOPSIS
    Installs the Pinquark Nexo Agent as a Windows Service.

.DESCRIPTION
    Uses WinSW to wrap the Python/FastAPI agent as a native Windows Service
    that starts automatically with the system.

.PARAMETER InstallDir
    The directory where the agent is installed.

.EXAMPLE
    .\install-service.ps1
    .\install-service.ps1 -InstallDir "C:\Program Files\Pinquark\NexoAgent"
#>

param(
    [string]$InstallDir = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = "Stop"

$serviceName = "PinquarkNexoAgent"
$serviceDir = Join-Path $InstallDir "service"
$serviceExe = Join-Path $serviceDir "nexo-agent-service.exe"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Instalacja usługi Pinquark Nexo Agent" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Katalog instalacji: $InstallDir"
Write-Host "Usługa: $serviceName"
Write-Host ""

# Verify WinSW exists
if (-not (Test-Path $serviceExe)) {
    Write-Host "[BLAD] Nie znaleziono pliku usługi: $serviceExe" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pobierz WinSW z: https://github.com/winsw/winsw/releases" -ForegroundColor Yellow
    Write-Host "Zapisz jako: $serviceExe" -ForegroundColor Yellow
    exit 1
}

# Check if service already exists
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Usługa '$serviceName' już istnieje (status: $($existingService.Status))" -ForegroundColor Yellow
    $response = Read-Host "Przeinstalować? (t/n)"
    if ($response -ne "t") {
        Write-Host "Anulowano." -ForegroundColor Yellow
        exit 0
    }

    Write-Host "Zatrzymywanie istniejącej usługi..."
    if ($existingService.Status -eq "Running") {
        Stop-Service -Name $serviceName -Force
        Start-Sleep -Seconds 3
    }
    Write-Host "Usuwanie istniejącej usługi..."
    & $serviceExe uninstall 2>$null
    Start-Sleep -Seconds 2
}

# Verify .env exists
$envFile = Join-Path $InstallDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "[UWAGA] Brak pliku .env — uruchom konfigurator lub skopiuj .env.example" -ForegroundColor Yellow
}

# Verify Python dependencies
Write-Host "Sprawdzanie zależności Python..."
$reqFile = Join-Path $InstallDir "requirements.txt"
if (Test-Path $reqFile) {
    & python -m pip install --quiet --no-cache-dir -r $reqFile
    Write-Host "  Zależności zainstalowane." -ForegroundColor Green
}

# Install service
Write-Host ""
Write-Host "Instalowanie usługi Windows..."
Push-Location $serviceDir
try {
    & $serviceExe install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[BLAD] Nie udało się zainstalować usługi." -ForegroundColor Red
        exit 1
    }
    Write-Host "  Usługa zainstalowana." -ForegroundColor Green
} finally {
    Pop-Location
}

# Start service
Write-Host "Uruchamianie usługi..."
Start-Service -Name $serviceName
Start-Sleep -Seconds 5

$svc = Get-Service -Name $serviceName
if ($svc.Status -eq "Running") {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Usługa uruchomiona pomyślnie!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  API:           http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  Swagger UI:    http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  Health check:  http://localhost:8000/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Zarządzanie:   sc stop $serviceName" -ForegroundColor Gray
    Write-Host "                 sc start $serviceName" -ForegroundColor Gray
    Write-Host "                 sc query $serviceName" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "[UWAGA] Usługa nie uruchomiła się automatycznie." -ForegroundColor Yellow
    Write-Host "Sprawdź logi: $InstallDir\logs\" -ForegroundColor Yellow
}

Write-Host ""
