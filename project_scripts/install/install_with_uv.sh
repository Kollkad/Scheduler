#!/bin/bash

# Установка Планировщика (Linux, SBEROSC) с использованием uv
# Скрипт должен лежать в одной папке с .env

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "===== УСТАНОВКА Планировщика (Linux, SBEROSC, uv) ====="
echo

# Загрузка .env
if [ ! -f ".env" ]; then
    echo "Файл .env не найден!"
    exit 1
fi
set -a
source .env
set +a

# Проверка обязательных переменных
: "${SBEROSC_TOKEN:?Не задан SBEROSC_TOKEN}"
: "${SBEROSC_URL:?Не задан SBEROSC_URL}"
: "${GITHUB_TAG:?Не задан GITHUB_TAG}"
GITHUB_ORG="${GITHUB_ORG:-Kollkad}"
GITHUB_PROJECT="${GITHUB_PROJECT:-Scheduler}"
GITHUB_FILE="${GITHUB_FILE:-Scheduler.zip}"

# Определение целевой директории
REAL_USER="${USER:-$(whoami)}"
INSTALL_DIR="/home/work/${REAL_USER}/ShedulerDir"
mkdir -p "$INSTALL_DIR"

echo "[1/4] Загрузка архива с SBEROSC..."

# Формирование URL (токен в URL)
DOWNLOAD_URL="https://token:${SBEROSC_TOKEN}@${SBEROSC_URL}/repo/extras/github_api/${GITHUB_ORG}/${GITHUB_PROJECT}/releases/download/${GITHUB_TAG}/${GITHUB_FILE}"

TEMP_DIR="/tmp/SchedulerUpdate"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

curl -k -L -o Scheduler.zip "$DOWNLOAD_URL" || { echo "Ошибка скачивания"; exit 1; }

echo "Распаковка..."
unzip -q Scheduler.zip
rm Scheduler.zip

# Имя распакованной папки (обычно Scheduler или Scheduler-main)
EXTRACTED=$(find . -maxdepth 1 -type d ! -name '.' | head -1 | sed 's|^\./||')

CODE_DIR="$INSTALL_DIR/Scheduler"
rm -rf "$CODE_DIR"
mkdir -p "$CODE_DIR"

echo "Копирование файлов в $CODE_DIR"
cp -r "$EXTRACTED"/* "$CODE_DIR"/

cd "$SCRIPT_DIR"
rm -rf "$TEMP_DIR"

echo
echo "[2/4] Установка и настройка uv..."

# Устанавливается uv, если ещё не установлен
if ! command -v uv &> /dev/null; then
    echo "uv не найден, устанавливаю..."
    PIP_INDEX="https://token:${SBEROSC_TOKEN}@${SBEROSC_URL}/repo/pypi/simple"
    python3 -m pip install uv -U --index-url "$PIP_INDEX" --trusted-host "$SBEROSC_URL"
    export PATH="$HOME/.local/bin:$PATH"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
else
    echo "uv уже установлен"
fi

# Создание конфигурации uv
mkdir -p "$HOME/.config/uv"
cat > "$HOME/.config/uv/uv.toml" <<EOF
python-install-mirror = "https://token:${SBEROSC_TOKEN}@${SBEROSC_URL}/repo/extras/github_api/astral-sh/python-build-standalone/releases/download/"
allow-insecure-host = ["https://${SBEROSC_URL}"]
[[index]]
url = "https://token:${SBEROSC_TOKEN}@${SBEROSC_URL}/repo/pypi/simple"
default = true
verify_ssl = false
authenticate = "always"
name = "sberosc"
EOF

echo "Устанавливаю Python 3.11.9 через uv..."
uv python install 3.11.9

echo
echo "[3/4] Создание виртуального окружения через uv..."

VENV_DIR="$INSTALL_DIR/venv"
uv venv --python 3.11 "$VENV_DIR"

# Активация для текущей сессии (чтобы дальше использовать uv pip)
source "$VENV_DIR/bin/activate"

echo
echo "[4/4] Установка зависимостей через uv..."

if [ -f "$CODE_DIR/backend/requirements.txt" ]; then
    echo "Установка из requirements.txt..."
    uv pip install -r "$CODE_DIR/backend/requirements.txt"
    echo "Зависимости установлены"
else
    echo "Файл backend/requirements.txt не найден, пропускаем"
fi

echo
echo "Создание скриптов запуска/остановки..."

# Скрипт запуска
LAUNCHER="$SCRIPT_DIR/Запуск_Планировщика.sh"
cat > "$LAUNCHER" <<EOF
#!/bin/bash
cd "$CODE_DIR/backend"
source "$VENV_DIR/bin/activate"
nohup python app/main.py > /dev/null 2>&1 &
sleep 3
xdg-open http://127.0.0.1:8000
EOF
chmod +x "$LAUNCHER"

# Скрипт остановки
STOPPER="$SCRIPT_DIR/Остановка_Планировщика.sh"
cat > "$STOPPER" <<EOF
#!/bin/bash
echo "Останавливаем Планировщик..."
pkill -f "python.*app/main.py"
echo "Готово"
EOF
chmod +x "$STOPPER"

echo
echo "===== УСТАНОВКА ЗАВЕРШЕНА ====="
echo
echo "Скрипты запуска/остановки:"
echo "  $LAUNCHER"
echo "  $STOPPER"
echo
echo "Проект установлен в: $CODE_DIR"
echo "Виртуальное окружение: $VENV_DIR"
echo
echo "Для первого запуска выполните:"
echo "  $LAUNCHER"