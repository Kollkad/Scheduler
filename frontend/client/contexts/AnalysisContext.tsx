// src/contexts/AnalysisContext.tsx
import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';
import { 
  analysisService, 
  AnalysisType, 
  AnalysisResult, 
  AnalysisProgress,
  AnalysisError,
  AnalysisStatus 
} from '@/services/analysis'; 

import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';
import { featureFlags } from '@/config/featureFlags';
import { useFilterOptions } from '@/hooks/useFilterOptions';

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

  // Результаты анализа по всем модулям системы
  rainbowResult: AnalysisResult | null;
  documentsResult: AnalysisResult | null;
  documentsChartsResult: AnalysisResult | null;
  termsV2LawsuitResult: AnalysisResult | null;
  termsV2OrderResult: AnalysisResult | null;
  termsV2LawsuitChartsResult: AnalysisResult | null;
  termsV2OrderChartsResult: AnalysisResult | null;
  tasksResult: AnalysisResult | null;
  uniqueValuesResult: AnalysisResult | null;
  
  // Статус загруженных файлов
  uploadedFiles: FilesStatus | null;
  refreshFilesStatus: () => Promise<void>;

  // Методы управления анализом
  runAnalysis: () => Promise<AnalysisStatus>;
  runSingleAnalysis: (type: AnalysisType) => Promise<AnalysisResult>;
  cancelAnalysis: () => void;
  clearResults: () => void;
  clearErrors: () => void;
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
  
  // Результаты анализа по различным модулям
  const [rainbowResult, setRainbowResult] = useState<AnalysisResult | null>(null);
  const [documentsResult, setDocumentsResult] = useState<AnalysisResult | null>(null);
  const [termsV2LawsuitResult, setTermsV2LawsuitResult] = useState<AnalysisResult | null>(null);
  const [termsV2OrderResult, setTermsV2OrderResult] = useState<AnalysisResult | null>(null);
  const [termsV2LawsuitChartsResult, setTermsV2LawsuitChartsResult] = useState<AnalysisResult | null>(null);
  const [termsV2OrderChartsResult, setTermsV2OrderChartsResult] = useState<AnalysisResult | null>(null);
  const [tasksResult, setTasksResult] = useState<AnalysisResult | null>(null);
  const [uniqueValuesResult, setUniqueValuesResult] = useState<AnalysisResult | null>(null);
  const [documentsChartsResult, setDocumentsChartsResult] = useState<AnalysisResult | null>(null);
  const { clearCache } = useFilterOptions();
  
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

  // Функция очищает все результаты анализа
  const clearResults = useCallback(() => {
    setRainbowResult(null);
    setDocumentsResult(null);
    setDocumentsChartsResult(null);
    setTermsV2LawsuitResult(null);
    setTermsV2OrderResult(null);
    setTermsV2LawsuitChartsResult(null);
    setTermsV2OrderChartsResult(null);
    setTasksResult(null);
    setUniqueValuesResult(null);
    setProgress(null);
    setAnalysisStatus({
      completed: [],
      failed: [],
      isComplete: false
    });
  }, []);

  // Функция очищает только ошибки анализа
  const clearErrors = useCallback(() => {
    setAnalysisStatus(prev => ({
      ...prev,
      failed: [],
      isComplete: false
    }));
  }, []);

  // Функция обновляет статус загруженных файлов
  const refreshFilesStatus = useCallback(async () => {
    try {
      const status = await apiClient.get<FilesStatus>(API_ENDPOINTS.FILES_STATUS);
      
      // Обработка флага сравнения для предыдущих отчетов
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

  // Функция запускает отдельный анализ указанного типа
  const runSingleAnalysis = useCallback(async (type: AnalysisType): Promise<AnalysisResult> => {
    try {
      console.log(`Запуск анализа: ${type}`);
      const result = await analysisService.runSingleAnalysis(type);
      
      if (result.success) {
        console.log(`Анализ завершен: ${type}`);
      } else {
        console.warn(`Анализ завершен с ошибкой: ${type}`, result.message);
      }
      
      return result;
    } catch (error) {
      console.error(`Ошибка анализа ${type}:`, error);
      const errorResult: AnalysisResult = {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Unknown error',
        type,
        error: {
          type,
          message: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date()
        }
      };
      return errorResult;
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

  // Функция очищает локальное хранилище от предыдущих результатов
  const clearLocalStorage = useCallback(() => {
    const keysToRemove = [
      'rainbowResult',
      'documentsResult', 
      'documentsChartsResult',
      'termsV2LawsuitResult',
      'termsV2OrderResult',
      'termsV2LawsuitChartsResult',
      'termsV2OrderChartsResult',
      'tasksResult'
    ];
    
    keysToRemove.forEach(key => {
      try {
        localStorage.removeItem(key);
      } catch (error) {
        console.warn(`Не удалось удалить ${key}:`, error);
      }
    });
  }, []);

  // Основная функция запускает полный последовательный анализ всех модулей
  const runAnalysis = useCallback(async (): Promise<AnalysisStatus> => {
    try {
      setIsAnalyzing(true);
      clearLocalStorage();
      clearResults();

      // Сброс предыдущих данных анализа на сервере
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
        
        const result = await runSingleAnalysis(type);
        
        // Сохранение результатов в состояние и локальное хранилище
        switch (type) {
          case 'rainbow':
            setRainbowResult(result);
            localStorage.setItem('rainbowResult', JSON.stringify(result));
            break;
          case 'documents':
            setDocumentsResult(result);
            break;
          case 'documents-charts':
            setDocumentsChartsResult(result);
            localStorage.setItem('documentsChartsResult', JSON.stringify(result));
            break;
          case 'terms-v2-lawsuit':
            setTermsV2LawsuitResult(result);
            break;
          case 'terms-v2-order':
            setTermsV2OrderResult(result);
            break;
          case 'terms-v2-lawsuit-charts':
            setTermsV2LawsuitChartsResult(result);
            localStorage.setItem('termsV2LawsuitChartsResult', JSON.stringify(result));
            break;
          case 'terms-v2-order-charts':
            setTermsV2OrderChartsResult(result);
            localStorage.setItem('termsV2OrderChartsResult', JSON.stringify(result));
            break;
          case 'tasks':
            setTasksResult(result);
            break;
        }

        // Обновление статуса выполнения
        if (result.success) {
          updateAnalysisStatus(type, true);
          console.log(`${name} - успешно завершен`);
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
      clearCache();
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
  }, [clearLocalStorage, clearResults, runSingleAnalysis, refreshFilesStatus, unsubscribeProgress, analysisStatus, updateAnalysisStatus]);

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

  // Эффект восстанавливает результаты анализа из локального хранилища
  useEffect(() => {
    const savedResults = [
      { key: 'rainbowResult', setter: setRainbowResult },
      { key: 'documentsResult', setter: setDocumentsResult },
      { key: 'documentsChartsResult', setter: setDocumentsChartsResult },
      { key: 'termsV2LawsuitResult', setter: setTermsV2LawsuitResult },
      { key: 'termsV2OrderResult', setter: setTermsV2OrderResult },
      { key: 'termsV2LawsuitChartsResult', setter: setTermsV2LawsuitChartsResult },
      { key: 'termsV2OrderChartsResult', setter: setTermsV2OrderChartsResult },
      { key: 'tasksResult', setter: setTasksResult },
    ];

    savedResults.forEach(({ key, setter }) => {
      const saved = localStorage.getItem(key);
      if (saved) {
        try {
          const result = JSON.parse(saved);
          setter(result);
          
          // Восстановление статуса выполнения для каждого модуля
          if (result.success && result.type) {
            updateAnalysisStatus(result.type, true);
          } else if (result.error) {
            updateAnalysisStatus(result.type, false, result.error);
          }
        } catch (err) {
          console.error(`Ошибка парсинга ${key}:`, err);
        }
      }
    });
  }, [updateAnalysisStatus]);

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
    rainbowResult,
    documentsResult,
    documentsChartsResult,
    termsV2LawsuitResult,
    termsV2OrderResult,
    termsV2LawsuitChartsResult,
    termsV2OrderChartsResult,
    tasksResult,
    uniqueValuesResult,
    analysisStatus,
    uploadedFiles,
    refreshFilesStatus,
    runAnalysis,
    runSingleAnalysis,
    cancelAnalysis,
    clearResults,
    clearErrors
  };

  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>;
};