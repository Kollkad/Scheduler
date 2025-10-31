// services/analysis/AnalysisService.ts
import { apiClient } from '../api/client';
import { API_ENDPOINTS } from '../api/endpoints';
import { AnalysisType, AnalysisResult, AnalysisTask, AnalysisProgress } from './types';

export class AnalysisService {
  private static instance: AnalysisService;
  private currentTask: AnalysisTask | null = null;
  private progressCallbacks: ((progress: AnalysisProgress) => void)[] = [];

  static getInstance(): AnalysisService {
    if (!AnalysisService.instance) {
      AnalysisService.instance = new AnalysisService();
    }
    return AnalysisService.instance;
  }
  
  // Основной метод запуска анализа с параллельным выполнением задач
  async runAnalysis(types: AnalysisType[]): Promise<AnalysisTask> {
    const taskId = this.generateTaskId();
    
    this.currentTask = {
      id: taskId,
      status: 'running',
      results: {},
      progress: 0,
      timestamp: new Date()
    };

    this.updateProgress('Сброс данных и запуск анализа', 0, types.length);

    try {
      const results = await Promise.allSettled(
        types.map((type, index) => 
          this.runSingleTask(type, index, types.length)
        )
      );

      this.currentTask.status = 'completed';
      this.currentTask.results = this.processResults(results, types);
      this.updateProgress('Анализ завершен', 100, types.length);

      return this.currentTask;
      
    } catch (error) {
      this.currentTask.status = 'failed';
      this.currentTask.error = error instanceof Error ? error.message : 'Unknown error';
      throw error;
    }
  }

  // Метод запускает отдельный анализ указанного типа
  async runSingleAnalysis(type: AnalysisType): Promise<AnalysisResult> {
    try {
      let data: any;
      
      // Маршрутизация запросов к соответствующим API endpoint'ам
      switch (type) {
        case 'rainbow':
          data = await apiClient.get(API_ENDPOINTS.RAINBOW_ANALYZE);
          break;
        
        case 'documents':
          data = await apiClient.get(API_ENDPOINTS.DOCUMENTS_ANALYZE);
          break;

        case 'documents-charts':
          data = await apiClient.get(API_ENDPOINTS.DOCUMENTS_CHARTS);
          break;
        
        case 'terms-v2-lawsuit':
          data = await apiClient.get(API_ENDPOINTS.TERMS_V2_LAWSUIT_ANALYZE);
          break;
        
        case 'terms-v2-order':
          data = await apiClient.get(API_ENDPOINTS.TERMS_V2_ORDER_ANALYZE);
          break;
        
        case 'terms-v2-lawsuit-charts':
          data = await apiClient.get(API_ENDPOINTS.TERMS_V2_LAWSUIT_CHARTS);
          break;
        
        case 'terms-v2-order-charts':
          data = await apiClient.get(API_ENDPOINTS.TERMS_V2_ORDER_CHARTS);
          break;
        
        case 'tasks':
          data = await apiClient.get(API_ENDPOINTS.TASKS_CALCULATE);
          break;
        
        case 'unique-values':
          data = await apiClient.get(API_ENDPOINTS.UNIQUE_VALUES);
          break;
        
        default:
          throw new Error(`Unknown analysis type: ${type}`);
      }

      return { 
        success: data.success !== undefined ? data.success : true,
        data: data.data || data,
        total: data.total || data.totalCases || data.totalDocuments || data.count,
        message: data.message,
        type 
      };
      
    } catch (error) {
      console.error(`Analysis task failed: ${type}`, error);
      return { 
        success: false, 
        data: null, 
        message: error instanceof Error ? error.message : 'Unknown error',
        type 
      };
    }
  }

  // Внутренний метод для выполнения отдельных задач в параллельном режиме
  private async runSingleTask(
    type: AnalysisType, 
    index: number, 
    total: number
  ): Promise<AnalysisResult> {
    this.updateProgress(`Выполнение: ${this.getTaskName(type)}`, index * 100 / total, total);
    return await this.runSingleAnalysis(type);
  }

  // Метод отменяет текущий выполняемый анализ
  cancelAnalysis(): void {
    if (this.currentTask && this.currentTask.status === 'running') {
      this.currentTask.status = 'cancelled';
      this.updateProgress('Анализ отменен', 0, 1);
    }
  }

  // Метод подписывает callback на обновления прогресса анализа
  onProgress(callback: (progress: AnalysisProgress) => void): () => void {
    this.progressCallbacks.push(callback);
    return () => {
      this.progressCallbacks = this.progressCallbacks.filter(cb => cb !== callback);
    };
  }

  // Внутренний метод обновляет прогресс и уведомляет подписчиков
  private updateProgress(taskName: string, progress: number, totalTasks: number): void {
    const progressInfo: AnalysisProgress = {
      currentTask: taskName,
      progress: Math.round(progress),
      totalTasks
    };

    this.progressCallbacks.forEach(callback => callback(progressInfo));
  }

  // Генерация уникального идентификатора задачи
  private generateTaskId(): string {
    return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Получение читаемого названия для типа анализа
  private getTaskName(type: AnalysisType): string {
    const names: Record<AnalysisType, string> = {
      'rainbow': 'Анализ радуги',
      'documents': 'Анализ документов',
      'documents-charts': 'Данные для диаграмм документов',
      'terms-v2-lawsuit': 'Анализ искового производства',
      'terms-v2-order': 'Анализ приказного производства',
      'terms-v2-lawsuit-charts': 'Данные для диаграмм искового',
      'terms-v2-order-charts': 'Данные для диаграмм приказного',
      'tasks': 'Расчет задач',
      'unique-values': 'Получение уникальных значений'
    };
    return names[type];
  }

  // Обработка результатов параллельного выполнения задач
  private processResults(
    results: PromiseSettledResult<AnalysisResult>[], 
    types: AnalysisType[]
  ): Partial<Record<AnalysisType, AnalysisResult>> {
    const processed: Partial<Record<AnalysisType, AnalysisResult>> = {};

    results.forEach((result, index) => {
      const type = types[index];
      
      if (result.status === 'fulfilled') {
        processed[type] = result.value;
      } else {
        processed[type] = {
          success: false,
          data: null,
          message: result.reason?.message || 'Unknown error',
          type
        };
      }
    });

    return processed;
  }
}

export const analysisService = AnalysisService.getInstance();