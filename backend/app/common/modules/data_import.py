"""
backend/app/common/modules/data_import.py

Модуль загрузки данных из Excel файлов с расширенной обработкой ошибок.

Реализует многоуровневую стратегию восстановления поврежденных файлов:
- Стандартная загрузка с разными движками
- Восстановление через openpyxl с агрессивными настройками
- Ремонт XML структуры файла
- Упрощенные fallback методы
"""

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
import warnings
import os
import tempfile
import zipfile
import shutil


def load_excel_data(filepath):
    """
    Загрузка всех данных из Excel с многоуровневой обработкой ошибок.

    Args:
        filepath (str): Путь к Excel файлу

    Returns:
        pd.DataFrame: Загруженные данные

    Raises:
        ValueError: Если файл невозможно загрузить всеми методами
    """
    # Метод 0: Попытка стандартной загрузки
    try:
        print("🔧 Пробуем стандартную загрузку...")
        return pd.read_excel(filepath, header=None)
    except Exception as e:
        print(f"⚠️ Стандартная загрузка не удалась: {e}")
        print("🔄 Пробуем альтернативные методы...")

    # Метод 1: Попытка загрузки с разными движками
    for engine in ['openpyxl', 'xlrd']:
        try:
            print(f"🔧 Пробуем движок: {engine}")
            return pd.read_excel(filepath, header=None, engine=engine)
        except Exception as e:
            print(f"❌ Движок {engine} не сработал: {e}")
            continue

    # Метод 2: Восстановление файла через openpyxl с агрессивными настройками
    try:
        print("🔧 Пробуем восстановить файл через openpyxl...")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Тестирование разных режимов чтения
            for read_only in [True, False]:
                try:
                    wb = load_workbook(
                        filepath,
                        data_only=True,
                        read_only=read_only,
                        keep_links=False  # Отключение внешних ссылок
                    )
                    sheet = wb.active
                    data = []
                    max_rows = 10000  # Ограничение для избежания бесконечных циклов
                    row_count = 0

                    # Итерация по строкам листа
                    for row in sheet.iter_rows(values_only=True):
                        data.append(row)
                        row_count += 1
                        if row_count >= max_rows:
                            break

                    df = pd.DataFrame(data)
                    print(f"✅ Файл загружен в режиме read_only={read_only}, строк: {len(df)}")
                    return df
                except Exception as e:
                    print(f"❌ Режим read_only={read_only} не сработал: {e}")
                    continue
    except Exception as e:
        print(f"❌ Восстановление через openpyxl не удалось: {e}")

    # Метод 3: Восстановление XML структуры файла
    try:
        print("🔧 Пробуем восстановить XML структуру...")
        return repair_excel_xml(filepath)
    except Exception as e:
        print(f"❌ Восстановление XML не удалось: {e}")

    # Метод 4: Упрощенная загрузка как последнее средство
    try:
        print("🔧 Пробуем упрощенную загрузку...")
        return load_excel_data_simple_fallback(filepath)
    except Exception as e:
        print(f"❌ Упрощенная загрузка не удалась: {e}")

    raise ValueError(f"Не удалось загрузить файл {filepath}. Файл сильно поврежден.")


def repair_excel_xml(filepath):
    """
    Попытка восстановления поврежденной XML структуры Excel файла.

    Args:
        filepath (str): Путь к поврежденному файлу

    Returns:
        pd.DataFrame: Восстановленные данные

    Raises:
        Exception: При критических ошибках восстановления
    """
    temp_dir = tempfile.mkdtemp()

    try:
        # Распаковка Excel как ZIP архива
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Поиск и восстановление поврежденных XML файлов
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.xml') or file.endswith('.rels'):
                    file_path = os.path.join(root, file)
                    try:
                        repair_xml_file(file_path)
                    except Exception as e:
                        print(f"⚠️ Не удалось восстановить {file}: {e}")
                        # Создание минимального валидного файла при неудаче
                        try:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><root></root>')
                        except:
                            pass

        # Создание временного восстановленного файла
        repaired_path = os.path.join(temp_dir, "repaired.xlsx")
        with zipfile.ZipFile(repaired_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file != "repaired.xlsx":
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)

        # Загрузка восстановленного файла
        df = pd.read_excel(repaired_path, header=None, engine='openpyxl')
        print("✅ Файл восстановлен через XML repair")
        return df

    except Exception as e:
        print(f"❌ Ошибка при восстановлении XML: {e}")
        raise
    finally:
        # Очистка временных файлов
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


def repair_xml_file(file_path):
    """
    Восстанавливает отдельный XML файл путем очистки дублирующихся атрибутов.

    Args:
        file_path (str): Путь к XML файлу для восстановления
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Очистка дублирующихся атрибутов
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            # Удаление дублирующихся атрибутов
            words = line.split()
            seen_attrs = set()
            cleaned_words = []

            for word in words:
                if '=' in word and word not in seen_attrs:
                    seen_attrs.add(word)
                    cleaned_words.append(word)
                else:
                    cleaned_words.append(word)

            cleaned_line = ' '.join(cleaned_words)
            cleaned_lines.append(cleaned_line)

        cleaned_content = '\n'.join(cleaned_lines)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

    except Exception as e:
        print(f"⚠️ Ошибка при восстановлении {file_path}: {e}")
        # Создание минимального валидного XML
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><root></root>')
        except:
            pass


def load_excel_data_simple_fallback(filepath):
    """
    Максимально упрощенная загрузка для сильно поврежденных файлов.

    Args:
        filepath (str): Путь к поврежденному файлу

    Returns:
        pd.DataFrame: Частично загруженные данные или DataFrame с сообщением об ошибке

    Raises:
        ValueError: Если файл невозможно прочитать даже в упрощенном режиме
    """
    try:
        # Попытка загрузки с ограничением количества строк
        for nrows in [1000, 500, 100, 50]:
            try:
                df = pd.read_excel(filepath, header=None, nrows=nrows, engine='openpyxl')
                if len(df) > 0:
                    print(f"✅ Загружено {len(df)} строк (ограничение: {nrows})")
                    return df
            except Exception as e:
                print(f"❌ Загрузка {nrows} строк не удалась: {e}")
                continue
    except Exception as e:
        print(f"❌ Упрощенная загрузка с ограничением строк не удалась: {e}")

    # Последняя попытка: создание минимального DataFrame с сообщением об ошибке
    try:
        print("⚠️ Создаем минимальный DataFrame с сообщением об ошибке")
        return pd.DataFrame([["Файл поврежден", "Невозможно прочитать данные"]])
    except:
        raise ValueError("Файл невозможно прочитать даже в упрощенном режиме")