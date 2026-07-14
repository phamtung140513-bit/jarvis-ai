@echo off
chcp 65001 >nul
title Cloudflare Tunnel - Jarvis 7860
cd /d "%~dp0"

where cloudflared >nul 2>&1
if errorlevel 1 (
  echo Chua cai cloudflared.
  echo Cai: winget install --id Cloudflare.cloudflared
  echo Hoac tai: https://github.com/cloudflare/cloudflared/releases
  pause
  exit /b 1
)

echo ============================================
echo  Tunnel free: public URL -^> http://127.0.0.1:7860
echo  1^) Dam bao CHAY_SERVER.bat dang mo
echo  2^) Copy URL https://....trycloudflare.com o duoi
echo  3^) Dan vao j-panel / config.json apiBase
echo  4^) User mo GitHub Pages de chat
echo ============================================
echo.
cloudflared tunnel --url http://127.0.0.1:7860
pause
