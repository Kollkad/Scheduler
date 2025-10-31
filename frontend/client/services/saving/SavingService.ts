// services/saving/SavingService.ts
import { apiClient } from '../api/client';

// Типы данных, доступные для сохранения в системе
export type SaveDataType = 
  | 'detailed-report'
  | 'documents-report' 
  | 'lawsuit-production'
  | 'order-production'
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
    const response = await fetch(`http://localhost:8000/api/save/${type}`);
    
    if (!response.ok) {
      throw new Error(`Ошибка сохранения: ${response.statusText}`);
    }
    
    return await response.blob();
  }

  // Метод получает статус доступных данных для сохранения
  async getAvailableDataStatus() {
    return await apiClient.get('/api/save/available-data');
  }

  // Метод получает статус всех обработанных данных в системе
  async getAllProcessedDataStatus() {
    return await apiClient.get('/api/save/all-processed-data');
  }
}

export const savingService = SavingService.getInstance();