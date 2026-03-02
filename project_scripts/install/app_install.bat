@echo off
chcp 65001 > NUL
setlocal enabledelayedexpansion

:: Папка, где лежит скрипт
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ==== УСТАНОВКА Планировщика (SBEROSC) ====
echo.

:: ========== Загружаем .env ==========
if not exist ".env" (
    echo Файл .env не найден! Создайте его рядом с скриптом.
    pause
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"

:: ========== Проверка обязательных переменных ==========
if "%SBEROSC_TOKEN%"=="" (
    echo Ошибка: SBEROSC_TOKEN не задан в .env
    pause
    exit /b 1
)

if "%SBEROSC_URL%"=="" (
    echo Ошибка: SBEROSC_URL не задан в .env
    pause
    exit /b 1
)

if "%GITHUB_ORG%"=="" set "GITHUB_ORG=Kollkad"
if "%GITHUB_PROJECT%"=="" set "GITHUB_PROJECT=Scheduler"

if "%GITHUB_TAG%"=="" (
    echo Ошибка: GITHUB_TAG не задан в .env
    pause
    exit /b 1
)

if "%GITHUB_FILE%"=="" set "GITHUB_FILE=Scheduler.zip"

:: Если INSTALL_DIR не задан — используется папка по умолчанию
if "%INSTALL_DIR%"=="" set "INSTALL_DIR=C:\SchedulerTest"

:: Создание целевой папки, если её нет
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: ========== [1/4] Загрузка архива с SBEROSC ==========
echo [1/4] Загрузка архива с SBEROSC...

:: Формируется URL для скачивания
set "DOWNLOAD_URL=https://token:%SBEROSC_TOKEN%@%SBEROSC_URL%/repo/extras/github_api/%GITHUB_ORG%/%GITHUB_PROJECT%/releases/download/%GITHUB_TAG%/%GITHUB_FILE%"
echo Ссылка сформирована (токен скрыт)

:: Временная папка для скачивания
set "TEMP_DIR=%TEMP%\SchedulerUpdate"
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"
cd /d "%TEMP_DIR%"

:: Скачивание архива
curl -k -L -o Scheduler.zip "%DOWNLOAD_URL%"
if errorlevel 1 (
    echo Ошибка скачивания архива!
    echo Проверьте переменные и доступ к SBEROSC.
    pause
    exit /b 1
)

echo Распаковка...
powershell -Command "Expand-Archive -Path Scheduler.zip -DestinationPath . -Force"
del Scheduler.zip

:: Находится имя распакованной папки (обычно Scheduler или Scheduler-main)
for /d %%i in (*) do set "EXTRACTED=%%i"

:: Папка для кода внутри INSTALL_DIR
set "CODE_DIR=%INSTALL_DIR%\Scheduler"
if exist "%CODE_DIR%" rmdir /s /q "%CODE_DIR%"
mkdir "%CODE_DIR%"

:: Копирование содержимого распакованной папки в CODE_DIR
echo Копирование файлов в %CODE_DIR%...
xcopy "%EXTRACTED%" "%CODE_DIR%" /E /Y /Q >nul

:: чистка временных
cd /d "%SCRIPT_DIR%"
rmdir /s /q "%TEMP_DIR%" 2>nul

echo.

:: ========== [2/4] Проверка Python ==========
echo [2/4] Проверка Python...

:: Определяет, какой Python использовать
if "%PYTHON_PATH%" == "" (
    set PYTHON=python
) else (
    set PYTHON=%PYTHON_PATH%
)

:: Проверяется, доступен ли Python
echo Используется:
%PYTHON% --version

echo.

:: ========== [3/4] Виртуальное окружение ==========
echo [3/4] Виртуальное окружение...

set "VENV_DIR=%INSTALL_DIR%\venv"
if not exist "%VENV_DIR%" (
    echo Создание нового venv в %VENV_DIR%
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Ошибка создания виртуального окружения!
        pause
        exit /b 1
    )
) else (
    echo Виртуальное окружение уже существует.
)

:: Активируется и обновляется pip
call "%VENV_DIR%\Scripts\activate.bat"

echo.

:: ========== [4/4] Установка зависимостей через внутренний PyPI ==========
echo [4/4] Установка зависимостей через внутренний PyPI...

if exist "%CODE_DIR%\backend\requirements.txt" (
    echo Установка из requirements.txt с использованием SBEROSC-индекса...

    :: URL для pip с токеном
    set "PIP_INDEX_URL=https://token:%SBEROSC_TOKEN%@%SBEROSC_URL%/repo/pypi/simple"

    :: Устанавливаются зависимости
    pip install -r "%CODE_DIR%\backend\requirements.txt" --index-url "%PIP_INDEX_URL%" --trusted-host "%SBEROSC_URL%" --break-system-packages

    if errorlevel 1 (
        echo Предупреждение: не все зависимости установились.
        echo Проверьте файл requirements.txt, токен и доступ к SBEROSC.
    ) else (
        echo Зависимости успешно установлены.
    )
) else (
    echo Файл backend\requirements.txt не найден, пропускаем установку.
)

echo.

:: ========== Создание скриптов запуска/остановки ==========
echo Создание скриптов запуска/остановки...

:: Скрипт ЗАПУСКА
set "LAUNCHER=%SCRIPT_DIR%Запуск Планировщика.bat"
(
    echo @echo off
    echo cd /d "%CODE_DIR%\backend"
    echo start /B "" "%VENV_DIR%\Scripts\python.exe" app\main.py
    echo timeout /t 3 /nobreak ^>nul
    echo start http://127.0.0.1:8000
    echo exit
) > "%LAUNCHER%"

:: Скрипт ОСТАНОВКИ
set "STOPPER=%SCRIPT_DIR%Остановка Планировщика.bat"
(
    echo @echo off
    echo echo Останавливаем Планировщик...
    echo taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq Scheduler" 2^>nul
    echo echo Готово
    echo pause
) > "%STOPPER%"

echo.
echo ==== УСТАНОВКА ЗАВЕРШЕНА ====
echo.
echo Скрипты запуска и остановки созданы в папке:
echo %SCRIPT_DIR%
echo.
echo Проект установлен в: %CODE_DIR%
echo Виртуальное окружение: %VENV_DIR%
echo.
echo Для первого запуска нажмите любую клавишу...
pause >nul

:: Запуск приложения
call "%LAUNCHER%"

endlocal