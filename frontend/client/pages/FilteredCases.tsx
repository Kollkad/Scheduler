import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { ReusableDataTable } from "@/components/tables/ReusableDataTable";
import { mapBackendDataTerms, mapBackendDataDocuments, getTableConfig } from "@/config/tableConfig";
import { apiClient } from '@/services/api/client'; 
import { API_ENDPOINTS } from '@/services/api/endpoints'; 
import { useState, useEffect, useMemo } from 'react';
import { documentsChecksToLabel } from '@/config/chartConfig';
import { rainbowChartConfig } from '@/config/chartConfig';
import { Button } from "@/components/ui/button";
import { useTableFiltersWithUrl } from "@/hooks/useTableFiltersWithUrl";

interface RainbowCase {
  caseCode: string;
  responsibleExecutor: string;
  gosb: string;
  currentPeriodColor: string;
  previousPeriodColor?: string;
  courtProtectionMethod: string;
  courtReviewingCase: string;
  caseStatus: string;
}

interface TermsCase {
  caseCode: string;
  responsibleExecutor: string;
  courtProtectionMethod: string;
  caseCategory: string;
  caseStatus: string;
  filingDate: string;
  courtReviewingCase: string;
  department?: string;
  documentType?: string;
}

interface DocumentCase {
  transferCode: string;
  responsibleExecutor: string;
  caseCode: string;
  documentType: string;
  department: string;
  monitoringStatus: string;
}

interface RainbowCasesResponse { success: boolean; cases: RainbowCase[]; message: string; }
interface TermsCasesResponse { success: boolean; cases: TermsCase[]; message: string; }
interface DocumentCasesResponse { success: boolean; documents: DocumentCase[]; }

// Парсинг фильтров из параметра URL
const parseFiltersFromUrl = (filtersParam: string | null): Record<string, string> => {
  if (!filtersParam) return {};
  try {
    return JSON.parse(decodeURIComponent(filtersParam));
  } catch {
    return {};
  }
};

// Применение фильтров к данным на фронте
const applyFiltersToData = (data: any[], filters: Record<string, string>): any[] => {
  if (Object.keys(filters).length === 0) return data;
  
  return data.filter(item => {
    return Object.entries(filters).every(([key, value]) => {
      const itemValue = item[key];
      if (itemValue === undefined || itemValue === null) return false;
      return String(itemValue) === value;
    });
  });
};

export function FilteredCases() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [rawCases, setRawCases] = useState<RainbowCase[] | TermsCase[] | DocumentCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const source = searchParams.get('source') || 'rainbow';
  const color = searchParams.get('color') || '';
  const process = searchParams.get('process') || '';
  const stage = searchParams.get('stage') || '';
  const status = searchParams.get('status') || '';
  
  // Получение дополнительных фильтров из URL
  const filtersParam = searchParams.get('filters');
  const additionalFilters = parseFiltersFromUrl(filtersParam);

  // Хук для синхронизации фильтров и сортировки таблицы с URL
  const { sortConfig, filterConfig, onSortChange, onFilterChange } = useTableFiltersWithUrl({
    tableKey: 'filteredCases'
  });

  // Применение дополнительных фильтров к загруженным данным
  const filteredCases = useMemo(() => {
    return applyFiltersToData(rawCases, additionalFilters);
  }, [rawCases, additionalFilters]);

  const getCasesByColor = async (color: string): Promise<RainbowCasesResponse> => {
    return apiClient.get(`${API_ENDPOINTS.RAINBOW_CASES_BY_COLOR}?color=${encodeURIComponent(color)}`);
  };

  const getCasesByTerms = async (process: string, stage: string, status: string): Promise<TermsCasesResponse> => {
    let endpoint;
    if (process === 'lawsuit') endpoint = API_ENDPOINTS.TERMS_V2_LAWSUIT_FILTERED;
    else if (process === 'order') endpoint = API_ENDPOINTS.TERMS_V2_ORDER_FILTERED;
    else throw new Error('Неизвестный тип процесса');

    return apiClient.get(`${endpoint}?stage=${encodeURIComponent(stage)}&status=${encodeURIComponent(status)}`);
  };

  const getDocumentsByType = async (documentType: string, status: string): Promise<DocumentCasesResponse> => {
    const endpoint = '/api/documents/filter_documents';
    return apiClient.get(`${endpoint}?documentType=${encodeURIComponent(documentType)}&status=${encodeURIComponent(status)}`);
  };

  useEffect(() => {
    const loadCases = async () => {
      try {
        setLoading(true);
        setError(null);

        if (source === 'rainbow' && color) {
          const response = await getCasesByColor(color);
          setRawCases(response.cases);
        } 
        else if (source === 'terms' && process && stage && status) {
          const response = await getCasesByTerms(process, stage, status);
          setRawCases(mapBackendDataTerms(response.cases));
        } 
        else if (source === 'documents') {
          const documentType = searchParams.get('documentType') || '';
          const response = await getDocumentsByType(documentType, status);
          setRawCases(mapBackendDataDocuments(response.documents));
        } 
        else {
          setError('Неверные параметры фильтрации');
        }

      } catch (err: any) {
        setError(`Ошибка загрузки: ${err.message || 'Неизвестная ошибка'}`);
      } finally {
        setLoading(false);
      }
    };
    loadCases();
  }, [source, color, process, stage, status, searchParams]);

  // Формирование строки с информацией о применённых фильтрах
  const getAdditionalFiltersString = (): string => {
    const entries = Object.entries(additionalFilters);
    if (entries.length === 0) return '';
    
    const getFieldLabel = (key: string): string => {
      const labels: Record<string, string> = {
        courtProtectionMethod: 'Способ судебной защиты',
        responsibleExecutor: 'Ответственный исполнитель',
        gosb: 'ГОСБ',
        caseStatus: 'Статус дела',
        courtReviewingCase: 'Суд'
      };
      return labels[key] || key;
    };
    
    const filtersString = entries
      .map(([key, value]) => `${getFieldLabel(key)}: ${value}`)
      .join(', ');
    
    return ` (доп. фильтры: ${filtersString})`;
  };

  const getCaption = () => {
    if (source === 'rainbow' && color) {
      const colorItem = rainbowChartConfig.items.find(item => item.name === color);
      const russianColor = colorItem?.label || color;
      return `Дела с цветом: ${russianColor}${getAdditionalFiltersString()}`;
    }
    if (source === 'terms' && process && stage && status) {
      const processName = process === 'lawsuit' ? 'искового' : 'приказного';
      let readableStage = stage;
      if (stage === 'documents_transferred') {
        readableStage = 'Передача документов';
      }
      
      let readableStatus = status;
      if (status === 'timely') readableStatus = 'В срок';
      else if (status === 'overdue') readableStatus = 'Просрочено';
      else if (status === 'no_data') readableStatus = 'Нет данных';
      
      return `Дела ${processName} производства: ${readableStage} (${readableStatus})${getAdditionalFiltersString()}`;
    }
    if (source === 'documents') {
      const docType = searchParams.get('documentType') || '';
      let readableStatus = status;
      if (status === 'timely') readableStatus = 'В срок';
      else if (status === 'overdue') readableStatus = 'Просрочено';
      else if (status === 'no_data') readableStatus = 'Нет данных';
      const readableType = documentsChecksToLabel[docType] || docType;
      return `Документы: ${readableType} (${readableStatus})${getAdditionalFiltersString()}`;
    }
    return "Фильтрованные дела";
  };

  // Получение колонок из конфига
  const getTableColumns = () => {
    // Rainbow
    if (source === 'rainbow') {
      return getTableConfig('rainbow').columns;
    }

    // Documents
    if (source === 'documents') {
      return getTableConfig('stageCases', 'documents').columns;
    }

    // Terms (lawsuit / order)
    if (source === 'terms') {
      const baseColumns = [...getTableConfig('stageCases', 'lawsuit').columns];
      
      // Для documents_transferred добавляем documentType и department
      if (stage === 'documents_transferred') {
        return [
          ...baseColumns,
          { key: 'documentType', title: 'Тип документа', sortable: true },
          { key: 'department', title: 'Категория подразделения', sortable: true }
        ];
      }
      
      return baseColumns;
    }

    return [];
  };
  
  if (loading) return (
    <PageContainer>
      <div className="flex justify-center items-center h-64">
        <div className="text-text-secondary">Загрузка данных...</div>
      </div>
    </PageContainer>
  );

  if (error) return (
    <PageContainer>
      <div className="text-red text-center">{error}</div>
    </PageContainer>
  );

  return (
    <PageContainer>
      <Button
        variant="grayOutline"
        size="rounded"
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2"
      >
        <ArrowLeft className="h-4 w-4" />
        Вернуться назад
      </Button>

      <div className="mt-4 mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">{getCaption()}</h1>
        <p className="text-text-secondary">
          Найдено дел: {filteredCases.length.toLocaleString()}
          {Object.keys(additionalFilters).length > 0 && ` (из ${rawCases.length.toLocaleString()} всего)`}
        </p>
      </div>

      <ReusableDataTable
        columns={getTableColumns()}
        data={filteredCases}
        isLoading={loading}
        loadingMessage="Загрузка дел..."
        sortConfig={sortConfig}
        onSortChange={onSortChange}
        filterConfig={filterConfig}
        onFilterChange={onFilterChange}
        onRowClick={(row) => {
          if (source === 'documents' && row.transferCode) {
            navigate(`/document?transferCode=${encodeURIComponent(row.transferCode)}`);
          }
          else if (row.caseCode) {
            navigate(`/case/${row.caseCode}`);
          }
        }}
      />
    </PageContainer>
  );
}