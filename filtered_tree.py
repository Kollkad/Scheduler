"""
Модуль для генерации фильтрованного дерева файловой структуры проекта.

Обеспечивает создание читаемого представления структуры проекта с исключением
системных файлов, кэшей, зависимостей и других нерелевантных элементов.
"""
import os
from pathlib import Path


def should_ignore(path, name):
    """
    Проверка необходимости игнорирования папки или файла при построении дерева.

    Args:
        path (str): Путь к текущей директории
        name (str): Имя проверяемого элемента

    Returns:
        bool: True если элемент нужно игнорировать, False если включать в дерево
    """
    ignore_patterns = [
        '.git', '.gitignore', '.gitattributes', '.github',
        '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
        'venv', 'env', '.venv', '.env', '.python-version',
        '.vscode', '.idea', '.vs', '.swp', '.swo',
        'scripts', 'lib', 'node_modules', 'dist', 'build',
        '.build', '.next', '.nuxt', '.output', 'cache',
        'netlify', 'public', 'shared',
        'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
        'coverage', '.nyc_output', 'logs'
    ]

    current_dir = Path(path).resolve()
    current_cwd = Path.cwd()

    # Особое правило: исключение папок Lib и Scripts из корневой директории проекта
    if current_dir == current_cwd:
        if name.lower() in ['lib', 'scripts']:
            return True

    # Особое правило: в корневой директории показывается папка frontend
    if current_dir == current_cwd and name == 'frontend':
        return False

    # Особое правило: во фронтенде остается только папка client
    if current_dir.name == 'frontend':
        if name != 'client' and os.path.isdir(os.path.join(path, name)):
            return True

    # Игнорирование скрытых файлов и папок
    if name.startswith('.'):
        return True

    # Игнорирование по паттернам
    if name.lower() in [pattern.lower() for pattern in ignore_patterns]:
        return True

    # Игнорирование бинарных файлов
    binary_extensions = ['.pyc', '.pyo', '.so', '.dll', '.exe', '.zip', '.tar', '.gz']
    if any(name.lower().endswith(ext.lower()) for ext in binary_extensions):
        return True

    return False


def generate_filtered_tree(start_path, output_file, max_depth=6, print_to_console=True):
    """
    Генерация дерева файлов с улучшенной системой исключений.

    Args:
        start_path (str): Путь к корневой директории проекта
        output_file (str): Имя файла для сохранения дерева
        max_depth (int): Максимальная глубина рекурсии
        print_to_console (bool): Флаг вывода дерева в консоль
    """
    lines = []

    def add_line(text):
        """Добавление строки в вывод и при необходимости в консоль."""
        lines.append(text)
        if print_to_console:
            print(text)

    add_line(f"Дерево проекта: {os.path.basename(os.path.abspath(start_path))}")
    add_line("=" * 60)
    add_line("Исключены: системные файлы, кэши, зависимости, билды, скрытые файлы")
    add_line("=" * 60)
    add_line("")

    # Печать корневой директории
    add_line(".")
    _generate_tree_recursive(Path(start_path), add_line, "", max_depth, 0)

    # Запись в файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def _generate_tree_recursive(path, add_line, prefix, max_depth, current_depth):
    """
    Рекурсивная генерация дерева файловой структуры.

    Args:
        path (Path): Текущий путь для обработки
        add_line (function): Функция для добавления строк вывода
        prefix (str): Префикс для отступов текущего уровня
        max_depth (int): Максимальная глубина рекурсии
        current_depth (int): Текущая глубина рекурсии
    """
    if current_depth >= max_depth:
        return

    try:
        items = sorted([item for item in path.iterdir()])
    except PermissionError:
        add_line(f"{prefix}└── [Доступ запрещен]")
        return

    # Фильтрация элементов
    filtered_items = []
    for item in items:
        if not should_ignore(str(path), item.name):
            filtered_items.append(item)

    if not filtered_items:
        return

    # Разделение папок и файлов
    directories = [item for item in filtered_items if item.is_dir()]
    files = [item for item in filtered_items if item.is_file()]

    # Сначала папки, потом файлы
    all_items = directories + files

    for i, item in enumerate(all_items):
        is_last = i == len(all_items) - 1
        connector = "└── " if is_last else "├── "

        if item.is_dir():
            add_line(f"{prefix}{connector}{item.name}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            _generate_tree_recursive(item, add_line, new_prefix, max_depth, current_depth + 1)
        else:
            size = item.stat().st_size
            size_str = format_size(size)
            add_line(f"{prefix}{connector}{item.name} {size_str}")


def format_size(size_bytes):
    """
    Форматирование размера файла в читаемый вид.

    Args:
        size_bytes (int): Размер файла в байтах

    Returns:
        str: Отформатированная строка размера
    """
    if size_bytes == 0:
        return "(empty)"
    elif size_bytes < 1024:
        return f"({size_bytes} B)"
    elif size_bytes < 1024 * 1024:
        return f"({size_bytes / 1024:.1f} KB)"
    else:
        return f"({size_bytes / (1024 * 1024):.1f} MB)"


if __name__ == "__main__":
    # Генерация файла с деревом с выводом в консоль
    generate_filtered_tree(
        start_path=".",
        output_file="project_structure.txt",
        max_depth=6,
        print_to_console=True
    )
    print("\nДерево проекта создано в файле 'project_structure.txt'!")