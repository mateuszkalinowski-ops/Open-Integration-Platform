<#
.SYNOPSIS
    Tests the connection to the running Pinquark Nexo Agent.

.DESCRIPTION
    Verifies the agent is running by hitting health, readiness, and
    connection status endpoints. Useful after installation.

.PARAMETER BaseUrl
    The base URL of the agent. Default: http://localhost:8000

.EXAMPLE
    .\test-connection.ps1
    .\test-connection.ps1 -BaseUrl "http://localhost:8000"
#>

param(
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Test połączenia — Pinquark Nexo Agent" -ForegroundColor Cyan
Write-Host "  $BaseUrl" -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int[]]$ExpectedCodes = @(200)
    )

    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        $stopwatch.Stop()
        $ms = $stopwatch.ElapsedMilliseconds

        if ($ExpectedCodes -contains $response.StatusCode) {
            Write-Host "  [OK]   $Name (${ms}ms)" -ForegroundColor Green
            try {
                $json = $response.Content | ConvertFrom-Json
                $json.PSObject.Properties | ForEach-Object {
                    if ($_.Name -ne "checks") {
                        Write-Host "         $($_.Name): $($_.Value)" -ForegroundColor Gray
                    }
                }
            } catch {}
            return $true
        } else {
            Write-Host "  [FAIL] $Name — HTTP $($response.StatusCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  [FAIL] $Name — $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test 1: Health
if (-not (Test-Endpoint "Health check" "$BaseUrl/health")) { $allPassed = $false }

# Test 2: Readiness
if (-not (Test-Endpoint "Readiness check" "$BaseUrl/readiness" @(200, 503))) { $allPassed = $false }

# Test 3: Connection status
if (-not (Test-Endpoint "Nexo connection" "$BaseUrl/connection/status")) { $allPassed = $false }

# Test 4: Swagger docs
if (-not (Test-Endpoint "API docs (Swagger)" "$BaseUrl/docs")) { $allPassed = $false }

# Test 5: Contractors list
if (-not (Test-Endpoint "Lista kontrahentów" "$BaseUrl/contractors?page=1&page_size=1" @(200, 503))) { $allPassed = $false }

# Test 6: Products list
if (-not (Test-Endpoint "Lista produktów" "$BaseUrl/products?page=1&page_size=1" @(200, 503))) { $allPassed = $false }

# Test 7: Stock levels
if (-not (Test-Endpoint "Stany magazynowe" "$BaseUrl/stock?page_size=1" @(200, 503))) { $allPassed = $false }

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "  WYNIK: Wszystkie testy przeszły ✓" -ForegroundColor Green
} else {
    Write-Host "  WYNIK: Niektóre testy nie przeszły ✗" -ForegroundColor Red
    Write-Host "  Sprawdź logi w katalogu logs/" -ForegroundColor Yellow
}
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
