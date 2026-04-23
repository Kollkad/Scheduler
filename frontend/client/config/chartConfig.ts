// src/config/chartConfig.ts

export interface ChartItemConfig {
  name: string;
  label: string;
  color: string;
}

export interface ChartGroupConfig {
  title: string;
  items: ChartItemConfig[];
}

export interface ChartConfig {
  title: string;
  items: ChartItemConfig[];
}

// Базовые сегменты для всех графиков (кроме исключений)
const BASE_SEGMENTS: ChartItemConfig[] = [
  { name: "timely", label: "В срок", color: "#41A457" },
  { name: "overdue", label: "Просрочено", color: "#FF5e3e" },
  { name: "upcoming_deadline", label: "Дело будет просрочено", color: "#FFA73B" },
  { name: "no_data", label: "Нет данных", color: "#8e8e8e" }
];
export const DEFAULT_SEGMENTS: ChartItemConfig[] = [
  { name: "timely", label: "В срок", color: "#41A457" },
  { name: "overdue", label: "Просрочено", color: "#FF5e3e" },
  { name: "no_data", label: "Нет данных", color: "#8e8e8e" }
];

// Специальные сегменты для исключений (разные цвета)
const EXCEPTIONS_SEGMENTS: ChartItemConfig[] = [
  { name: "reopened", label: "Переоткрыты", color: "#6EDFF2" },
  { name: "complaint_filed", label: "Жалоба подана", color: "#3d3dff" },
  { name: "error_dublicate", label: "Ошибка-Дубликат", color: "#e65cb3" },
  { name: "withdraw_by_the_initiator", label: "Отозвано инициатором", color: "#8b00ff" }
];

// ================= РАДУГА =================
export const rainbowChartConfig: ChartConfig = {
  title: "Rainbow",
  items: [
    { name: "ik", label: "ИК", color: "#000000" },  
    { name: "gray", label: "Серый", color: "#8e8e8e" },   
    { name: "green", label: "Зеленый", color: "#41A457" },  
    { name: "yellow", label: "Желтый", color: "#ffe947" }, 
    { name: "orange", label: "Оранжевый", color: "#FFA73B" },
    { name: "blue", label: "Синий", color: "#3d3dff" },
    { name: "red", label: "Красный", color: "#FF5e3e" },
    { name: "purple", label: "Лиловый", color: "#D53DFF" },
    { name: "white", label: "Белый", color: "#FFFFFF" }
  ]
};

// ================= ДОКУМЕНТЫ =================
export const documentsChartConfig: ChartGroupConfig[] = [
  {
    title: "Исполнительный лист",
    items: BASE_SEGMENTS
  },
  {
    title: "Решение суда",
    items: BASE_SEGMENTS
  },
  {
    title: "Судебный приказ",
    items: BASE_SEGMENTS
  }
];

export const documentsChecksToLabel: Record<string, string> = {
  "executionDocument": "Исполнительный лист",
  "courtDecision": "Решение суда", 
  "courtOrder": "Судебный приказ"
};

// ================= ИСКОВОЕ ПРОИЗВОДСТВО =================
export const lawsuitTermsConfig: ChartGroupConfig[] = [
  { title: "Исключения", items: EXCEPTIONS_SEGMENTS },
  { title: "1.1 Смена статуса подготовки (14кд)", items: BASE_SEGMENTS },
  { title: "2.1 Реакция суда (7рд)", items: BASE_SEGMENTS },
  { title: "3.1 Назначение заседания (3рд)", items: BASE_SEGMENTS },
  { title: "3.2 Интервал между заседаниями (2рд)", items: BASE_SEGMENTS },
  { title: "3.3 Рассмотрение дела (60кд)", items: BASE_SEGMENTS },
  { title: "4.1 Вынесение решения (45кд)", items: BASE_SEGMENTS },
  { title: "4.2 Получение решения (3кд)", items: BASE_SEGMENTS },
  { title: "4.3 Передача решения (1кд)", items: BASE_SEGMENTS },
  { title: "5.1 ИД получен (14кд)", items: BASE_SEGMENTS },
  { title: "6.1 Закрытие дела (125кд)", items: BASE_SEGMENTS },
];

// ================= ПРИКАЗНОЕ ПРОИЗВОДСТВО =================
export const orderTermsConfig: ChartGroupConfig[] = [
  { title: "Исключения", items: EXCEPTIONS_SEGMENTS },
  { title: "1.1 Смена статуса подготовки (14кд)", items: BASE_SEGMENTS },
  { title: "2.1 Реакция суда (60кд)", items: BASE_SEGMENTS },
  { title: "3.1 ИД получен (14кд)", items: BASE_SEGMENTS },
  { title: "4.1 Закрытие дела (90кд)", items: BASE_SEGMENTS },
];

// Маппинг checkCode → русское название этапа для искового производства
export const lawsuitChecksToLabel: Record<string, string> = {
  "exceptionsL": "Исключения",
  "closedL": "6.1 Закрытие дела (125кд)",
  "executionDocumentReceivedL": "5.1 ИД получен (14кд)",
  "decisionDateL": "4.1 Вынесение решения (45кд)",
  "decisionReceiptL": "4.2 Получение решения (3кд)",
  "decisionTransferL": "4.3 Передача решения (1кд)",
  "nextHearingPresentL": "3.1 Назначение заседания (3рд)",
  "hearingIntervalL": "3.2 Интервал между заседаниями (2рд)",
  "consideration60daysL": "3.3 Рассмотрение дела (60кд)",
  "courtReactionL": "2.1 Реакция суда (7рд)",
  "firstStatusChangedL": "1.1 Смена статуса подготовки (14кд)",
};
// Маппинг checkCode → русское название этапа для приказного производства
export const orderChecksToLabel: Record<string, string> = {
  "exceptionsO": "Исключения",
  "closedO": "4.1 Закрытие дела (90кд)",
  "executionDocumentReceivedO": "3.1 ИД получен (14кд)",
  "courtReactionO": "2.1 Реакция суда (60кд)",
  "firstStatusChangedO": "1.1 Смена статуса подготовки (14кд)",
};

// Вспомогательные функции
export const getRussianLabel = (englishName: string, config: ChartItemConfig[]): string => {
  const item = config.find(item => item.name === englishName);
  return item ? item.label : englishName;
};

export const getEnglishName = (russianLabel: string, config: ChartItemConfig[]): string => {
  const item = config.find(item => item.label === russianLabel);
  return item ? item.name : russianLabel;
};