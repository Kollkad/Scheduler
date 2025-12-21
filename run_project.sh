#!/bin/bash

# Получаем путь к корню проекта (папка, где лежит скрипт)
ROOT="$(dirname "$0")"

echo "ROOT: $ROOT"

# --- Фронтенд ---
if [ -d "$ROOT/frontend" ]; then
    echo "[OK] Папка фронтенда найдена: $ROOT/frontend"
    gnome-terminal -- bash -c "cd '$ROOT/frontend' && npm run dev; exec bash"
else
    echo "[ERROR] Папка фронтенда НЕ найдена: $ROOT/frontend"
fi

# --- Бэкенд ---
if [ -d "$ROOT/backend/app" ]; then
    echo "[OK] Папка бэкенда найдена: $ROOT/backend/app"
    gnome-terminal -- bash -c "cd '$ROOT' && python3 -m backend.app.main; exec bash"
else
    echo "[ERROR] Папка бэкенда НЕ найдена: $ROOT/backend/app"
fi

echo "Проверка завершена."
