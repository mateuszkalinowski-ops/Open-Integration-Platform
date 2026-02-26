@echo off
title Pinquark Nexo Agent
cd /d "%~dp0"

echo ============================================
echo   Pinquark Nexo Agent v1.0.0
echo   InsERT Nexo ERP Integration
echo ============================================
echo.

if not exist ".env" (
    echo [BLAD] Brak pliku konfiguracyjnego .env
    echo Uruchom instalator lub skopiuj .env.example do .env
    pause
    exit /b 1
)

echo Uruchamianie agenta...
echo API bedzie dostepne pod: http://localhost:8000
echo Dokumentacja Swagger UI:  http://localhost:8000/docs
echo.
echo Nacisnij Ctrl+C aby zatrzymac agenta.
echo.

python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

pause
