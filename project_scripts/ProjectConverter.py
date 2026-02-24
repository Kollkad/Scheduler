"""
Модуль для конвертации файлов проекта в текстовый формат и обратно.

Предоставляет функциональность для преобразования структуры проекта в формат .txt
с сохранением информации о расширениях файлов и последующего восстановления.
"""
import os
import shutil
from pathlib import Path


class ProjectConverter:
    """
    Класс для конвертации файлов проекта между оригинальным и текстовым форматами.

    Обеспечивает двустороннее преобразование с сохранением структуры директорий
    и информации о расширениях файлов.
    """

    def __init__(self):
        """Инициализация конвертера с настройками формата."""
        self.converted_suffix = ".txt"
        self.extension_pattern = r"\(([^)]+)\)"
        self.excluded_dirs = {'node_modules', '__pycache__', 'Lib', 'Scripts'}

    def should_skip_directory(self, dir_path):
        """
        Проверяет, нужно ли пропустить директорию.

        Args:
            dir_path (Path): Путь к директории

        Returns:
            bool: True если директорию нужно пропустить
        """
        return dir_path.name in self.excluded_dirs

    def convert_to_txt(self, source_dir, target_dir):
        """
        Конвертация всех файлов проекта в формат txt с сохранением структуры папок.

        Оригинальное расширение файла добавляется в название в скобках.

        Args:
            source_dir (str): Путь к исходной директории проекта
            target_dir (str): Путь к целевой директории для сохранения
        """
        source_path = Path(source_dir)
        target_path = Path(target_dir)

        # Создание целевой директории если не существует
        target_path.mkdir(parents=True, exist_ok=True)

        converted_count = 0

        # Рекурсивный обход исходной директории
        for root, dirs, files in os.walk(source_dir):
            current_path = Path(root)

            # Пропуск исключенных директорий
            if self.should_skip_directory(current_path):
                print(f"Пропущена директория: {current_path}")
                dirs[:] = []  # Останавливаем обход вглубь этой директории
                continue

            # Фильтрация исключенных директорий из списка для обхода
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]

            # Получение относительного пути от исходной директории
            rel_path = current_path.relative_to(source_path)
            target_subdir = target_path / rel_path

            # Создание поддиректории в целевой папке
            target_subdir.mkdir(exist_ok=True)

            # Обработка каждого файла в текущей директории
            for file in files:
                source_file = current_path / file
                file_name = source_file.stem  # имя файла без расширения
                file_ext = source_file.suffix[1:] if source_file.suffix else ""  # расширение без точки

                # Формирование нового имени файла
                if file_ext:
                    new_filename = f"{file_name}({file_ext}){self.converted_suffix}"
                else:
                    new_filename = f"{file_name}{self.converted_suffix}"

                target_file = target_subdir / new_filename

                try:
                    # Копирование файла с новым именем
                    shutil.copy2(source_file, target_file)
                    converted_count += 1
                    print(f"Конвертирован: {source_file} -> {target_file}")
                except Exception as e:
                    print(f"Ошибка при конвертации {source_file}: {e}")

        print(f"\nКонвертация завершена. Обработано файлов: {converted_count}")

    def convert_from_txt(self, source_dir, target_dir):
        """
        Восстановление оригинальных файлов из txt-формата.

        Извлекает оригинальное расширение из названия файла и восстанавливает
        исходную структуру проекта.

        Args:
            source_dir (str): Путь к директории с конвертированными файлами
            target_dir (str): Путь для восстановления оригинального проекта
        """
        source_path = Path(source_dir)
        target_path = Path(target_dir)

        # Создание целевой директории если не существует
        target_path.mkdir(parents=True, exist_ok=True)

        restored_count = 0

        # Рекурсивный обход исходной директории
        for root, dirs, files in os.walk(source_dir):
            current_path = Path(root)

            # Пропуск исключенных директорий
            if self.should_skip_directory(current_path):
                print(f"Пропущена директория: {current_path}")
                dirs[:] = []  # Останавливаем обход вглубь этой директории
                continue

            # Фильтрация исключенных директорий из списка для обхода
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]

            # Получение относительного пути от исходной директории
            rel_path = current_path.relative_to(source_path)
            target_subdir = target_path / rel_path

            # Создание поддиректории в целевой папке
            target_subdir.mkdir(exist_ok=True)

            # Обработка каждого файла в текущей директории
            for file in files:
                source_file = current_path / file

                # Пропуск файлов, которые не являются конвертированными
                if not file.endswith(self.converted_suffix):
                    continue

                # Извлечение оригинального имени и расширения
                base_name = file[:-len(self.converted_suffix)]  # удаление .txt

                # Проверка наличия расширения в скобках
                if "(" in base_name and ")" in base_name:
                    # Разделение имени файла и расширения в скобках
                    name_part = base_name.rsplit("(", 1)[0]
                    ext_part = base_name.split("(")[-1].rstrip(")")

                    # Формирование оригинального имени файла
                    original_filename = f"{name_part}.{ext_part}" if ext_part else name_part
                else:
                    # Если скобок нет - файл без расширения
                    original_filename = base_name

                target_file = target_subdir / original_filename

                try:
                    # Копирование файла с оригинальным именем
                    shutil.copy2(source_file, target_file)
                    restored_count += 1
                    print(f"Восстановлен: {source_file} -> {target_file}")
                except Exception as e:
                    print(f"Ошибка при восстановлении {source_file}: {e}")

        print(f"\nВосстановление завершено. Обработано файлов: {restored_count}")


def main():
    """
    Основная функция для интерактивного использования конвертера.

    Предоставляет пользовательский интерфейс для выбора режима конвертации
    и ввода путей к директориям.
    """
    converter = ProjectConverter()

    print("Конвертер проекта")
    print("1. Конвертировать проект в txt-формат")
    print("2. Восстановить проект из txt-формата")

    choice = input("Выберите действие (1 или 2): ").strip()

    if choice == "1":
        source_dir = input("Введите путь к исходной папке проекта: ").strip()
        target_dir = input("Введите путь для сохранения конвертированного проекта: ").strip()

        if not source_dir or not target_dir:
            print("Ошибка: пути не могут быть пустыми")
            return

        converter.convert_to_txt(source_dir, target_dir)

    elif choice == "2":
        source_dir = input("Введите путь к папке с конвертированным проектом: ").strip()
        target_dir = input("Введите путь для восстановления оригинального проекта: ").strip()

        if not source_dir or not target_dir:
            print("Ошибка: пути не могут быть пустыми")
            return

        converter.convert_from_txt(source_dir, target_dir)

    else:
        print("Неверный выбор. Завершение работы.")


if __name__ == "__main__":
    main()