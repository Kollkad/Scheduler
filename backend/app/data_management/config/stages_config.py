# backend/app/data_management/config/stages_config.py
"""
Конфигурация этапов для документов и производств.

Определяет статический список этапов, используемых в системе.
"""

from backend.app.data_management.models.stage import Stage
from typing import List

# Этапы для документов (из отчета документов)
DOCUMENT_STAGES = [
    Stage(stageCode="transferredDocumentD", stageName="Передача документа", fileType="documents_report"),
]

# Этапы для дел искового производства (из детального отчета)
LAWSUIT_STAGES = [
    Stage(stageCode="exceptionsL", stageName="Исключение", fileType="detailed_report"),
    Stage(stageCode="closedL", stageName="Закрыто", fileType="detailed_report"),
    Stage(stageCode="executionDocumentReceivedL", stageName="ИД получен", fileType="detailed_report"),
    Stage(stageCode="decisionMadeL", stageName="Решение вынесено", fileType="detailed_report"),
    Stage(stageCode="underConsiderationL", stageName="Рассмотрение дела", fileType="detailed_report"),
    Stage(stageCode="courtReactionL", stageName="Реакция суда", fileType="detailed_report"),
    Stage(stageCode="firstStatusChangedL", stageName="Подготовка документов", fileType="detailed_report"),
]

# Этапы для дел приказного производства (из детального отчета)
ORDER_STAGES = [
    Stage(stageCode="exceptionsO", stageName="Исключение", fileType="detailed_report"),
    Stage(stageCode="closedO", stageName="Закрыто", fileType="detailed_report"),
    Stage(stageCode="executionDocumentReceivedO", stageName="ИД получен", fileType="detailed_report"),
    Stage(stageCode="courtReactionO", stageName="Реакция суда", fileType="detailed_report"),
    Stage(stageCode="firstStatusChangedO", stageName="Подготовка документов", fileType="detailed_report"),
]

# Полный список этапов
ALL_STAGES = DOCUMENT_STAGES + LAWSUIT_STAGES + ORDER_STAGES

# Словарь для быстрого доступа по stageCode
STAGES_BY_CODE = {stage.stageCode: stage for stage in ALL_STAGES}

def get_stages_by_file_type(file_type: str) -> List[Stage]:
    """
    Возвращает список этапов, применимых к указанному типу файла.
    """
    return [stage for stage in ALL_STAGES if stage.fileType == file_type]

def get_stage_codes_by_file_type(file_type: str) -> List[str]:
    """
    Возвращает список stageCode, допустимых для указанного типа файла.
    """
    return [stage.stageCode for stage in get_stages_by_file_type(file_type)]

