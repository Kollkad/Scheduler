#backend/app/additional_processing/config/anonymization_rules.py
"""
Конфигурация обезличивания данных для модуля дополнительной обработки.
Содержит единые правила анонимизации для всех типов отчетов.

Основные элементы:
- ALL_REPORTS_RULES: Список словарей с правилами замены для конкретных колонок.
- get_all_rules(): Возвращает полный список правил.
- get_applicable_rules(df_columns): Фильтрует правила по наличию колонок в DataFrame.
- validate_rule(rule): Проверяет корректность структуры правила.
"""

from backend.app.common.config.column_names import COLUMNS


# ЕДИНЫЕ ПРАВИЛА ДЛЯ ВСЕХ ОТЧЕТОВ
# Правила применяются только к тем колонкам, которые присутствуют в конкретном DataFrame.
ALL_REPORTS_RULES = [
    # ФИО и персоналии
    {
        "column_name": COLUMNS["RESPONSIBLE_EXECUTOR"],
        "replacement_type": "numbered",
        "replacement_text": "ФИО_"
    },
    {
        "column_name": COLUMNS["ADDITIONAL_EXECUTOR"],
        "replacement_type": "numbered",
        "replacement_text": "ФИО_"
    },
    {
        "column_name": COLUMNS["BORROWER"],
        "replacement_type": "numbered",
        "replacement_text": "ФИз/юр лицо_"
    },
    {
        "column_name": COLUMNS["REQUEST_INITIATOR"],
        "replacement_type": "numbered",
        "replacement_text": "ФИО_"
    },
    {
        "column_name": COLUMNS["EXECUTOR_FILED_CLAIMS"],
        "replacement_type": "numbered",
        "replacement_text": "ФИО_"
    },
    {
        "column_name": COLUMNS["INITIATOR_OF_TRANSFER"],
        "replacement_type": "numbered",
        "replacement_text": "ФИО_"
    },
    {
        "column_name": COLUMNS["EXECUTOR"],
        "replacement_type": "numbered",
        "replacement_text": "ФИО_"
    },

    # Названия и данные
    {
        "column_name": COLUMNS["CASE_NAME"],
        "replacement_type": "fixed",
        "replacement_text": "Данные о деле"
    },
    {
        "column_name": COLUMNS["DEFENDANTS"],
        "replacement_type": "fixed",
        "replacement_text": "Данные о людях"
    },
    {
        "column_name": COLUMNS["REGISTRATION_ADDRESS"],
        "replacement_type": "fixed",
        "replacement_text": "Полный адрес с индексом"
    },
    {
        "column_name": COLUMNS["CONTRACT_AGREEMENT_NUMBER"],
        "replacement_type": "fixed",
        "replacement_text": "Цифро-буквенный набор"
    },
    {
        "column_name": COLUMNS["REQUEST_SUBJECT"],
        "replacement_type": "fixed",
        "replacement_text": "Разные данные"
    },
    {
        "column_name": COLUMNS["DOCUMENT_NUMBER"],
        "replacement_type": "fixed",
        "replacement_text": "Цифро-буквенный набор"
    },
    {
        "column_name": COLUMNS["COMMENT_ON_THE_REASON_FOR_REFUSAL"],
        "replacement_type": "fixed",
        "replacement_text": "Любые возможно персональные данные"
    }
]


def get_all_rules() -> list[dict]:
    """
    Возвращает ВСЕ правила обезличивания, определенные в модуле.

    Returns:
        list[dict]: Копия списка ALL_REPORTS_RULES. Каждый словарь содержит ключи:
            'column_name' (str): Название колонки для обработки.
            'replacement_type' (str): Тип замены ('numbered' или 'fixed').
            'replacement_text' (str): Базовый текст для замены.
    """
    return ALL_REPORTS_RULES.copy()


def get_applicable_rules(df_columns: list[str]) -> list[dict]:
    """
    Фильтрует общие правила, оставляя только применимые к переданным колонкам.

    Args:
        df_columns (list[str]): Список названий колонок, присутствующих в
            целевом DataFrame.

    Returns:
        list[dict]: Список правил, у которых значение 'column_name' входит
            в предоставленный список df_columns.
    """
    applicable = []
    # Преобразование в set выполняется для оптимизации операции проверки вхождения.
    column_set = set(df_columns)

    for rule in ALL_REPORTS_RULES:
        if rule["column_name"] in column_set:
            applicable.append(rule)

    return applicable


def validate_rule(rule: dict) -> bool:
    """
    Проверяет корректность структуры и значений правила обезличивания.

    Функция выполняет валидацию на наличие обязательных полей и допустимость
    значения типа замены.

    Args:
        rule (dict): Словарь с правилом для проверки.

    Returns:
        bool: True, если правило корректно, иначе False.
    """
    required_fields = {"column_name", "replacement_type", "replacement_text"}

    # Проверка выполняется для всех обязательных полей.
    if not all(field in rule for field in required_fields):
        return False

    # Проверка допустимых значений для типа замены.
    if rule["replacement_type"] not in ["numbered", "fixed"]:
        return False

    return True