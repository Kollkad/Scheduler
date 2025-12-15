// src/pages/Rainbow.tsx
import { useState, useEffect } from "react";
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

interface RainbowItem {
  name: string;
  label: string;
  value: number;
  color: string;
  full_name?: string;
}

interface RainbowCase {
  code?: string;
  executor?: string;
  gosb?: string;
  color?: string;
  previousColor?: string;
  protectionMethod?: string;
  court?: string;
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

export default function Rainbow() {
  const navigate = useNavigate();
  const { rainbowResult, isAnalyzing } = useAnalysis();
  const [total, setTotal] = useState(0);
  const [rainbowData, setRainbowData] = useState<RainbowItem[]>([]);
  const { loadOptions } = useFilterOptions();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [tableData, setTableData] = useState<any[]>([]); 
  const [currentFilters, setCurrentFilters] = useState<Record<string, string>>({});
  const [reportStatus, setReportStatus] = useState<"idle" | "loading" | "ready">("idle");

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

      const result = await FilterService.applyFilters(currentFilters);

      if (result.success) {
        console.log('Данные получены, записей:', result.data.length);

        // Преобразование данных для таблицы с безопасным извлечением значений
        const fullTableData = result.data.map((caseItem: any) => {
          const getValue = (field: string, defaultValue = "Не указан") => {
            const value = caseItem[field];
            return value !== null && value !== undefined && value !== "" 
              ? String(value) 
              : defaultValue;
          };

          return {
            caseCode: getValue('Код дела', 'Не указан'),
            responsibleExecutor: getValue('Ответственный исполнитель'),
            gosb: getValue('ГОСБ'),
            currentPeriodColor: getValue('Цвет (текущий период)'),
            courtProtectionMethod: getValue('Способ судебной защиты'), 
            courtReviewingCase: getValue('Суд, рассматривающий дело'),
            ...(featureFlags.hasPreviousReport && { 
              previousPeriodColor: getValue('Цвет (прошедший период)', 'Не указан')
            })
          };
        });

        setTableData(fullTableData);
        setReportStatus("ready");
        console.log('Таблица обновлена. Записей:', fullTableData.length);
      } else {
        console.error('Ошибка при формировании отчета:', result.message);
        setReportStatus("idle");
      }
      
    } catch (error) {
      console.error('Ошибка формирования отчета:', error);
      setReportStatus("idle");
    }
  };

  // Конфигурация кнопок формы с обработчиками
  const rainbowFormButtons = [
    { 
      type: 'secondary' as const, 
      text: 'Очистить форму',
      onClick: undefined,
      onClearAll: () => {
        setTableData([]);
        setReportStatus("idle");
      }
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

  // Эффект обновляет данные диаграммы при изменении результатов анализа
  useEffect(() => {
    if (rainbowResult && rainbowResult.success) {
      const transformedData = transformRainbowData(rainbowResult.data, rainbowChartConfig.items);
      setRainbowData(transformedData);
      setTotal(rainbowResult.total);
      
      loadOptions().then(() => {
        console.log('Фильтры загружены после анализа радуги');
      }).catch(error => {
        console.error('Ошибка загрузки фильтров:', error);
      });
    } else {
      const defaultData = transformRainbowData([], rainbowChartConfig.items);
      setRainbowData(defaultData);
      setTotal(0);
    }
  }, [rainbowResult]);

  // Обработчик клика по строке таблицы для перехода к деталям дела
  const handleRowClick = (row: Record<string, any>) => {
    if (tableData.length > 1 && row.caseCode !== '-') {
      navigate(`/case/${row.caseCode}`);
    }
  };

  // Обработчик клика по столбцу диаграммы для фильтрации дел по цвету
  const handleBarClick = (item: { name: string; label: string; value: number; color: string }) => {
    if (item.value > 0) {
      navigate(`/filtered-cases?source=rainbow&color=${encodeURIComponent(item.name)}&count=${item.value}`);
    }
  };

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Rainbow</h1>
        <p className="text-gray-600">Всего дел: {typeof total === 'number' ? total.toLocaleString() : '0'}</p>
        {isAnalyzing && <p className="text-blue-500">Идет анализ...</p>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <DefaultChart data={rainbowData} onBarClick={handleBarClick} />
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
      />

      <div className="mt-6">
        {reportStatus === "idle" && (
          <div className="text-gray-500 text-center py-6">
            После формирования отчёта здесь появится таблица
          </div>
        )}

        {reportStatus === "loading" && (
          <div className="text-gray-500 text-center py-6">
            Отчет формируется..
          </div>
        )}

        {reportStatus === "ready" && (
          <ReusableDataTable
            columns={tableColumns}
            data={tableData.length > 0 ? tableData : defaultTableData}
            onRowClick={handleRowClick}
            isLoading={isAnalyzing}
          />
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
