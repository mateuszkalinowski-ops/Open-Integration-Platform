<#
.SYNOPSIS
    Checks all prerequisites for Pinquark Nexo Agent installation.

.DESCRIPTION
    Verifies: Python 3.12+, .NET 8.0 Runtime, InsERT Nexo SDK,
    SQL Server connectivity, and system requirements.

.EXAMPLE
    .\check-prerequisites.ps1
    .\check-prerequisites.ps1 -SdkPath "C:\nexoSDK\Bin" -SqlServer "(local)\INSERTNEXO"
#>

param(
    [string]$SdkPath = "C:\nexoSDK\Bin",
    [string]$SqlServer = "(local)\INSERTNEXO"
)

$ErrorActionPreference = "Continue"

function Write-Check {
    param([string]$Name, [bool]$Passed, [string]$Detail = "")
    if ($Passed) {
        Write-Host "  [OK]   $Name" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $Name" -ForegroundColor Red
    }
    if ($Detail) {
        Write-Host "         $Detail" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Pinquark Nexo Agent — Sprawdzanie wymagań" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# 1. OS check
Write-Host "System operacyjny:" -ForegroundColor Yellow
$os = Get-CimInstance Win32_OperatingSystem
$isWin10Plus = [System.Environment]::OSVersion.Version.Major -ge 10
Write-Check "Windows 10/11/Server 2019+" $isWin10Plus "$($os.Caption) ($($os.Version))"
$is64bit = [Environment]::Is64BitOperatingSystem
Write-Check "64-bit" $is64bit
if (-not $isWin10Plus -or -not $is64bit) { $allPassed = $false }

Write-Host ""

# 2. Python check
Write-Host "Python:" -ForegroundColor Yellow
try {
    $pyVersion = & python --version 2>&1
    $pyInstalled = $LASTEXITCODE -eq 0
    if ($pyVersion -match "Python (\d+)\.(\d+)") {
        $pyMajor = [int]$Matches[1]
        $pyMinor = [int]$Matches[2]
        $pyOk = ($pyMajor -ge 3) -and ($pyMinor -ge 12)
        Write-Check "Python 3.12+" $pyOk $pyVersion
        if (-not $pyOk) { $allPassed = $false }
    } else {
        Write-Check "Python 3.12+" $false "Nie można odczytać wersji"
        $allPassed = $false
    }
} catch {
    Write-Check "Python 3.12+" $false "Python nie jest zainstalowany. Pobierz z https://www.python.org/downloads/"
    $allPassed = $false
}

# pip check
try {
    $pipVersion = & python -m pip --version 2>&1
    Write-Check "pip" ($LASTEXITCODE -eq 0) $pipVersion
} catch {
    Write-Check "pip" $false
}

Write-Host ""

# 3. .NET Runtime check
Write-Host ".NET Runtime:" -ForegroundColor Yellow
try {
    $dotnetRuntimes = & dotnet --list-runtimes 2>&1
    $dotnetInstalled = $LASTEXITCODE -eq 0
    if ($dotnetInstalled) {
        $hasNet8 = $dotnetRuntimes | Where-Object { $_ -match "Microsoft\.NETCore\.App 8\." }
        Write-Check ".NET 8.0 Runtime" ([bool]$hasNet8) ($hasNet8 | Select-Object -First 1)
        if (-not $hasNet8) { $allPassed = $false }
    } else {
        Write-Check ".NET 8.0 Runtime" $false "dotnet CLI nie jest zainstalowany"
        $allPassed = $false
    }
} catch {
    Write-Check ".NET 8.0 Runtime" $false "Pobierz z https://dotnet.microsoft.com/download/dotnet/8.0"
    $allPassed = $false
}

Write-Host ""

# 4. InsERT Nexo SDK check
Write-Host "InsERT Nexo SDK:" -ForegroundColor Yellow
$requiredDlls = @(
    "InsERT.Moria.API.dll",
    "InsERT.Moria.ModelDanych.dll",
    "InsERT.Moria.Sfera.dll",
    "InsERT.Mox.Core.dll"
)
$sdkExists = Test-Path $SdkPath
Write-Check "Katalog SDK ($SdkPath)" $sdkExists

if ($sdkExists) {
    foreach ($dll in $requiredDlls) {
        $dllPath = Join-Path $SdkPath $dll
        $dllExists = Test-Path $dllPath
        Write-Check "  $dll" $dllExists
        if (-not $dllExists) { $allPassed = $false }
    }
} else {
    Write-Host "         Ustaw -SdkPath na prawidłową ścieżkę" -ForegroundColor Gray
    $allPassed = $false
}

Write-Host ""

# 5. SQL Server connectivity
Write-Host "SQL Server:" -ForegroundColor Yellow
try {
    $sqlCmd = "sqlcmd -S `"$SqlServer`" -Q `"SELECT 1`" -h -1 -W"
    $sqlResult = Invoke-Expression $sqlCmd 2>&1
    $sqlOk = $LASTEXITCODE -eq 0
    Write-Check "Połączenie z $SqlServer" $sqlOk
    if (-not $sqlOk) { $allPassed = $false }
} catch {
    Write-Check "Połączenie z $SqlServer" $false "sqlcmd niedostępny lub serwer nieosiągalny"
}

Write-Host ""

# 6. Port availability
Write-Host "Porty:" -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$portFree = -not $port8000
Write-Check "Port 8000 wolny" $portFree $(if (-not $portFree) { "Port 8000 jest zajęty przez inny proces" })
if (-not $portFree) { $allPassed = $false }

Write-Host ""

# 7. Disk space
Write-Host "Dysk:" -ForegroundColor Yellow
$drive = (Get-PSDrive -Name C)
$freeGB = [math]::Round($drive.Free / 1GB, 1)
$diskOk = $freeGB -gt 1
Write-Check "Wolne miejsce > 1 GB" $diskOk "${freeGB} GB wolne"
if (-not $diskOk) { $allPassed = $false }

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "  WYNIK: Wszystkie wymagania spełnione ✓" -ForegroundColor Green
} else {
    Write-Host "  WYNIK: Niektóre wymagania niespełnione ✗" -ForegroundColor Red
    Write-Host "  Zainstaluj brakujące komponenty i uruchom ponownie." -ForegroundColor Yellow
}
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
