// src/components/FilteredCases.tsx
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { ReusableDataTable } from "@/components/tables/ReusableDataTable";
import { mapBackendDataTerms, mapBackendDataDocuments } from "@/config/tableConfig";
import { featureFlags } from '@/config/featureFlags';
import { apiClient } from '@/services/api/client'; 
import { API_ENDPOINTS } from '@/services/api/endpoints'; 
import { useState, useEffect } from 'react';
import { lawsuitTermsConfig, orderTermsConfig, stageNameToLabel, documentsChecksToLabel } from '@/config/chartConfig';
import { rainbowChartConfig } from '@/config/chartConfig';

// Типы данных для различных источников дел
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
}

interface DocumentCase {
  requestCode?: string;
  caseCode: string;
  documentType: string;
  monitoringStatus: string;
  receiptDate?: string;
  transferDate?: string;
  department?: string;
}

// Типы ответов API для различных источников данных
interface RainbowCasesResponse { success: boolean; cases: RainbowCase[]; message: string; }
interface TermsCasesResponse { success: boolean; cases: TermsCase[]; message: string; }
interface DocumentCasesResponse { success: boolean; documents: DocumentCase[]; }

export function FilteredCases() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [cases, setCases] = useState<RainbowCase[] | TermsCase[] | DocumentCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const source = searchParams.get('source') || 'rainbow';
  const color = searchParams.get('color') || '';
  const process = searchParams.get('process') || '';
  const stage = searchParams.get('stage') || '';
  const status = searchParams.get('status') || '';

  // Функция загружает дела по цветовым меткам Rainbow
  const getCasesByColor = async (color: string): Promise<RainbowCasesResponse> => {
    return apiClient.get(`${API_ENDPOINTS.RAINBOW_CASES_BY_COLOR}?color=${encodeURIComponent(color)}`);
  };

  // Функция загружает дела по срокам процессов
  const getCasesByTerms = async (process: string, stage: string, status: string): Promise<TermsCasesResponse> => {
    let endpoint;
    if (process === 'lawsuit') endpoint = API_ENDPOINTS.TERMS_V2_LAWSUIT_FILTERED;
    else if (process === 'order') endpoint = API_ENDPOINTS.TERMS_V2_ORDER_FILTERED;
    else throw new Error('Неизвестный тип процесса');

    return apiClient.get(`${endpoint}?stage=${encodeURIComponent(stage)}&status=${encodeURIComponent(status)}`);
  };

  // Функция загружает документы по типу и статусу
  const getDocumentsByType = async (documentType: string, status: string): Promise<DocumentCasesResponse> => {
    const endpoint = '/api/documents/filter_documents';
    return apiClient.get(`${endpoint}?documentType=${encodeURIComponent(documentType)}&status=${encodeURIComponent(status)}`);
  };

  // Эффект загружает данные при изменении параметров фильтрации
  useEffect(() => {
    const loadCases = async () => {
      try {
        setLoading(true);
        setError(null);

        if (source === 'rainbow' && color) {
          const response = await getCasesByColor(color);
          setCases(response.cases);
        } 
        else if (source === 'terms' && process && stage && status) {
          const response = await getCasesByTerms(process, stage, status);
          setCases(mapBackendDataTerms(response.cases));
        } 
        else if (source === 'documents') {
          const documentType = searchParams.get('documentType') || '';
          const response = await getDocumentsByType(documentType, status);
          setCases(mapBackendDataDocuments(response.documents));
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
  }, [source, color, process, stage, status]);

  // Функция формирует заголовок страницы в зависимости от источника данных
  const getCaption = () => {
    if (source === 'rainbow' && color) {
      const colorItem = rainbowChartConfig.items.find(item => item.name === color);
      const russianColor = colorItem?.label || color;
      return `Дела с цветом: ${russianColor}`;
    }
    if (source === 'terms' && process && stage && status) {
      const processName = process === 'lawsuit' ? 'искового' : 'приказного';
      const readableStage = stageNameToLabel[stage] || stage;

      const config = process === 'lawsuit' ? lawsuitTermsConfig : orderTermsConfig;
      let readableStatus = status;
      for (const group of config) {
        const statusItem = group.items.find(item => item.name === status);
        if (statusItem) { readableStatus = statusItem.label; break; }
      }
      return `Дела ${processName} производства: ${readableStage} (${readableStatus})`;
    }
    if (source === 'documents') {
      const docType = searchParams.get('documentType') || '';
      let readableStatus = status;
      if (status === 'timely') readableStatus = 'В срок';
      else if (status === 'overdue') readableStatus = 'Просрочено';
      else if (status === 'no_data') readableStatus = 'Нет данных';
      const readableType = documentsChecksToLabel[docType] || docType;
      return `Документы: ${readableType} (${readableStatus})`;
    }
    return "Фильтрованные дела";
  };

  // Функция определяет набор колонок таблицы в зависимости от источника данных
  const getTableColumns = () => {
    if (source === 'rainbow') {
      return [
        { key: 'caseCode', title: 'Код дела' },
        { key: 'responsibleExecutor', title: 'Ответственный исполнитель' },
        { key: 'gosb', title: 'ГОСБ' },
        { key: 'currentPeriodColor', title: 'Цвет (тек. период)' },
        ...(featureFlags.hasPreviousReport ? [{ key: 'previousPeriodColor', title: 'Цвет (пред. период)' }] : []),
        { key: 'caseStatus', title: 'Статус дела' },
        { key: 'courtProtectionMethod', title: 'Способ судебной защиты' },
        { key: 'courtReviewingCase', title: 'Суд, рассматривающий дело' }
      ];
    }

    if (source === 'documents') {
      return [
        { key: 'requestCode', title: 'Код запроса', width: '150px' },
        { key: 'caseCode', title: 'Код дела', width: '150px' },
        { key: 'documentType', title: 'Тип документа', width: '180px' },
        { key: 'department', title: 'Подразделение', width: '180px' },
        { key: 'responseEssence', title: 'Суть ответа', width: '250px' },
        { key: 'monitoringStatus', title: 'Статус мониторинга', width: '150px' }
      ];
    }

    // Базовые колонки для дел по срокам
    let baseColumns = [
      { key: 'caseCode', title: 'Код дела' },
      { key: 'responsibleExecutor', title: 'Ответственный исполнитель' },
      { key: 'courtProtectionMethod', title: 'Способ судебной защиты' },
      { key: 'caseStatus', title: 'Статус дела' },
      { key: 'courtReviewingCase', title: 'Суд, рассматривающий дело' }
    ];

    // Добавление специфичных колонок для этапа передачи документов
    if (stage === 'documents_transferred') {
      baseColumns.push(
        { key: 'department', title: 'Категория подразделения' },
        { key: 'documentType', title: 'Документ' },
        { key: 'receiptDate', title: 'Дата поступления документа' },
        { key: 'transferDate', title: 'Дата передачи документа' }
      );
    } else {
      baseColumns.push({ key: 'filingDate', title: 'Дата подачи иска/заявления' });
    }
    return baseColumns;
  };
  
  if (loading) return (
    <PageContainer>
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Загрузка данных...</div>
      </div>
    </PageContainer>
  );

  if (error) return (
    <PageContainer>
      <div className="text-red-600 text-center">{error}</div>
    </PageContainer>
  );

  return (
    <PageContainer>
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-full hover:bg-gray-50 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Вернуться назад
        </button>
      </div>

      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{getCaption()}</h1>
        <p className="text-gray-600">Найдено дел: {cases.length.toLocaleString()}</p>
      </div>

      <ReusableDataTable
        columns={getTableColumns()}
        data={cases}
        isLoading={loading}
        loadingMessage="Загрузка дел..."
        onRowClick={(row) => {
          // Обработчик клика перенаправляет на страницу документа или дела
          if (source === 'documents' && row.caseCode && row.documentType && row.department) {
            navigate(`/document?caseCode=${encodeURIComponent(row.caseCode)}&documentType=${encodeURIComponent(row.documentType)}&department=${encodeURIComponent(row.department)}`);
          }
          else if (row.caseCode) {
            navigate(`/case/${row.caseCode}`);
          }
        }}
      />
    </PageContainer>
  );
}