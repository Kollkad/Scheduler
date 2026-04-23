// client/services/saving/SavingService.ts
import { apiClient } from '../api/client';
import { API_ENDPOINTS } from '../api/endpoints';

export type SaveDataType = 
  | 'detailed-report'
  | 'documents-report'
  | 'stages'
  | 'checks'
  | 'check-results-cases'
  | 'check-results-documents'
  | 'tasks'
  | 'user-overrides';

export interface DataStatus {
  loaded: boolean;
  row_count: number;
}

export interface AvailableDataStatus {
  detailed_report: DataStatus;
  documents_report: DataStatus;
  stages: DataStatus;
  checks: DataStatus;
  check_results: DataStatus;
  tasks: DataStatus;
  user_overrides: DataStatus;
}

export class SavingService {
  private static instance: SavingService;

  static getInstance(): SavingService {
    if (!SavingService.instance) {
      SavingService.instance = new SavingService();
    }
    return SavingService.instance;
  }

  // Сохранение данных указанного типа
  async saveData(type: SaveDataType): Promise<Blob> {
    const endpointMap: Record<SaveDataType, string> = {
      'detailed-report': API_ENDPOINTS.SAVE_DETAILED_REPORT,
      'documents-report': API_ENDPOINTS.SAVE_DOCUMENTS_REPORT,
      'stages': API_ENDPOINTS.SAVE_STAGES,
      'checks': API_ENDPOINTS.SAVE_CHECKS,
      'check-results-cases': API_ENDPOINTS.SAVE_CHECK_RESULTS_CASES,
      'check-results-documents': API_ENDPOINTS.SAVE_CHECK_RESULTS_DOCUMENTS,
      'tasks': API_ENDPOINTS.SAVE_TASKS,
      'user-overrides': API_ENDPOINTS.SAVE_USER_OVERRIDES,
    };
    return await apiClient.downloadFile(endpointMap[type]);
  }

  // Сохранение задач по исполнителю
  async saveTasksByExecutor(executor: string): Promise<Blob> {
    return await apiClient.downloadFile(API_ENDPOINTS.SAVE_TASKS_BY_EXECUTOR, { executor });
  }

  // Получение статуса доступных данных для сохранения
  async getAvailableDataStatus(): Promise<{ success: boolean; status: AvailableDataStatus }> {
    return await apiClient.get(API_ENDPOINTS.SAVE_AVAILABLE_DATA_STATUS);
  }
}

export const savingService = SavingService.getInstance();