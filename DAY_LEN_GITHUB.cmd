@echo off
chcp 65001 >nul
set PATH=C:\Program Files\GitHub CLI;C:\Program Files\Git\bin;%PATH%
cd /d "%~dp0"

echo ============================================
echo   TungDevAI - Day len GitHub Pages (free)
echo   User: phamtung140513-bit
echo   Repo: TungDevAI
echo ============================================
echo.

REM 1) Mo trang tao repo (neu chua co)
echo [1/4] Mo trinh duyet tao repo (neu can)...
start "" "https://github.com/new?name=tungdevai&description=TungDevAI+ChatGPT-style+web+%2B+Telegram+bot&visibility=public"
echo     - Owner: phamtung140513-bit
echo     - Name: TungDevAI
echo     - Public, KHONG tick README
echo     - Bam Create repository
echo.
pause

REM 2) Dang nhap GitHub
echo.
echo [2/4] Dang nhap GitHub CLI...
gh auth status >nul 2>&1
if errorlevel 1 (
  echo     Chua login - se mo trinh duyet...
  gh auth login -h github.com -p https -w
) else (
  echo     Da login.
)

REM 3) Tao repo neu chua co (bo qua neu da co)
echo.
echo [3/4] Tao / kiem tra repo...
gh repo view phamtung140513-bit/jarvis-ai >nul 2>&1
if errorlevel 1 (
  gh repo create TungDevAI --public --source=. --remote=origin --description "TungDevAI - ChatGPT-style web + Telegram bot"
  if errorlevel 1 (
    echo     Repo co the da co remote. Tiep tuc push...
  )
) else (
  echo     Repo da ton tai.
)

git remote remove origin 2>nul
git remote add origin https://github.com/phamtung140513-bit/jarvis-ai.git

REM 4) Push
echo.
echo [4/4] Push code...
git branch -M main
git push -u origin main
if errorlevel 1 (
  echo.
  echo *** PUSH LOI ***
  echo Thu: gh auth login  roi chay lai file nay.
  pause
  exit /b 1
)

echo.
echo ============================================
echo   XONG! Bat GitHub Pages:
echo   https://github.com/phamtung140513-bit/jarvis-ai/settings/pages
echo   Source = GitHub Actions
echo.
echo   Web chat se la:
echo   https://jarvisai-tung.github.io/
echo ============================================
start "" "https://github.com/phamtung140513-bit/jarvis-ai/settings/pages"
pause
