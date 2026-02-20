//client\services\saving\SavingService.ts
import { apiClient } from '../api/client';
import { StatusResponse } from '../api/types';

// Типы данных, доступные для сохранения в системе
export type SaveDataType = 
  | 'detailed-report'
  | 'documents-report' 
  | 'terms-productions'
  | 'documents-analysis'
  | 'tasks'
  | 'rainbow-analysis'
  | 'all-analysis';

export class SavingService {
  private static instance: SavingService;

  static getInstance(): SavingService {
    if (!SavingService.instance) {
      SavingService.instance = new SavingService();
    }
    return SavingService.instance;
  }

  // Метод сохраняет данные указанного типа и возвращает blob с результатом
  async saveData(type: SaveDataType): Promise<Blob> {
    return await apiClient.downloadFile(`/api/save/${type}`);
  }

  // Метод получает статус доступных данных для сохранения
  async getAvailableDataStatus() {
    return await apiClient.get('/api/save/available-data');
  }

  // Метод получает статус всех обработанных данных в системе
  async getAllProcessedDataStatus(): Promise<StatusResponse> {
    return await apiClient.get<StatusResponse>('/api/save/all-processed-data');
  }
}

export const savingService = SavingService.getInstance();