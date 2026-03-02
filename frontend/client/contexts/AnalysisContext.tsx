// src/contexts/AnalysisContext.tsx
import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';
import { 
  analysisService, 
  AnalysisType, 
  AnalysisProgress,
  AnalysisError,
  AnalysisStatus 
} from '@/services/analysis'; 

import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';
import { featureFlags } from '@/config/featureFlags';

// Интерфейс статуса загруженных файлов для анализа
export interface FilesStatus {
  current_detailed_report?: { filepath?: string; loaded?: boolean };
  documents_report?: { filepath?: string; loaded?: boolean };
  previous_detailed_report?: { filepath?: string; loaded?: boolean };
  ready_for_analysis?: boolean;
}

interface AnalysisContextType {
  // Состояние выполнения анализа
  isAnalyzing: boolean;
  progress: AnalysisProgress | null;
  // Статус выполнения и ошибки
  analysisStatus: AnalysisStatus;
  
  // Статус загруженных файлов
  uploadedFiles: FilesStatus | null;
  refreshFilesStatus: () => Promise<void>;

  // Методы управления анализом
  runAnalysis: () => Promise<AnalysisStatus>;
  cancelAnalysis: () => void;

  //Обновление UI почле анализа
  rainbowTrigger: number;
  termsTrigger: number;
  triggerRainbowUpdate: () => void;
  triggerTermsUpdate: () => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const useAnalysis = (): AnalysisContextType => {
  const context = useContext(AnalysisContext);
  if (context === undefined) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};

interface AnalysisProviderProps {
  children: ReactNode;
}

export const AnalysisProvider: React.FC<AnalysisProviderProps> = ({ children }) => {
  // Состояние выполнения анализа
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);
  
  // Статус выполнения анализа и информация об ошибках
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>({
    completed: [],
    failed: [],
    isComplete: false
  });

  // Статус загруженных файлов
  const [uploadedFiles, setUploadedFiles] = useState<FilesStatus | null>(null);

  // Функция отписки от отслеживания прогресса
  const [unsubscribeProgress, setUnsubscribeProgress] = useState<(() => void) | null>(null);

  //Обновления
  const [rainbowTrigger, setRainbowTrigger] = useState<number>(0);
  const [termsTrigger, setTermsTrigger] = useState<number>(0);

  const triggerRainbowUpdate = useCallback(() => {
    setRainbowTrigger(prev => prev + 1);
  }, []);

  const triggerTermsUpdate = useCallback(() => {
    setTermsTrigger(prev => prev + 1);
  }, []);

  // Функция обновляет статус загруженных файлов
  const refreshFilesStatus = useCallback(async () => {
    try {
      const status = await apiClient.get<FilesStatus>(API_ENDPOINTS.FILES_STATUS);
      
      if (!featureFlags.enableComparison && status.previous_detailed_report) {
        const { previous_detailed_report, ...statusWithoutComparison } = status;
        setUploadedFiles(statusWithoutComparison);
      } else {
        setUploadedFiles(status);
      }
    } catch (err) {
      console.error('Ошибка при запросе статуса файлов:', err);
    }
  }, []);

  // Функция обновляет общий статус выполнения анализа
  const updateAnalysisStatus = useCallback((type: AnalysisType, success: boolean, error?: AnalysisError) => {
    setAnalysisStatus(prev => {
      const newStatus = { ...prev };
      
      if (success) {
        newStatus.completed = [...prev.completed, type];
      } else if (error) {
        newStatus.failed = [...prev.failed, error];
      }
      
      return newStatus;
    });
  }, []);

  // Функция очистки кэша графиков
  const clearChartsCache = () => {
    try {
      const cacheKeys = [
        'rainbow_diagram_cache',
        'terms_lawsuit_charts_cache',
        'terms_order_charts_cache',
        'terms_documents_charts_cache'
      ];
      
      cacheKeys.forEach(key => {
        for (let i = 0; i < localStorage.length; i++) {
          const storageKey = localStorage.key(i);
          if (storageKey?.startsWith(key)) {
            localStorage.removeItem(storageKey);
          }
        }
      });
      console.log('Кэш графиков очищен');
    } catch (error) {
      console.error('Ошибка очистки кэша:', error);
    }
  };

  // Основная функция запускает полный последовательный анализ всех модулей
  const runAnalysis = useCallback(async (): Promise<AnalysisStatus> => {
    try {
      setIsAnalyzing(true);

      // Сброс предыдущих данных анализа на клиенте и сервере
      clearChartsCache();
      try {
        console.log('Сбрасываем предыдущие данные анализа...');
        await apiClient.post(API_ENDPOINTS.RESET_ANALYSIS);
        console.log('Сброс данных выполнен');
      } catch (resetError) {
        console.warn('Не удалось сбросить данные, продолжаем анализ:', resetError);
      }

      console.log('Запуск всех анализов');
      // Подписка на обновления прогресса анализа
      const unsubscribe = analysisService.onProgress((progressData) => {
        setProgress(progressData);
      });
      setUnsubscribeProgress(() => unsubscribe);

      // Последовательность выполнения анализов с весами для прогресса
      const analysisSequence: { type: AnalysisType; name: string; weight: number }[] = [
        { type: 'rainbow', name: 'Анализ цветовой классификации', weight: 15 },
        { type: 'documents', name: 'Анализ документов', weight: 25 },
        { type: 'documents-charts', name: 'Данные для диаграмм документов', weight: 30 },
        { type: 'terms-v2-lawsuit', name: 'Анализ искового производства', weight: 40 },
        { type: 'terms-v2-order', name: 'Анализ приказного производства', weight: 55 },
        { type: 'terms-v2-lawsuit-charts', name: 'Данные для диаграмм искового', weight: 70 },
        { type: 'terms-v2-order-charts', name: 'Данные для диаграмм приказного', weight: 80 },
        { type: 'tasks', name: 'Расчет задач', weight: 90 }
      ];

      let currentProgress = 0;

      // Последовательное выполнение всех анализов
      for (const { type, name, weight } of analysisSequence) {
        setProgress({ currentTask: name, progress: currentProgress, totalTasks: analysisSequence.length });
        
        // Выполняем анализ
        const result = await analysisService.runSingleAnalysis(type);

        // Обновление статуса выполнения
        if (result.success) {
          updateAnalysisStatus(type, true);
          console.log(`${name} - успешно завершен`);
          if (type === 'rainbow') {
            triggerRainbowUpdate();
            console.log('✅ Триггер Rainbow обновлен');
          }
          if (type === 'terms-v2-lawsuit-charts' || type === 'terms-v2-order-charts') {
            triggerTermsUpdate();
            console.log('✅ Триггер Terms обновлен');
          }
          if (type === 'documents-charts') {
            triggerTermsUpdate();
            console.log('✅ Триггер Documents обновлен');
          }
          
        } else {
          updateAnalysisStatus(type, false, result.error);
          console.warn(`${name} - завершен с ошибкой: ${result.message}`);
        }
        currentProgress = weight;
      }

      // Формирование финального статуса анализа
      const finalStatus: AnalysisStatus = {
        completed: analysisStatus.completed,
        failed: analysisStatus.failed,
        isComplete: true
      };

      setProgress({ currentTask: 'Анализ завершен', progress: 100, totalTasks: analysisSequence.length });
      setAnalysisStatus(finalStatus);
      // Обновление статуса файлов после завершения анализа
      await refreshFilesStatus();

      console.log('Полный анализ завершен', finalStatus);
      return finalStatus;

    } catch (error) {
      console.error('Критическая ошибка анализа:', error);
      
      const errorStatus: AnalysisStatus = {
        completed: analysisStatus.completed,
        failed: analysisStatus.failed,
        isComplete: false
      };
      
      setAnalysisStatus(errorStatus);
      throw error;
    } finally {
      setIsAnalyzing(false);
      setProgress(null);
      if (unsubscribeProgress) {
        unsubscribeProgress();
        setUnsubscribeProgress(null);
      }
    }
  }, [analysisStatus, updateAnalysisStatus, refreshFilesStatus]);

  // Функция отменяет текущий выполняемый анализ
  const cancelAnalysis = useCallback(() => {
    analysisService.cancelAnalysis();
    setIsAnalyzing(false);
    setProgress(null);
    if (unsubscribeProgress) {
      unsubscribeProgress();
      setUnsubscribeProgress(null);
    }
    console.log('Анализ отменен');
  }, [unsubscribeProgress]);

  // Эффект запрашивает статус файлов при монтировании компонента
  useEffect(() => {
    refreshFilesStatus().catch(err => {
      console.warn('Не удалось получить статус файлов при старте:', err);
    });
  }, [refreshFilesStatus]);

  // Эффект очистки подписки на прогресс при размонтировании
  useEffect(() => {
    return () => {
      if (unsubscribeProgress) {
        unsubscribeProgress();
      }
    };
  }, [unsubscribeProgress]);

  const value: AnalysisContextType = {
    isAnalyzing,
    progress,
    analysisStatus,
    uploadedFiles,
    refreshFilesStatus,
    runAnalysis,
    cancelAnalysis,
    rainbowTrigger,
    termsTrigger,
    triggerRainbowUpdate,
    triggerTermsUpdate,
  };

  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>;
};