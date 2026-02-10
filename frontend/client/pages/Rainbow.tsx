// frontend/client/pages/Rainbow.tsx
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { DefaultChart } from "@/components/DefaultChart";
import { PageContainer } from "@/components/PageContainer";
import { RainbowMeanings } from "@/components/RainbowMeanings";
import { ReusableDataTable } from "@/components/tables/ReusableDataTable";
import { SettingsForm } from "@/components/sorter";
import { UploadFilesModal } from "@/components/UploadFilesModal";
import { useAnalysis } from "@/contexts/AnalysisContext";
import { featureFlags } from '@/config/featureFlags';
import { rainbowChartConfig } from '@/config/chartConfig';
import { sorterConfig } from '@/config/sorterConfig';
import { rainbowTableConfig } from '@/config/tableConfig';
import { transformRainbowData } from '@/utils/dataTransform';
import { useFilterOptions } from '@/hooks/useFilterOptions';
import { FilterService } from '@/services/filter/FilterService';
import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';

interface RainbowItem {
  name: string;
  label: string;
  value: number;
  color: string;
  full_name?: string;
}

// Конфигурация полей формы с динамической загрузкой опций
const rainbowFormFields = sorterConfig.rainbow.fields
  .filter(field => {
    if (field.id === 'previous_color' && !featureFlags.hasPreviousReport) {
      return false;
    }
    return true;
  })
  .map(field => ({
    ...field,
    options: [] // Опции загружаются динамически
  }));

const tableColumns = rainbowTableConfig.columns;

// Ключ для localStorage кэша
const RAINBOW_CACHE_KEY = 'rainbow_diagram_cache';
const CACHE_TTL = 5 * 60 * 1000; // 5 минут

interface CacheData {
  data: RainbowItem[];
  total: number;
  filters?: Record<string, string>;
  timestamp: number;
}

// Генерация ключа кэша с учетом фильтров
const generateCacheKey = (filters?: Record<string, string>): string => {
  if (!filters || Object.keys(filters).length === 0) {
    return RAINBOW_CACHE_KEY;
  }
  
  // Сортируем фильтры для консистентного ключа
  const sortedFilters = Object.keys(filters)
    .sort()
    .reduce((acc, key) => {
      acc[key] = filters[key];
      return acc;
    }, {} as Record<string, string>);
  
  return `${RAINBOW_CACHE_KEY}_${JSON.stringify(sortedFilters)}`;
};

export default function Rainbow() {
  const navigate = useNavigate();
  const { isAnalyzing } = useAnalysis();
  const [total, setTotal] = useState(0);
  const [rainbowData, setRainbowData] = useState<RainbowItem[]>([]);
  const { loadOptions } = useFilterOptions();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [tableData, setTableData] = useState<any[]>([]); 
  const [currentFilters, setCurrentFilters] = useState<Record<string, string>>({});
  const [reportStatus, setReportStatus] = useState<"idle" | "loading" | "ready">("idle");
  const [diagramFiltered, setDiagramFiltered] = useState<boolean>(false);
  
  // Флаг для предотвращения множественных одновременных запросов
  const isFetchingRef = useRef(false);

  // Функция загрузки кэша из localStorage
  const loadFromCache = (filters?: Record<string, string>): CacheData | null => {
    try {
      const cacheKey = generateCacheKey(filters);
      const cached = localStorage.getItem(cacheKey);
      if (!cached) return null;
      
      const parsed: CacheData = JSON.parse(cached);
      const isExpired = Date.now() - parsed.timestamp > CACHE_TTL;
      
      return isExpired ? null : parsed;
    } catch (error) {
      console.error('Ошибка чтения кэша:', error);
      return null;
    }
  };

  // Функция сохранения в кэш
  const saveToCache = (data: RainbowItem[], total: number, filters?: Record<string, string>) => {
    try {
      const cacheKey = generateCacheKey(filters);
      const cacheData: CacheData = {
        data,
        total,
        filters,
        timestamp: Date.now()
      };
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (error) {
      console.error('Ошибка сохранения кэша:', error);
    }
  };

  // Функция загрузки данных диаграммы с бэкенда
  const loadDiagramData = async (filters?: Record<string, string>) => {
    if (isFetchingRef.current) return null;
    isFetchingRef.current = true;

    try {
      const response = await apiClient.post<{
        success: boolean;
        data?: number[];
        totalCases?: number;
        filtered?: boolean;
        colorLabels?: string[];
        message?: string;
      }>(API_ENDPOINTS.RAINBOW_FILL_DIAGRAM, {
        filters: filters || {}
      });
      
      if (response.success && response.data) {
        console.log('Данные диаграммы получены:', {
          filtered: response.filtered,
          totalCases: response.totalCases,
          dataLength: response.data.length
        });

        // Преобразование данных для диаграммы
        const transformedData = transformRainbowData(
          response.data, 
          rainbowChartConfig.items,
          response.colorLabels
        );
        
        const totalCases = response.totalCases || 0;
        
        // Сохраняем в кэш
        saveToCache(transformedData, totalCases, filters);
        
        return {
          data: transformedData,
          total: totalCases,
          filtered: response.filtered || false
        };
      }
      return null;
    } catch (error) {
      console.error('Ошибка загрузки данных диаграммы:', error);
      return null;
    } finally {
      isFetchingRef.current = false;
    }
  };

  useEffect(() => {
    // 1. Загружаем данные из кэша (если есть и не устарели)
    const cached = loadFromCache(); // Без фильтров для начальной загрузки
    if (cached) {
      setRainbowData(cached.data);
      setTotal(cached.total);
      setDiagramFiltered(false);
    } else {
      // 2. Или показываем дефолтные данные
      const defaultData = transformRainbowData([], rainbowChartConfig.items);
      setRainbowData(defaultData);
      setTotal(0);
      setDiagramFiltered(false);
    }

    // 3. Фоновая загрузка актуальных данных
    const loadFreshData = async () => {
      const result = await loadDiagramData(); // Без фильтров
      if (result) {
        setRainbowData(result.data);
        setTotal(result.total);
        setDiagramFiltered(result.filtered);
      }
    };

    // Запускаем фоновую загрузку
    const shouldLoadImmediately = !cached || (Date.now() - cached.timestamp > CACHE_TTL);
    
    if (shouldLoadImmediately) {
      loadFreshData();
    } else {
      // Если кэш свежий, загружаем в фоне с небольшой задержкой
      setTimeout(loadFreshData, 1000);
    }

    // 4. Загружаем фильтры
    loadOptions().catch(error => {
      console.error('Ошибка загрузки фильтров:', error);
    });
  }, []);

  // Данные по умолчанию для таблицы до формирования отчета
  const defaultTableData = [{
    caseCode: 'Сначала сформируйте отчет',
    responsibleExecutor: '-',
    gosb: '-',
    currentPeriodColor: '-',
    courtProtectionMethod: '-',
    courtReviewingCase: '-',
    ...(featureFlags.hasPreviousReport && { previousPeriodColor: '-' })
  }];

  // Функция формирует отчет на основе текущих фильтров
  const handleGenerateReport = async () => {
    try {
      if (Object.keys(currentFilters).length === 0) {
        console.log('Нет активных фильтров');
        return;
      }

      console.log('Отправляем фильтры:', currentFilters);
      setReportStatus("loading");

      // ПАРАЛЛЕЛЬНАЯ ЗАГРУЗКА таблицы и диаграммы
      const [tableResult, diagramResult] = await Promise.allSettled([
        // 1. Загрузка табличных данных (существующий запрос)
        FilterService.applyFilters(currentFilters),
        
        // 2. Загрузка данных для диаграммы с теми же фильтрами
        loadDiagramData(currentFilters)
      ]);

      // Обработка результатов таблицы
      if (tableResult.status === 'fulfilled' && tableResult.value.success) {
        console.log('Табличные данные получены, записей:', tableResult.value.data.length);
        const fullTableData = tableResult.value.data.map((caseItem: any) => ({
          caseCode: caseItem.caseCode || 'Не указан',
          responsibleExecutor: caseItem.responsibleExecutor || 'Не указан',
          gosb: caseItem.gosb || 'Не указан',
          currentPeriodColor: caseItem.currentPeriodColor || 'Не указан',
          courtProtectionMethod: caseItem.courtProtectionMethod || 'Не указан',
          courtReviewingCase: caseItem.courtReviewingCase || 'Не указан',
          ...(featureFlags.hasPreviousReport && {
            previousPeriodColor: caseItem.previousPeriodColor || 'Не указан'
          })
        }));

        setTableData(fullTableData);
      } else {
        console.error('Ошибка при загрузке таблицы:', 
          tableResult.status === 'rejected' ? tableResult.reason : tableResult.value?.message);
        setTableData([]);
      }

      // Обработка результатов диаграммы
      if (diagramResult.status === 'fulfilled' && diagramResult.value) {
        console.log('Данные диаграммы получены успешно');
        setRainbowData(diagramResult.value.data);
        setTotal(diagramResult.value.total);
        setDiagramFiltered(diagramResult.value.filtered);
      } else {
        console.error('Ошибка при загрузке диаграммы:', 
          diagramResult.status === 'rejected' ? diagramResult.reason : 'Неизвестная ошибка');
      }

      setReportStatus("ready");
      console.log('Отчет сформирован');

    } catch (error) {
      console.error('Ошибка формирования отчета:', error);
      setReportStatus("idle");
    }
  };

  // Функция сброса фильтров и возврата к общей статистике
  const handleResetFilters = async () => {
    try {
      setReportStatus("loading");
      
      // Очищаем таблицу
      setTableData([]);
      setCurrentFilters({});
      
      // Загружаем общие данные диаграммы (без фильтров)
      const result = await loadDiagramData();
      if (result) {
        setRainbowData(result.data);
        setTotal(result.total);
        setDiagramFiltered(result.filtered);
      }
      
      setReportStatus("idle");
      console.log('Фильтры сброшены, загружена общая статистика');
    } catch (error) {
      console.error('Ошибка сброса фильтров:', error);
      setReportStatus("idle");
    }
  };

  // Конфигурация кнопок формы с обработчиками
  const rainbowFormButtons = [
    { 
      type: 'secondary' as const, 
      text: 'Очистить форму',
      onClick: undefined,
      onClearAll: handleResetFilters
    },
    { 
      type: 'primary' as const, 
      text: 'Сформировать отчет',
      onClick: handleGenerateReport
    }
  ];

  // Обработчик изменений фильтров в форме
  const handleFiltersChange = (filters: Record<string, string>) => {
    console.log('Фильтры изменены:', filters);
    setCurrentFilters(filters);
  };

  // Обработчик клика по строке таблицы для перехода к деталям дела
  const handleRowClick = (row: Record<string, any>) => {
    if (tableData.length > 1 && row.caseCode !== '-') {
      navigate(`/case/${row.caseCode}`);
    }
  };

  // Обработчик клика по столбцу диаграммы для фильтрации дел по цвету
  const handleBarClick = (item: { name: string; label: string; value: number; color: string }) => {
    if (item.value > 0) {
      const filters = diagramFiltered ? currentFilters : {};
      navigate(`/filtered-cases?source=rainbow&color=${encodeURIComponent(item.name)}&count=${item.value}&filters=${encodeURIComponent(JSON.stringify(filters))}`);
    }
  };

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Rainbow</h1>
        <div className="flex items-center gap-4">
          <p className="text-gray-600">
            Всего дел: {typeof total === 'number' ? total.toLocaleString() : '0'}
            {diagramFiltered && ' (отфильтровано)'}
          </p>
        </div>
        {isAnalyzing && <p className="text-blue-500">Идет анализ...</p>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <DefaultChart 
            data={rainbowData} 
            onBarClick={handleBarClick}
          />
        </div>

        <div className="space-y-4">
          <RainbowMeanings />
        </div>
      </div>

      <SettingsForm
        title={sorterConfig.rainbow.title}
        fields={rainbowFormFields}
        buttons={rainbowFormButtons}
        onFiltersChange={handleFiltersChange}
        initialValues={currentFilters}
      />

      <div className="mt-6">
        {reportStatus === "idle" && (
          <div className="text-gray-500 text-center py-6">
            После формирования отчёта здесь появится таблица
          </div>
        )}

        {reportStatus === "loading" && (
          <div className="text-gray-500 text-center py-6">
            Отчет формируется...
          </div>
        )}

        {reportStatus === "ready" && (
          <>
            <div className="mb-4 p-3 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-600">
                {diagramFiltered 
                  ? `Диаграмма отображает распределение по цветам для отфильтрованных дел (${total} шт.)`
                  : `Диаграмма отображает общее распределение по цветам (${total} шт.)`}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                В таблице: {tableData.length} записей
              </p>
            </div>
            <ReusableDataTable
              columns={tableColumns}
              data={tableData.length > 0 ? tableData : defaultTableData}
              onRowClick={handleRowClick}
              isLoading={isAnalyzing}
            />
          </>
        )}
      </div>
      
      <UploadFilesModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onCalculate={() => {}}
      />
    </PageContainer>
  );
}