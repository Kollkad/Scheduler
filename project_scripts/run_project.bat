@echo off
REM --- Get the script directory and project root ---
set SCRIPT_DIR=%~dp0
set ROOT=%SCRIPT_DIR%..

echo ROOT: %ROOT%

REM --- Frontend check ---
if exist "%ROOT%\frontend" (
    echo [OK] Frontend folder found: %ROOT%\frontend
    start cmd /k "cd /d "%ROOT%\frontend" && npm run dev"
) else (
    echo [ERROR] Frontend folder NOT found: %ROOT%\frontend
)

REM --- Backend check ---
if exist "%ROOT%\backend\app" (
    echo [OK] Backend folder found: %ROOT%\backend\app
    start cmd /k "cd /d "%ROOT%" && python -m backend.app.main"
) else (
    echo [ERROR] Backend folder NOT found: %ROOT%\backend\app
)

echo Check complete.
pause