# backend/app/common/config/special_fields_case.py
"""
Конфигурация специальных полей для карточки дела.

Содержит перечень полей, которые отображаются в группе "Общая информация"
в фиксированном порядке с особым дизайном.
"""

from backend.app.common.config.column_names import COLUMNS

# Список реальных названий полей для категории "Общая информация"
SPECIAL_FIELDS = [
    COLUMNS["CASE_CODE"],
    COLUMNS["CASE_NUMBER"],
    COLUMNS["CONTRACT_AGREEMENT_NUMBER"],
    COLUMNS["CASE_NAME"],
    COLUMNS["METHOD_OF_PROTECTION"],
    COLUMNS["COURT"],
    COLUMNS["COURT_ADDRESS"],
    COLUMNS["CASE_STATUS"],
    COLUMNS["RESPONSIBLE_EXECUTOR"]
]