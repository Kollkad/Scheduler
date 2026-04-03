// client/services/api/taskTypes.ts
//Типы данных толкьо для задач

// Базовый тип задачи
export interface Task {
  taskCode: string;
  failedCheck: string;
  caseCode: string;
  responsibleExecutor: string;
  caseStage: string;
  taskText: string;
  monitoringStatus: string;
  isCompleted: boolean;
  reasonText?: string;
  sourceType?: string;
  createdDate?: string;
  documentType?: string;
  department?: string;
  requestCode?: string;
  [key: string]: any; // для расширяемости
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