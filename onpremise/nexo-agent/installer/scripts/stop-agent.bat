@echo off
echo Zatrzymywanie Pinquark Nexo Agent...

:: Stop the service if running
net stop PinquarkNexoAgent 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Usluga PinquarkNexoAgent zatrzymana.
) else (
    echo Usluga nie jest uruchomiona lub nie jest zainstalowana.
    echo Probuje zatrzymac proces uvicorn...
    taskkill /f /im uvicorn.exe 2>nul
    taskkill /f /im python.exe /fi "WINDOWTITLE eq Pinquark Nexo Agent" 2>nul
)

echo Gotowe.
pause
