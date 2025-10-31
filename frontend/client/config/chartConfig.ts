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

// ================= ИСКОВОЕ ПРОИЗВОДСТВО V2 =================
export const lawsuitTermsV2Config: ChartGroupConfig[] = [
  {
    title: "Исключения",
    items: EXCEPTIONS_SEGMENTS
  },
  {
    title: "1.1 Смена статуса подготовки (14кд)",
    items: BASE_SEGMENTS
  },
  {
    title: "2.1 Реакция суда (7рд)",
    items: BASE_SEGMENTS
  },
  {
    title: "3.1 Назначение заседания (3рд)",
    items: BASE_SEGMENTS
  },
  {
    title: "3.2 Интервал между заседаниями (2рд)",
    items: BASE_SEGMENTS
  },
  {
    title: "3.3 Рассмотрение дела (60кд)",
    items: BASE_SEGMENTS
  },
  {
    title: "4.1 Вынесение решения (45кд)",
    items: BASE_SEGMENTS
  },
  {
    title: "4.2 Получение решения (3кд)",
    items: BASE_SEGMENTS
  },
  {
    title: "4.3 Передача решения (1кд)",
    items: BASE_SEGMENTS
  },
  {
    title: "5.1 ИД получен (14кд)",
    items: BASE_SEGMENTS
  },
  {
    title: "6.1 Закрытие дела (125кд)",
    items: BASE_SEGMENTS
  }
];

// ================= ПРИКАЗНОЕ ПРОИЗВОДСТВО V2 =================
export const orderTermsV2Config: ChartGroupConfig[] = [
  {
    title: "Исключения",
    items: EXCEPTIONS_SEGMENTS
  },
  {
    title: "1.1 Смена статуса подготовки (14кд)",
    items: BASE_SEGMENTS
  },
  {
    title: "2.1 Реакция суда (60кд)",
    items: BASE_SEGMENTS
  },
  {
    title: "3.1 ИД получен (14кд)",
    items: BASE_SEGMENTS
  },
  {
    title: "4.1 Закрытие дела (90кд)",
    items: BASE_SEGMENTS
  }
];

export const lawsuitChecksToLabel: Record<string, string> = {
  "exceptionStatus": "Исключения",
  "firstStatusChanged14days": "1.1 Смена статуса подготовки (14кд)",
  "courtReaction7days": "2.1 Реакция суда (7рд)",
  "nextHearing3days": "3.1 Назначение заседания (3рд)",
  "hearingInterval2days": "3.2 Интервал между заседаниями (2рд)", 
  "consideration60days": "3.3 Рассмотрение дела (60кд)",
  "decision45days": "4.1 Вынесение решения (45кд)",
  "decisionReceipt3days": "4.2 Получение решения (3кд)",
  "decisionTransfer1day": "4.3 Передача решения (1кд)",
  "executionDocumentReceivedL": "5.1 ИД получен (14кд)",
  "closed125days": "6.1 Закрытие дела (125кд)"
};
export const orderChecksToLabel: Record<string, string> = {
  "exceptionStatus": "Исключения",
  "firstStatus14Days": "1.1 Смена статуса подготовки (14кд)",
  "courtReaction60Days": "2.1 Реакция суда (60кд)", 
  "executionDocumentReceivedO": "3.1 ИД получен (14кд)",
  "closed90Days": "4.1 Закрытие дела (90кд)"
};

// ================= МАППИНГ ДЛЯ СТАРОГО КОДА =================
// Обновленный маппинг проверок (а не этапов) для обратной совместимости
export const stageNameToLabel: Record<string, string> = {
  // Исковое производство
  "nextHearing3days": "3.1 Назначение заседания (3 рабочих дня)",
  "hearingInterval2days": "3.2 Интервал между заседаниями (2 рабочих дня)", 
  "consideration60days": "3.3 Рассмотрение дела (60 календарных дней)",
  "decision45days": "4.1 Вынесение решения (45 календарных дней)",
  "decisionReceipt3days": "4.2 Получение решения (3 календарных дня)",
  "decisionTransfer1day": "4.3 Передача решения (1 календарный день)",
  "courtReaction7days": "2.1 Реакция суда (7 рабочих дней)",
  "firstStatusChanged14days": "1.1 Смена статуса подготовки (14 календарных дней)",
  "closed125days": "6.1 Закрытие дела (125 календарных дней)",
  "executionDocumentReceivedL": "5.1 ИД получен (14 календарных дней)",
  
  // Приказное производство
  "exceptionStatus": "Исключения",
  "closed90Days": "4.1 Закрытие дела (90 календарных дней)",
  "executionDocumentReceivedO": "3.1 ИД получен (14 календарных дней)",
  "courtReaction60Days": "2.1 Реакция суда (60 календарных дней)",
  "firstStatus14Days": "1.1 Смена статуса подготовки (14 календарных дней)"
};

// Устаревшие конфиги (можно удалить после полного перехода на v2)
export const stageNameToLabelV2: Record<string, string> = {};
export const lawsuitTermsConfig: ChartGroupConfig[] = [];
export const orderTermsConfig: ChartGroupConfig[] = [];

// Вспомогательные функции
export const getRussianLabel = (englishName: string, config: ChartItemConfig[]): string => {
  const item = config.find(item => item.name === englishName);
  return item ? item.label : englishName;
};

export const getEnglishName = (russianLabel: string, config: ChartItemConfig[]): string => {
  const item = config.find(item => item.label === russianLabel);
  return item ? item.name : russianLabel;
};