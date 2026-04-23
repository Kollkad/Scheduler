# backend/app/common/config/task_mappings.py
"""
Конфигурация задач для модуля управления задачами (v3).

Содержит маппинг условий формирования задач для различных типов производств:
- Исковое производство (lawsuit)
- Приказное производство (order)
- Документы (documents)

Каждая задача содержит:
- conditions: условия формирования [completion_status, monitoring_status]
- failed_check_name: код проверки из checks_config.py
- task_text: текст задачи для отображения пользователю
- reason_text: пояснение причины постановки задачи
- source: источник данных для проверки
"""
from backend.app.common.config.column_names import COLUMNS

TASK_MAPPINGS = {
    "lawsuit": {
        "closedL": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "closedL",
                "task_text": "Обеспечить закрытие дела. Обновить 'Дата закрытия дела' в системе",
                "reason_text": "Задача ставится если 'Дата закрытия дела' отсутствует и от 'Дата подачи иска/заявления' прошло более 125 календарных дней.",
                "source": "detailed_report"
            }
        ],

        "executionDocumentReceivedL": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "executionDocumentReceivedL",
                "task_text": "Обеспечить получение подтверждения исполнительного листа ПСИП",
                "reason_text": "Задача ставится если в отчёте документов для дела отсутствует документ 'Исполнительный лист' подразделения 'ПСИП', "
                               "либо статус мониторинга этого документа 'overdue', "
                               "либо в поле 'Суть ответа' не содержится 'Передача подтверждена'.",
                "source": "detailed_report"
            }
        ],

        "decisionMadeL": [
            {
                "special_conditions": {
                    "column": COLUMNS["CHARACTERISTICS_FINAL_COURT_ACT"],
                    "value": "Не в пользу Банка",
                    "columns": [COLUMNS["TAGS"]]
                },
                "failed_check_name": "decisionDateL",
                "task_text": "Принять решение об обжаловании",
                "reason_text": "Задача ставится если заполнены теги дела и значение 'Характеристика финального судебного акта' равно 'Не в пользу Банка'",
                "source": "detailed_report"
            },
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "decisionReceiptL",
                "task_text": "Отразить дату вступления в законную силу",
                "reason_text": "Задача ставится если 'Дата вступления в законную силу решения суда' отсутствует и "
                               "от 'Дата вынесения решения суда' прошло более 45 календарных дней.",
                "source": "detailed_report"
            },
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "decisionTransferL",
                "task_text": "Обеспечить передачу решения суда / судебного приказа / судебного акта",
                "reason_text": "Задача ставится если 'Фактическая дата передачи ИД' отсутствует и "
                               "от 'Дата вынесения решения суда' прошло более 1 календарного дня.",
                "source": "detailed_report"
            }
        ],

        "underConsiderationL": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "nextHearingPresentL",
                "task_text": "Фиксировать реакцию суда(новая дата, 'решение вынесено')",
                "reason_text": "Задача ставится если 'Дата ближайшего заседания суда' отсутствует и "
                               "от 'Дата вынесения определения суда' прошло более 3 рабочих дней.",
                "source": "detailed_report"
            },
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "hearingIntervalL",
                "task_text": "Фиксировать реакцию суда(новая дата, 'решение вынесено')",
                "reason_text": "Задача ставится если интервал между 'Дата предыдущего заседания суда' и 'Дата ближайшего заседания суда' превышает 2 рабочих дня, "
                               "либо одна из дат отсутствует, "
                               "либо дата ближайшего заседания раньше предыдущего.",
                "source": "detailed_report",
                "special_conditions": {
                    "check_type": "validate_hearing_dates",
                    "columns": [COLUMNS["PREVIOUS_HEARING_DATE"], COLUMNS["NEXT_HEARING_DATE"]]
                }
            },
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "consideration60daysL",
                "task_text": "Обеспечить вынесение решения суда",
                "reason_text": "Задача ставится если от 'Дата подачи иска/заявления' прошло более 60 календарных дней, а дело всё ещё в статусе 'На рассмотрении'.",
                "source": "detailed_report"
            }
        ],

        "courtReactionL": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "courtReactionL",
                "task_text": "Отобразить реакцию суда",
                "reason_text": "Задача ставится если 'Дата вынесения определения суда' отсутствует и от 'Дата подачи иска/заявления' прошло более 7 рабочих дней.",
                "source": "detailed_report"
            }
        ],

        "firstStatusChangedL": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "firstStatusChangedL",
                "task_text": "Проверить подачу документов в суд",
                "reason_text": "Задача ставится если от 'Дата подачи иска/заявления' прошло более 14 календарных дней, "
                               "а статус дела всё ещё 'Подготовка документов'.",
                "source": "detailed_report"
            }
        ]
    },

    "order": {
        "closedO": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "closedO",
                "task_text": "Обеспечить закрытие дела. Обновить данные 'Дата закрытия дела' в системе",
                "reason_text": "Задача ставится если 'Дата закрытия дела' отсутствует и от 'Дата подачи иска/заявления' прошло более 90 календарных дней.",
                "source": "detailed_report"
            }
        ],

        "executionDocumentReceivedO": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "executionDocumentReceivedO",
                "task_text": "Обеспечить получение подтверждения исполнительного листа ПСИП",
                "reason_text": "Задача ставится если в отчёте документов для дела отсутствует документ 'Исполнительный лист' подразделения 'ПСИП', либо статус мониторинга этого документа 'overdue', либо в поле 'Суть ответа' не содержится 'Передача подтверждена'.",
                "source": "detailed_report"
            },
            {
                "special_conditions": {
                    "status": "Условно закрыто",
                    "has_transfer_date": True
                },
                "failed_check_name": "executionDocumentReceivedO",
                "task_text": "Закрыть дело в системе",
                "reason_text": "Задача ставится если статус дела 'Условно закрыто' и 'Фактическая дата передачи ИД' заполнена, но дело не закрыто окончательно.",
                "source": "detailed_report"
            },
            {
                "special_conditions": {
                    "status": "Условно закрыто",
                    "has_transfer_date": False
                },
                "failed_check_name": "executionDocumentReceivedO",
                "task_text": "Передать СП",
                "reason_text": "Задача ставится если статус дела 'Условно закрыто', а 'Фактическая дата передачи ИД' не заполнена.",
                "source": "detailed_report"
            }
        ],

        "courtReactionO": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "courtReactionO",
                "task_text": "Обеспечить получение СП",
                "reason_text": "Задача ставится если от 'Дата подачи иска/заявления' прошло более 60 календарных дней, и при этом не выполнены все условия: "
                               "'Определение суда' не равно 'Судебный приказ', "
                               "либо отсутствует 'Дата получения ИД', "
                               "либо отсутствует 'Фактическая дата передачи ИД', "
                               "либо статус дела не 'Условно закрыто'.",
                "source": "detailed_report"
            },
            {
                "special_conditions": {
                    "check_type": "court_order_delivery"
                },
                "failed_check_name": "courtReactionO",
                "task_text": "Убедиться в суде, что СП вынесен и направлен должнику в течение 15 дней",
                "reason_text": "Задача ставится если дело приказного производства и требуется подтверждение, что судебный приказ вынесен и направлен должнику в течение 15 дней.",
                "source": "detailed_report"
            }
        ],

        "firstStatusChangedO": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "firstStatusChangedO",
                "task_text": "Проверить подачу документов в суд",
                "reason_text": "Задача ставится если от 'Дата подачи иска/заявления' прошло более 14 календарных дней, а статус дела всё ещё 'Подготовка документов'.",
                "source": "detailed_report"
            }
        ]
    },

    "documents": {
        "transferredDocumentD": [
            {
                "conditions": ["false", "overdue"],
                "failed_check_name": "documentTransferConfirmationD",
                "task_text": "Обеспечить подтверждение передачи документа",
                "reason_text": "Задача ставится если от 'Дата запроса' до 'Дата передачи' (при отсутствии даты передачи: до дня проверки) прошло более 14 дней и в столбце 'Суть ответа' не стоит 'Передача подтверждена'",
                "source": "documents_report"
            }
        ]
    }
}