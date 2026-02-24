#!/usr/bin/env python3
"""
releasePreparer.py
Скрипт для подготовки релизной сборки проекта.
- Собирает фронтенд (npm run build)
- Копирует backend и собранный фронтенд во временную папку
- Восстанавливает исходное состояние frontend (удаляет папку dist)
- Создаёт архив с релизом
- Очищает временные файлы
"""

import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# ---- Конфигурация ----
PROJECT_ROOT = Path(__file__).parent.parent          # корень проекта (scheduler)
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
SCRIPTS_DIR = PROJECT_ROOT / "project_scripts"

# Папка для временной сборки
RELEASE_TEMP = SCRIPTS_DIR / "release_temp"
# Папка для готовых архивов (можно создать рядом со скриптом)
RELEASES_DIR = SCRIPTS_DIR / "releases"
RELEASES_DIR.mkdir(exist_ok=True)

# Имя архива с меткой времени
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
ARCHIVE_NAME = f"release_{TIMESTAMP}.zip"
ARCHIVE_PATH = RELEASES_DIR / ARCHIVE_NAME

# Исключаемые папки при копировании backend (чтобы не тащить мусор)
BACKEND_IGNORE = {
    "__pycache__", "venv", ".venv", ".git", ".idea", ".vscode",
    "*.pyc", "__pycache__", ".pytest_cache", ".mypy_cache"
}

def ignore_backend(src, names):
    """Функция игнорирования для shutil.copytree (backend)"""
    ignored = set()
    for name in names:
        if name in BACKEND_IGNORE or name.endswith(('.pyc', '.pyo', '.pyd')):
            ignored.add(name)
    return ignored

def main():
    print("=== Начинаем подготовку релиза ===")

    # 1. Проверяем наличие фронтенда
    if not FRONTEND_DIR.exists():
        print("❌ Папка frontend не найдена", file=sys.stderr)
        sys.exit(1)

    # 2. Сборка фронтенда
    print("🏗️  Запускаем npm run build во frontend...")
    try:
        # Проверяем доступность npm (опционально)
        # Запускаем с shell=True для Windows
        result = subprocess.run(
            "npm run build",
            cwd=str(FRONTEND_DIR),
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Сборка фронтенда выполнена")
    except subprocess.CalledProcessError as e:
        print("❌ Ошибка сборки фронтенда:", e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Не удалось найти npm. Убедитесь, что Node.js установлен и npm доступен в командной строке.",
              file=sys.stderr)
        sys.exit(1)

    # 3. Определяем путь к собранным файлам
    BUILD_PATH = FRONTEND_DIR / "dist" / "spa"
    if not BUILD_PATH.exists():
        # Если по какой-то причине папка dist/spa не создалась, пробуем dist
        BUILD_PATH = FRONTEND_DIR / "dist"
        if not BUILD_PATH.exists():
            print("❌ Не найдена папка со сборкой (dist/spa)", file=sys.stderr)
            sys.exit(1)

    print(f"📦 Сборка находится в {BUILD_PATH}")

    # 4. Создаём временную структуру релиза
    print("📁 Создаём временную папку для релиза...")
    if RELEASE_TEMP.exists():
        shutil.rmtree(RELEASE_TEMP)
    RELEASE_TEMP.mkdir()

    # 5. Копируем backend (с игнорированием мусора)
    print("📂 Копируем backend...")
    dest_backend = RELEASE_TEMP / "backend"
    shutil.copytree(BACKEND_DIR, dest_backend, ignore=ignore_backend)

    # 6. Копируем собранный фронтенд в структуру frontend/dist/spa
    print("📂 Копируем собранный фронтенд...")
    dest_frontend_dist_spa = RELEASE_TEMP / "frontend" / "dist" / "spa"
    dest_frontend_dist_spa.mkdir(parents=True, exist_ok=True)

    # Копируем содержимое BUILD_PATH (сами файлы) в dest_frontend_dist_spa
    for item in BUILD_PATH.iterdir():
        if item.is_file():
            shutil.copy2(item, dest_frontend_dist_spa / item.name)
        elif item.is_dir():
            shutil.copytree(item, dest_frontend_dist_spa / item.name)

    # 7. Возвращаем исходный фронтенд в чистое состояние (удаляем dist)
    print("🧹 Очищаем исходную папку frontend от build...")
    dist_to_remove = FRONTEND_DIR / "dist"
    if dist_to_remove.exists():
        shutil.rmtree(dist_to_remove)
        print("✅ Папка dist удалена из исходного frontend")

    # 8. Создаём архив
    print("🗜️  Создаём архив...")
    with zipfile.ZipFile(ARCHIVE_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(RELEASE_TEMP):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(RELEASE_TEMP)
                zipf.write(file_path, arcname)

    print(f"✅ Архив создан: {ARCHIVE_PATH}")

    # 9. Удаляем временную папку
    print("🧹 Удаляем временную папку...")
    shutil.rmtree(RELEASE_TEMP)

    print("=== Готово! ===")

if __name__ == "__main__":
    main()