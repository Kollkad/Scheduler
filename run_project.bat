@echo off
REM --- Получаем путь к папке с батником (корень проекта) ---
set ROOT=%~dp0

echo ROOT: %ROOT%

REM --- Проверка фронтенда ---
if exist "%ROOT%frontend" (
    echo [OK] Папка фронтенда найдена: %ROOT%frontend
    start cmd /k "cd /d "%ROOT%frontend" && npm run dev"
) else (
    echo [ERROR] Папка фронтенда НЕ найдена: %ROOT%frontend
)

REM --- Проверка бэкенда ---
if exist "%ROOT%backend\app" (
    echo [OK] Папка бэкенда найдена: %ROOT%backend\app
    REM Запуск Python модуля из корня проекта
    start cmd /k "cd /d "%ROOT%" && python -m backend.app.main"
) else (
    echo [ERROR] Папка бэкенда НЕ найдена: %ROOT%backend\app
)

echo Проверка завершена.
pause
