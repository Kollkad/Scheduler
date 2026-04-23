import { featureFlags } from '@/config/featureFlags';
import { TableConfig } from "@/components/tables/TableTypes";

// Функция преобразует данные терминов из формата бэкенда в формат таблицы
export const mapBackendDataTerms = (data: Record<string, any>[]) => {
  return data.map(row => ({
    caseCode: row.caseCode || '',
    responsibleExecutor: row.responsibleExecutor || '',
    courtProtectionMethod: row.courtProtectionMethod || '',
    caseCategory: row.caseCategory || '',
    caseStatus: row.caseStatus || '',
    filingDate: row.filingDate || '',
    courtReviewingCase: row.courtReviewingCase || '',
    department: row.department || '',
    documentType: row.documentType || ''
  }));
};

// Функция преобразует данные документов из формата бэкенда в формат таблицы
export const mapBackendDataDocuments = (data: Record<string, any>[]) => {
  return data.map(row => ({
    transferCode: row.transferCode || '',
    responsibleExecutor: row.responsibleExecutor || '',
    caseCode: row.caseCode || '',
    documentType: row.documentType || '',
    department: row.department || '',
    monitoringStatus: formatMonitoringStatus(row.monitoringStatus || '')
  }));
};

// Функция преобразует данные задач из формата бэкенда в формат таблицы
export const mapBackendDataTasks = (data: any[]): any[] => {
  return data.map(task => ({
    ...task,
    stageCode: caseStageMapping[task.stageCode] || task.stageCode || "Не указан",
    monitoringStatus: formatMonitoringStatus(task.monitoringStatus)
  }));
};

// Функция форматирует статус мониторинга для читаемого отображения
export const formatMonitoringStatus = (statusString: string): string => {
  if (!statusString || statusString === "no_data") {
    return "Нет данных";
  }
  
  const statusParts = statusString.split(';');
  
  return statusParts.map((status, index) => {
    const cleanStatus = status.trim().toLowerCase();
    const translatedStatus = monitoringStatusMapping[cleanStatus] || cleanStatus;
    return `Проверка ${index + 1} - ${translatedStatus}`;
  }).join('; ');
};

// Конфигурация колонок для таблицы Rainbow
export const rainbowTableConfig = {
  columns: [
    { key: 'caseCode', title: 'Код дела', width: '150px', sortable: true },
    { key: 'responsibleExecutor', title: 'Ответственный исполнитель', width: '200px', sortable: true },
    { key: 'gosb', title: 'ГОСБ', width: '120px', sortable: true },
    { key: 'currentPeriodColor', title: 'Цвет (тек. период)', width: '120px', sortable: true },
    ...(featureFlags.hasPreviousReport ? [
      { key: 'previousPeriodColor', title: 'Цвет (пред. период)', width: '120px', sortable: true }
    ] : []),
    { key: 'caseStatus', title: 'Статус дела', width: '150px', sortable: true },
    { key: 'courtProtectionMethod', title: 'Способ судебной защиты', width: '180px', sortable: true },
    { key: 'courtReviewingCase', title: 'Суд, рассматривающий дело', width: '150px', sortable: true }
  ]
};

// Конфигурация колонок для таблицы фильтрованных дел (Rainbow)
export const filteredCasesTableConfig = {
  columns: rainbowTableConfig.columns
};

// Конфигурация колонок для таблиц терминов (единая для искового и приказного)
export const termsTableConfig = {
  columns: [
    { key: 'caseCode', title: 'Код дела', sortable: true },
    { key: 'responsibleExecutor', title: 'Ответственный исполнитель', sortable: true },
    { key: 'courtProtectionMethod', title: 'Способ судебной защиты', sortable: true },
    { key: 'caseStatus', title: 'Статус дела', sortable: true },
    { key: 'filingDate', title: 'Дата подачи иска', sortable: true },
    { key: 'courtReviewingCase', title: 'Суд, рассматривающий дело', sortable: true }
  ]
};

// Конфигурация колонок для таблицы задач
export const tasksTableConfig: TableConfig = {
  columns: [
    { key: "taskCode", title: "Код задачи", width: "150px", sortable: true },
    { key: "caseCode", title: "Код дела", width: "150px", sortable: true },  
    { key: "responsibleExecutor", title: "Ответственный исполнитель", width: "200px", sortable: true },
    { key: "stageCode", title: "Этап дела", width: "180px", sortable: true },
    { key: "checkName", title: "Название проверки", width: "120px", sortable: true },
    { key: "monitoringStatus", title: "Статус проверки", width: "150px", sortable: true },
    { key: "taskText", title: "Текст задачи", width: "300px", sortable: true },
  ],
  pageSize: 20,
};

// Маппинг этапов дела для читаемого отображения
export const caseStageMapping: Record<string, string> = {
  // Исковое производство
  "exceptionsL": "Исключение",
  "closedL": "Закрыто",
  "executionDocumentReceivedL": "ИД получен",
  "decisionMadeL": "Решение вынесено",
  "underConsiderationL": "На рассмотрении",
  "courtReactionL": "Ожидание реакции суда",
  "firstStatusChangedL": "Подготовка документов",
  // Приказное производство
  "exceptionsO": "Исключение",
  "closedO": "Закрыто",
  "executionDocumentReceivedO": "ИД получен",
  "courtReactionO": "Ожидание реакции суда",
  "firstStatusChangedO": "Подготовка документов",
  // Документы
  "transferredDocumentD": "Передача документа",
};

// Маппинг статусов мониторинга для читаемого отображения
export const monitoringStatusMapping: Record<string, string> = {
  "timely": "в срок",
  "overdue": "просрочена", 
  "no_data": "нет данных"
};

// Конфигурация колонок для таблиц этапов и документов
export const stageTableConfig = {
  lawsuit: {
    columns: termsTableConfig.columns
  },
  order: {
    columns: termsTableConfig.columns
  },
  documents: {
    columns: [
      { key: 'transferCode', title: 'Код передачи', width: '170px', sortable: true },
      { key: 'responsibleExecutor', title: 'Ответственный исполнитель', width: '200px', sortable: true },
      { key: 'caseCode', title: 'Код дела', width: '150px', sortable: true },
      { key: 'documentType', title: 'Тип документа', width: '180px', sortable: true },
      { key: 'department', title: 'Подразделение', width: '180px', sortable: true },
      { key: 'monitoringStatus', title: 'Статус мониторинга', width: '150px', sortable: true }
    ]
  }
};

// Функция возвращает конфигурацию таблицы для указанной страницы и типа процесса
export const getTableConfig = (page: 'rainbow' | 'filteredCases' | 'stageCases', processType?: 'lawsuit' | 'order' | 'documents') => {
  const configs = {
    rainbow: rainbowTableConfig,
    filteredCases: filteredCasesTableConfig,
    stageCases: processType ? stageTableConfig[processType] : stageTableConfig.lawsuit
  };
  return configs[page];
};