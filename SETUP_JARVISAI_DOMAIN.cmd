@echo off
chcp 65001 >nul
set PATH=C:\Program Files\GitHub CLI;C:\Program Files\Git\bin;%PATH%
cd /d "%~dp0"

set ORG=jarvisai-tung
set REPO=jarvisai-tung.github.io
set SITE=https://jarvisai-tung.github.io/

echo =====================================================
echo   SETUP FREE DOMAIN: %SITE%
echo   Org/User: %ORG%
echo   Repo:     %REPO%
echo =====================================================
echo.
echo Buoc 1: Xac nhan org/user "%ORG%" da co
echo   https://github.com/%ORG%
start "" "https://github.com/%ORG%"
echo.
echo Neu CHUA co repo %REPO%, se mo trang tao repo.
echo   Ten repo PHAI DUNG: %REPO%
echo   Public, KHONG tick README
echo.
start "" "https://github.com/organizations/%ORG%/repositories/new"
start "" "https://github.com/new?name=%REPO%&owner=%ORG%"
echo Nhan phim bat ky sau khi repo %REPO% da duoc tao (hoac da co)...
pause

echo.
echo Buoc 2: Dang nhap GitHub CLI...
gh auth status >nul 2>&1
if errorlevel 1 (
  gh auth login -h github.com -p https -w
)

echo.
echo Buoc 3: Tao repo neu chua co...
gh repo view %ORG%/%REPO% >nul 2>&1
if errorlevel 1 (
  gh repo create %ORG%/%REPO% --public --description "Jarvis AI free site"
)

echo.
echo Buoc 4: Push code...
git remote remove origin-org 2>nul
git remote add origin-org https://github.com/%ORG%/%REPO%.git
git branch -M main
git push -u origin-org main
if errorlevel 1 (
  echo.
  echo *** PUSH LOI ***
  echo Thu: gh auth login  roi chay lai file nay.
  pause
  exit /b 1
)

echo.
echo Buoc 5: Bat GitHub Pages
echo   1. https://github.com/%ORG%/%REPO%/settings/pages
echo   2. Source = Deploy from a branch
echo   3. Branch = main , Folder = /docs
echo   4. Save
echo.
start "" "https://github.com/%ORG%/%REPO%/settings/pages"
echo.
echo =====================================================
echo   SAU 1-2 PHUT MO:
echo   %SITE%
echo   %SITE%landing.html
echo =====================================================
start "" "%SITE%"
pause
