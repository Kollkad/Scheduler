// frontend/client/config/tableConfig.ts
import { featureFlags } from '@/config/featureFlags';
import { TableConfig } from "@/components/tables/TableTypes";

// Базовые настройки оформления для всех таблиц системы
export const tableBaseConfig = {
  colors: {
    headerBackground: '#E3E3F1',
    border: '#BDBDCC', 
    text: '#171A1F',
    alternateRowBackground: '#F3F3FD',
    normalRowBackground: 'transparent'
  },
  defaultPageSize: 8
};

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
    department: row.department || ''
  }));
};

// Функция преобразует данные документов из формата бэкенда в формат таблицы
export const mapBackendDataDocuments = (data: Record<string, any>[]) => {
  return data.map(row => ({
    requestCode: row.requestCode || '',
    caseCode: row.caseCode || '',
    documentType: row.document || '',
    department: row.department || '',
    responseEssence: row.responseEssence || '',
    monitoringStatus: row.monitoringStatus || ''
  }));
};

// Функция преобразует данные задач из формата бэкенда в формат таблицы
export const mapBackendDataTasks = (data: any[]): any[] => {
  return data.map(task => ({
    ...task,
    caseStage: caseStageMapping[task.caseStage] || task.caseStage || "Не указан",
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
    { key: 'caseCode', title: 'Код дела', width: '120px' },
    { key: 'responsibleExecutor', title: 'Ответственный исполнитель', width: '200px' },
    { key: 'gosb', title: 'ГОСБ', width: '120px' },
    { key: 'currentPeriodColor', title: 'Цвет (тек. период)', width: '120px' },
    ...(featureFlags.hasPreviousReport ? [
      { key: 'previousPeriodColor', title: 'Цвет (пред. период)', width: '120px' }
    ] : []),
    { key: 'courtProtectionMethod', title: 'Способ судебной защиты', width: '180px' },
    { key: 'courtReviewingCase', title: 'Суд, рассматривающий дело', width: '150px' }
  ]
};

// Конфигурация колонок для таблицы фильтрованных дел
export const filteredCasesTableConfig = {
  columns: [
    { key: 'caseCode', title: 'Код дела', width: '120px' },
    { key: 'responsibleExecutor', title: 'Ответственный исполнитель', width: '200px' },
    { key: 'gosb', title: 'ГОСБ', width: '120px' },
    { key: 'currentPeriodColor', title: 'Цвет (тек. период)', width: '120px' },
    { key: 'caseStatus', title: 'Статус дела', width: '150px' },
    { key: 'courtProtectionMethod', title: 'Способ судебной защиты', width: '180px' },
    { key: 'courtReviewingCase', title: 'Суд, рассматривающий дело', width: '150px' }
  ]
};

// Конфигурация колонок для таблиц терминов по типам процессов
export const termsTableConfig = {
  lawsuit: {
    columns: [
      { key: 'caseCode', title: 'Код дела' },
      { key: 'responsibleExecutor', title: 'Ответственный исполнитель' },
      { key: 'courtProtectionMethod', title: 'Способ судебной защиты' },
      { key: 'caseCategory', title: 'Категория дела' },
      { key: 'caseStatus', title: 'Статус дела' },
      { key: 'filingDate', title: 'Дата подачи иска' },
      { key: 'courtReviewingCase', title: 'Суд, рассматривающий дело' }
    ]
  },
  order: {
    columns: [
      { key: 'caseCode', title: 'Код дела' },
      { key: 'responsibleExecutor', title: 'Ответственный исполнитель' },
      { key: 'courtProtectionMethod', title: 'Способ судебной защиты' },
      { key: 'caseCategory', title: 'Категория дела' },
      { key: 'caseStatus', title: 'Статус дела' },
      { key: 'filingDate', title: 'Дата подачи заявления' },
      { key: 'courtReviewingCase', title: 'Суд, рассматривающий дело' },
      { key: 'department', title: 'Категория подразделения' },
      { key: 'documentType', title: 'Документ' },
      { key: 'receiptDate', title: 'Дата поступления документа' },
      { key: 'transferDate', title: 'Дата передачи документа' }
    ]
  }
};

// Конфигурация колонок для таблицы задач
export const tasksTableConfig: TableConfig = {
  columns: [
    { key: "taskCode", title: "Код задачи", width: "120px" },
    { key: "caseCode", title: "Код дела", width: "120px" },  
    { key: "responsibleExecutor", title: "Ответственный исполнитель", width: "200px" },
    { key: "caseStage", title: "Этап дела", width: "180px" },
    { key: "failedCheck", title: "Название проверки", width: "120px" },
    { key: "monitoringStatus", title: "Статус проверки", width: "150px" },
    { key: "taskText", title: "Текст задачи", width: "300px" },
  ],
  pageSize: 20,
};

// Маппинг этапов дела для читаемого отображения
export const caseStageMapping: Record<string, string> = {
  "exceptions": "Исключение",
  "underConsideration": "На рассмотрении", 
  "decisionMade": "Решение вынесено",
  "courtReaction": "Ожидание реакции суда",
  "firstStatusChanged": "Подготовка документов",
  "closed": "Закрыто",
  "executionDocumentReceived": "ИД получен",
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
    columns: [
      { key: 'caseCode', title: 'Код дела', width: '170px' },
      { key: 'responsibleExecutor', title: 'Ответственный исполнитель', width: '200px' },
      { key: 'courtProtectionMethod', title: 'Способ судебной защиты', width: '150px' },
      { key: 'gosb', title: 'ГОСБ', width: '120px' },
      { key: 'caseStage', title: 'Этап дела', width: '150px' },
      { key: 'monitoringStatus', title: 'Статус мониторинга', width: '150px' },
      { key: 'caseStatus', title: 'Статус дела', width: '150px' },
      { key: 'filingDate', title: 'Дата подачи', width: '120px' },
      { key: 'courtReviewingCase', title: 'Суд', width: '180px' }
    ]
  },
  order: {
    columns: [
      { key: 'caseCode', title: 'Код дела', width: '170px' },
      { key: 'responsibleExecutor', title: 'Ответственный исполнитель', width: '200px' },
      { key: 'gosb', title: 'ГОСБ', width: '120px' },
      { key: 'caseStage', title: 'Этап дела', width: '150px' },
      { key: 'monitoringStatus', title: 'Статус мониторинга', width: '150px' },
      { key: 'caseStatus', title: 'Статус дела', width: '150px' },
      { key: 'filingDate', title: 'Дата подачи заявления', width: '140px' },
      { key: 'court', title: 'Суд', width: '180px' }
    ]
  },
  documents: {
    columns: [
      { key: 'requestCode', title: 'Код запроса', width: '170px' },
      { key: 'caseCode', title: 'Код дела', width: '150px' },
      { key: 'documentType', title: 'Тип документа', width: '180px' },
      { key: 'department', title: 'Подразделение', width: '180px' },
      { key: 'responseEssence', title: 'Суть ответа', width: '250px' },
      { key: 'monitoringStatus', title: 'Статус мониторинга', width: '150px' }
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