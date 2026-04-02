// frontend/client/pages/Rainbow.tsx

import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
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
import { useTableFiltersWithUrl } from '@/hooks/useTableFiltersWithUrl';
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

// Конфигурация полей формы с исключением неактивных полей на основе feature-флага
const rainbowFormFields = sorterConfig.rainbow.fields
  .filter(field => {
    if (field.id === 'previous_color' && !featureFlags.hasPreviousReport) {
      return false;
    }
    return true;
  })
  .map(field => ({
    ...field,
    options: [] // Опции загружаются динамически через useFilterOptions
  }));

const tableColumns = rainbowTableConfig.columns;

// Ключи для кэширования данных диаграммы в localStorage
const RAINBOW_CACHE_KEY = 'rainbow_diagram_cache';
const CACHE_TTL = 5 * 60 * 1000; // 5 минут

interface CacheData {
  data: RainbowItem[];
  total: number;
  filters?: Record<string, string>;
  timestamp: number;
}

// Генерация уникального ключа кэша на основе применённых фильтров
const generateCacheKey = (filters?: Record<string, string>): string => {
  if (!filters || Object.keys(filters).length === 0) {
    return RAINBOW_CACHE_KEY;
  }
  
  const sortedFilters = Object.keys(filters)
    .sort()
    .reduce((acc, key) => {
      acc[key] = filters[key];
      return acc;
    }, {} as Record<string, string>);
  
  return `${RAINBOW_CACHE_KEY}_${JSON.stringify(sortedFilters)}`;
};

// Получение русских названий полей из конфига таблицы
const getFilterFieldLabel = (fieldKey: string): string => {
  const column = rainbowTableConfig.columns.find(col => col.key === fieldKey);
  return column?.title || fieldKey;
};

// Преобразование объекта фильтров в читаемую строку
const formatFiltersToString = (filters: Record<string, string>): string => {
  const entries = Object.entries(filters)
    .filter(([, value]) => value && value !== '')
    .map(([key, value]) => {
      const fieldName = getFilterFieldLabel(key);
      return `${fieldName}: ${value}`;
    });
  
  if (entries.length === 0) return '';
  return entries.join(', ');
};

// Формирование объединённых фильтров (форма + таблица)
const getMergedFiltersDisplay = (formFilters: Record<string, string>, tableFilters: Record<string, string[]>): Record<string, string> => {
  const result: Record<string, string> = { ...formFilters };
  
  // Преобразование фильтров таблицы в формат {поле: значение}
  Object.entries(tableFilters).forEach(([key, values]) => {
    if (values && values.length > 0) {
      result[key] = values[0];
    }
  });
  
  return result;
};

// Получение фильтров таблицы из URL (для отображения при обновлении страницы)
const getTableFiltersFromUrl = (searchParams: URLSearchParams): Record<string, string[]> => {
  const filtersParam = searchParams.get('rainbow_filters');
  if (!filtersParam) return {};
  try {
    return JSON.parse(decodeURIComponent(filtersParam));
  } catch {
    return {};
  }
};

export default function Rainbow() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { isAnalyzing, rainbowTrigger } = useAnalysis();
  const [total, setTotal] = useState(0);
  const [rainbowData, setRainbowData] = useState<RainbowItem[]>([]);
  const { loadOptions } = useFilterOptions();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [tableData, setTableData] = useState<any[]>([]); 
  const [currentFilters, setCurrentFilters] = useState<Record<string, string>>({});
  const [reportStatus, setReportStatus] = useState<"idle" | "loading" | "ready">("idle");
  const [diagramFiltered, setDiagramFiltered] = useState<boolean>(false);
  
  const isFetchingRef = useRef(false);
  const prevFilterConfigRef = useRef<string>(''); // Отслеживание предыдущих фильтров таблицы для предотвращения бесконечных циклов
  const isInitialLoadRef = useRef(false);

  // Хук для синхронизации фильтров и сортировки таблицы с параметрами URL
  const { sortConfig, filterConfig, onSortChange, onFilterChange } = useTableFiltersWithUrl({
    tableKey: 'rainbow'
  });

  // Получение объединённых фильтров для отображения (с прямым чтением из URL)
  const getDisplayFilters = (): Record<string, string> => {
    const formFilters: Record<string, string> = {};
    for (const [key, value] of searchParams.entries()) {
      if (key !== 'rainbow_sort' && key !== 'rainbow_sort_dir' && key !== 'rainbow_filters') {
        formFilters[key] = value;
      }
    }
    const tableFiltersFromUrl = getTableFiltersFromUrl(searchParams);
    return getMergedFiltersDisplay(formFilters, tableFiltersFromUrl);
  };

  const displayFilters = getDisplayFilters();
  const displayFiltersString = formatFiltersToString(displayFilters);

  // Восстановление фильтров формы из URL при загрузке страницы
  useEffect(() => {
    const formFilters: Record<string, string> = {};
    for (const [key, value] of searchParams.entries()) {
      // Исключение параметров, принадлежащих таблице
      if (key !== 'rainbow_sort' && key !== 'rainbow_sort_dir' && key !== 'rainbow_filters') {
        formFilters[key] = value;
      }
    }
    
    // Получение фильтров таблицы из URL
    const tableFiltersFromUrl = getTableFiltersFromUrl(searchParams);
    
    // Объединение фильтров для первоначальной загрузки
    const mergedFilters: Record<string, string> = { ...formFilters };
    Object.entries(tableFiltersFromUrl).forEach(([key, values]) => {
      if (values && values.length > 0) {
        mergedFilters[key] = values[0];
      }
    });
    
    if (Object.keys(formFilters).length > 0 || Object.keys(tableFiltersFromUrl).length > 0) {
      setCurrentFilters(formFilters);
      isInitialLoadRef.current = true;
      const timer = setTimeout(() => {
        handleGenerateReportWithFilters(mergedFilters);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, []);

  // Чтение данных диаграммы из кэша localStorage
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

  // Сохранение данных диаграммы в кэш localStorage
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

  // Загрузка данных диаграммы с бэкенда
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
        const transformedData = transformRainbowData(
          response.data, 
          rainbowChartConfig.items,
          response.colorLabels
        );        
        const totalCases = response.totalCases || 0;
        
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

  // Основная функция загрузки таблицы и диаграммы с применением фильтров
  const handleGenerateReportWithFilters = async (filters: Record<string, string>) => {
    try {
      if (Object.keys(filters).length === 0) {
        return;
      }

      setReportStatus("loading");

      // Параллельная загрузка табличных данных и данных диаграммы
      const [tableResult, diagramResult] = await Promise.allSettled([
        FilterService.applyFilters(filters),
        loadDiagramData(filters)
      ]);

      if (tableResult.status === 'fulfilled' && tableResult.value.success) {
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
        setTableData([]);
      }

      if (diagramResult.status === 'fulfilled' && diagramResult.value) {
        setRainbowData(diagramResult.value.data);
        setTotal(diagramResult.value.total);
        setDiagramFiltered(diagramResult.value.filtered);
      }

      setReportStatus("ready");
      isInitialLoadRef.current = false;

    } catch (error) {
      console.error('Ошибка формирования отчета:', error);
      setReportStatus("idle");
      isInitialLoadRef.current = false;
    }
  };

  // Обновление параметров URL при изменении фильтров формы
  const updateUrlWithFormFilters = (filters: Record<string, string>) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      }
    });
    setSearchParams(params, { replace: true });
  };

  // Загрузка начальных данных при монтировании компонента
  useEffect(() => {
    const loadInitialData = async () => {
      const cached = loadFromCache();
      if (cached) {
        setRainbowData(cached.data);
        setTotal(cached.total);
        setDiagramFiltered(false);
      } else {
        const defaultData = transformRainbowData([], rainbowChartConfig.items);
        setRainbowData(defaultData);
        setTotal(0);
        setDiagramFiltered(false);
      }

      const result = await loadDiagramData();
      if (result) {
        setRainbowData(result.data);
        setTotal(result.total);
        setDiagramFiltered(result.filtered);
      }

      loadOptions().catch(error => {
        console.error('Ошибка загрузки фильтров:', error);
      });
    };

    loadInitialData();
  }, []);

  // Данные по умолчанию для отображения в таблице до формирования отчёта
  const defaultTableData = [{
    caseCode: 'Сначала сформируйте отчет',
    responsibleExecutor: '-',
    gosb: '-',
    currentPeriodColor: '-',
    courtProtectionMethod: '-',
    courtReviewingCase: '-',
    ...(featureFlags.hasPreviousReport && { previousPeriodColor: '-' })
  }];

  // Обработчик нажатия кнопки "Сформировать отчет"
  const handleGenerateReport = async () => {
    if (Object.keys(currentFilters).length === 0) {
      return;
    }
    updateUrlWithFormFilters(currentFilters);
    await handleGenerateReportWithFilters(currentFilters);
  };

  // Обновление данных диаграммы после завершения анализа
  useEffect(() => {
    const refreshAfterAnalysis = async () => {
      if (isAnalyzing) return;
      const result = await loadDiagramData(currentFilters);
      if (result) {
        setRainbowData(result.data);
        setTotal(result.total);
        setDiagramFiltered(result.filtered);
      }
    };

    refreshAfterAnalysis();
  }, [rainbowTrigger, isAnalyzing]);

  // Сброс всех фильтров и возврат к общей статистике
  const handleResetFilters = async () => {
    setReportStatus("loading");
    setTableData([]);
    setCurrentFilters({});
    setSearchParams({}, { replace: true });
    
    const result = await loadDiagramData();
    if (result) {
      setRainbowData(result.data);
      setTotal(result.total);
      setDiagramFiltered(result.filtered);
    }
    
    setReportStatus("idle");
  };

  // Конфигурация кнопок формы
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

  const handleFiltersChange = (filters: Record<string, string>) => {
    setCurrentFilters(filters);
  };

  // Переход на страницу деталей дела при клике по строке таблицы
  const handleRowClick = (row: Record<string, any>) => {
    if (tableData.length > 1 && row.caseCode !== '-') {
      navigate(`/case/${row.caseCode}`);
    }
  };

  // Переход на страницу отфильтрованных дел при клике по столбцу диаграммы
  const handleBarClick = (item: { name: string; label: string; value: number; color: string }) => {
    if (item.value > 0) {
      const filters = diagramFiltered ? currentFilters : {};
      navigate(`/filtered-cases?source=rainbow&color=${encodeURIComponent(item.name)}&count=${item.value}&filters=${encodeURIComponent(JSON.stringify(filters))}`);
    }
  };

  // При изменении фильтров в таблице (SortButton) происходит объединение с фильтрами формы и перезагрузка графика
  useEffect(() => {
    // Пропуск обработки во время первоначальной загрузки
    if (isInitialLoadRef.current) return;
    
    const currentFiltersKey = JSON.stringify(filterConfig);
    
    // Предотвращение повторных вызовов с теми же фильтрами
    if (prevFilterConfigRef.current === currentFiltersKey) {
      return;
    }
    prevFilterConfigRef.current = currentFiltersKey;
    
    if (reportStatus === "ready" && filterConfig && Object.keys(filterConfig).length > 0) {
      // Преобразование фильтров из таблицы в формат, ожидаемый бэкендом
      const tableFilters: Record<string, string> = {};
      Object.entries(filterConfig).forEach(([key, values]) => {
        if (values && values.length > 0) {
          tableFilters[key] = values[0];
        }
      });
      
      // Объединение фильтров формы и таблицы для перезагрузки графика
      const mergedFilters = { ...currentFilters, ...tableFilters };
      
      if (Object.keys(mergedFilters).length > 0) {
        handleGenerateReportWithFilters(mergedFilters);
      }
    }
  }, [filterConfig, reportStatus, currentFilters]);

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">Rainbow</h1>
        <div className="flex items-center gap-4">
          <p className="text-text-secondary">
            Всего дел: {typeof total === 'number' ? total.toLocaleString() : '0'}
            {diagramFiltered && ' (отфильтровано)'}
          </p>
        </div>
        {diagramFiltered && displayFiltersString && (
          <p className="text-sm text-text-secondary mt-1">
            Примененные фильтры: {displayFiltersString}
          </p>
        )}
        {isAnalyzing && <p className="text-blue">Идет анализ...</p>}
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
          <div className="text-text-secondary text-center py-6">
            После формирования отчёта здесь появится таблица
          </div>
        )}

        {reportStatus === "loading" && (
          <div className="text-text-secondary text-center py-6">
            Отчет формируется...
          </div>
        )}

        {reportStatus === "ready" && (
          <>
            <div className="mb-4 p-3 bg-bg-default-light-field rounded-md">
              <p className="text-sm text-text-secondary">
                Таблица и диаграмма отражают {tableData.length.toLocaleString()} дел
              </p>
              {diagramFiltered && displayFiltersString && (
                <p className="text-sm text-text-secondary mt-1">
                  Примененные фильтры: {displayFiltersString}
                </p>
              )}
            </div>
            <ReusableDataTable
              columns={tableColumns}
              data={tableData.length > 0 ? tableData : defaultTableData}
              sortConfig={sortConfig}
              onSortChange={onSortChange}
              filterConfig={filterConfig}
              onFilterChange={onFilterChange}
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