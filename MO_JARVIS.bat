@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] Mo server (cua so den - DUNG TAT)...
start "JARVIS-SERVER" cmd /k "%~dp0CHAY_SERVER.bat"

echo [2/3] Doi 5 giay...
timeout /t 5 /nobreak >nul

echo [3/3] Mo trinh duyet...
start http://127.0.0.1:7860/

echo.
echo Neu trang trang / loi:
echo   1. Xem cua so den JARVIS-SERVER co chu loi do khong
echo   2. Copy vao Edge: http://127.0.0.1:7860/
echo   3. Thu tat VPN
echo.
echo Admin (bi mat): http://127.0.0.1:7860/j-panel.html
echo.
pause
