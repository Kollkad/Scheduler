// client/services/api/taskTypes.ts
//Типы данных толкьо для задач

// Базовый тип задачи
export interface Task {
  taskCode: string;
  failedCheck: string;
  caseCode: string;
  responsibleExecutor: string;
  stageCode: string;
  taskText: string;
  monitoringStatus: string;
  isCompleted: boolean;
  reasonText?: string;
  sourceType?: string;
  createdDate?: string;
  executionDatePlan?: string;
  executionDateTimeFact?: string;
  documentType?: string;
  department?: string;
  requestCode?: string;
  // Поля оверрайда
  hasOverride?: boolean;
  shiftCode?: string;
  shiftName?: string;
  daysToAdd?: number;
  originalPlannedDate?: string;
  // для расширяемости
  [key: string]: any;
}

// Тип для отображения в таблице (TaskItem)
export interface TaskItem extends Task {}

// Ответ от API /api/tasks/list
export interface TasksListResponse {
  success: boolean;
  totalTasks: number;
  filteredCount: number;
  column: string;
  value: string;
  tasks: Task[];
  message: string;
}

// Ответ от API /api/tasks/{task_code}
export interface TaskDetailsResponse {
  success: boolean;
  task: Task | null;
  message: string;
}