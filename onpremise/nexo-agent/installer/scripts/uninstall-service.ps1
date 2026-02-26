<#
.SYNOPSIS
    Stops and removes the Pinquark Nexo Agent Windows Service.

.EXAMPLE
    .\uninstall-service.ps1
#>

param(
    [string]$InstallDir = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = "Continue"

$serviceName = "PinquarkNexoAgent"
$serviceExe = Join-Path $InstallDir "service\nexo-agent-service.exe"

Write-Host ""
Write-Host "Odinstalowywanie usługi $serviceName..." -ForegroundColor Yellow
Write-Host ""

$svc = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if (-not $svc) {
    Write-Host "Usługa '$serviceName' nie jest zainstalowana." -ForegroundColor Gray
    exit 0
}

if ($svc.Status -eq "Running") {
    Write-Host "Zatrzymywanie usługi..."
    Stop-Service -Name $serviceName -Force
    Start-Sleep -Seconds 3
    Write-Host "  Zatrzymana." -ForegroundColor Green
}

if (Test-Path $serviceExe) {
    Push-Location (Split-Path $serviceExe)
    & $serviceExe uninstall
    Pop-Location
} else {
    sc.exe delete $serviceName
}

Start-Sleep -Seconds 2

$svc = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if (-not $svc) {
    Write-Host ""
    Write-Host "Usługa usunięta pomyślnie." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Usługa może wymagać restartu systemu do pełnego usunięcia." -ForegroundColor Yellow
}

Write-Host ""
