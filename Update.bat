@echo off
cd /d "%~dp0"
echo ============================================================
echo   3psLCCA Updater
echo ============================================================
echo.

:: ── Check Python ─────────────────────────────────────────────
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Please install Python and add it to PATH.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v
echo.

:: ── Check Git ─────────────────────────────────────────────────
git --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git not found. Please install Git and add it to PATH.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('git --version 2^>^&1') do echo [OK] %%v
echo.

:: ── Restore local changes ─────────────────────────────────────
echo Restoring local files...
git restore .
if %ERRORLEVEL% neq 0 (
    echo [ERROR] git restore failed. Cannot continue.
    echo.
    pause
    exit /b 1
)
echo [OK] Local files restored.
echo.

:: ── Pull latest ───────────────────────────────────────────────
echo Pulling latest updates...
echo.
git pull
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Update failed. Check your internet connection or repository access.
    echo.
    pause
    exit /b 1
)
echo.
echo ============================================================
echo   Update successful. 3psLCCA is up to date.
echo ============================================================
echo.
pause
