# backend/app/document_monitoring_v3/config/special_fields_document_v3.py

from backend.app.common.config.column_names import COLUMNS

# Список полей для категории "Общая информация" в карточке документа
SPECIAL_FIELDS_DOCUMENT = [
    COLUMNS["DOCUMENT_CASE_CODE"],      # Код дела
    COLUMNS["TRANSFER_CODE"],           # Код передачи
    COLUMNS["DOCUMENT_REQUEST_CODE"],   # Код запроса
    COLUMNS["CASE_NUMBER"],             # Судебный номер дела
    COLUMNS["CASE_NAME"],               # Наименование дела
    COLUMNS["COURT"],                   # Суд, рассматривающий дело
    COLUMNS["CASE_STATUS"],             # Статус дела
    COLUMNS["RESPONSIBLE_EXECUTOR"]     # Ответственный исполнитель
]