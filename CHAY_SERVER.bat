@echo off
chcp 65001 >nul
title TUNGDEVAI WEB - DUNG TAT CUA SO NAY
cd /d "%~dp0"
echo ============================================
echo   TUNGDEVAI WEB SERVER
echo ============================================
echo.
echo   Chat:  http://127.0.0.1:7860/
echo   Admin: http://127.0.0.1:7860/j-panel.html
echo   Key:   jarvis-admin-change-me
echo.
echo   *** DE CUA SO NAY MO - neu tat la web chet ***
echo ============================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo LOI: thieu .venv
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m webapp.server
echo.
echo Server da dung.
pause
