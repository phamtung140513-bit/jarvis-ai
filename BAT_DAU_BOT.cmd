@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-services.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0watch-services.ps1"
echo Bot + Pay + Watchdog started. Close this window is OK.
pause
