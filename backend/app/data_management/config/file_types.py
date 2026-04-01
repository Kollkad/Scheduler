# backend/app/data_management/config/file_types.py
"""
Конфигурация допустимых типов файлов для загрузки в систему.
"""

ALLOWED_FILE_TYPES = {
    "current_detailed_report",
    "documents_report",
    "previous_detailed_report",
    "anonymization_source",
    "anonymization_result"
}