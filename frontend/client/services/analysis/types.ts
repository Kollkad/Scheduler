// services/analysis/types.ts

/**
 * Типы анализа, соответствующие новой архитектуре бэкенда
 * Порядок отражает правильную последовательность выполнения
 */
export type AnalysisType = 
  | 'rainbow'                   // Цветовая классификация (радуга)
  | 'documents'                 // Мониторинг документов
  | 'documents-charts'          // Мониторинг документов(диаграммы)
  | 'terms-v2-lawsuit'          // Исковое производство (данные)
  | 'terms-v2-order'            // Приказное производство (данные)
  | 'terms-v2-lawsuit-charts'   // Исковое производство (диаграммы)
  | 'terms-v2-order-charts'     // Приказное производство (диаграммы)
  | 'tasks'                     // Расчет задач
  | 'unique-values';            // Уникальные значения (фильтры)

/* Результат выполнения одного анализа*/
export interface AnalysisResult {
  success: boolean;             // Успешно ли выполнен анализ
  data: any;                    // Основные данные анализа
  total?: number;               // Общее количество (для радуги)
  totalCases?: number;          // Общее количество дел (для производств)
  totalDocuments?: number;      // Для документов
  count?: number;               // Количество элементов фильтрации
  message?: string;             // Сообщение о результате
  type?: AnalysisType;          // Тип анализа (для идентификации)
}

/*Задача анализа - объединяет несколько AnalysisResult*/
export interface AnalysisTask {
  id: string;                   // Уникальный идентификатор задачи
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'; // Статус выполнения
  results: Partial<Record<AnalysisType, AnalysisResult>>; // Результаты по типам
  progress: number;             // Прогресс выполнения (0-100)
  error?: string;               // Ошибка (если есть)
  timestamp: Date;              // Время создания задачи
}

/*Прогресс выполнения анализ */
export interface AnalysisProgress {
  currentTask: string;          // Текущая выполняемая задача
  progress: number;             // Общий прогресс (0-100)
  totalTasks: number;           // Всего задач для выполнения
}

/* Статус загруженных файлов (для интеграции с AnalysisContext)*/
export interface FilesStatus {
  currentDetailedReport?: {
    loaded?: boolean;
    filepath?: string;
    exists?: boolean;
  };
  documentsReport?: {
    loaded?: boolean;
    filepath?: string;
    exists?: boolean;
  };
  previousDetailedReport?: {
    loaded?: boolean;
    filepath?: string;
    exists?: boolean;
  };
  readyForAnalysis?: boolean;
}

/*Данные для отображения в диаграммах*/
export interface ChartData {
  group_name: string;           // Название группы (этапа)
  values: number[];             // Значения [в срок, просрочено, будет просрочено, нет данных]
}

/* Данные по задаче для отображения*/
export interface TaskData {
  taskCode: string;            // Код задачи
  caseCode: string;            // Код дела
  sourceType: string;          // Тип источника (detailed/documents)
  responsibleExecutor: string; // Ответственный исполнитель
  caseStage: string;           // Этап дела
  monitoringStatus: string;    // Статус мониторинга
  isCompleted: boolean;        // Выполнена ли задача
  taskText: string;            // Текст задачи
}

/*Данные по документу для отображения*/
export interface DocumentData {
  documentId: string;          // Идентификатор документа
  caseCode: string;            // Код связанного дела
  documentType: string;        // Тип документа
  monitoringStatus: string;    // Статус мониторинга (timely/overdue/no_data)
  deadlineDate?: string;       // Дата дедлайна
  responsibleExecutor?: string; // Ответственный исполнитель
}

/* Отладка ошибок */
/* Информация об ошибке в анализе*/
export interface AnalysisError {
  type: AnalysisType;           // Тип анализа, в котором произошла ошибка
  message: string;              // Сообщение об ошибке
  timestamp: Date;              // Время ошибки
}

/* Расширенный результат анализа с информацией об ошибках*/
export interface AnalysisResult {
  success: boolean;
  data: any;
  total?: number;
  totalCases?: number;
  count?: number;
  message?: string;
  type?: AnalysisType;
  error?: AnalysisError;
}

/*Статус выполнения полного анализа*/
export interface AnalysisStatus {
  completed: AnalysisType[];    // Успешно выполненные анализы
  failed: AnalysisError[];      // Анализы с ошибками
  isComplete: boolean;          // Завершен ли весь анализ
}
