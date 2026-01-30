// src/pages/TermsOfSupport.tsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "@/components/PageContainer";
import { RadioButtonGroup } from "@/components/RadioButtonGroup";
import { SegmentedChart } from "@/components/SegmentedChart";
import { TermsOfSupportMeanings } from "@/components/TermsOfSupportMeanings";
import { ReusableDataTable } from "@/components/tables/ReusableDataTable";
import { useAnalysis } from "@/contexts/AnalysisContext";
import { 
  lawsuitTermsV2Config, 
  orderTermsV2Config, 
  documentsChartConfig,
  lawsuitChecksToLabel, 
  orderChecksToLabel,
  documentsChecksToLabel 
} from '@/config/chartConfig';
import { termsTableConfig } from '@/config/tableConfig'; 
import { transformLawsuitV2Data, transformOrderV2Data, transformDocumentsData } from '@/utils/dataTransform';
import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';

// Опции для выбора типа процесса
const processOptions = [
  {
    id: 'lawsuit',
    label: 'Описание процесса искового производства в суде общей юрисдикции',
    value: 'lawsuit'
  },
  {
    id: 'order',
    label: 'Описание процесса приказного производства в мировом суде', 
    value: 'order'
  }
];

// Интерфейс для преобразованных данных групп сроков
interface TransformedTermsGroup {
  title: string;
  segments: Array<{
    name: string;
    label: string;
    value: number;
    color: string;
  }>;
  total: number;
}

export function TermsOfSupport() {
  const [selectedProcess, setSelectedProcess] = useState('lawsuit');
  const [lawsuitData, setLawsuitData] = useState<TransformedTermsGroup[]>([]);
  const [orderData, setOrderData] = useState<TransformedTermsGroup[]>([]);
  const [documentsData, setDocumentsData] = useState<TransformedTermsGroup[]>([]);
  const [lawsuitTotalCases, setLawsuitTotalCases] = useState(0);
  const [orderTotalCases, setOrderTotalCases] = useState(0);
  const [documentsTotalCount, setDocumentsTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  
  const { 
    termsV2LawsuitResult, 
    termsV2OrderResult, 
    termsV2LawsuitChartsResult,
    termsV2OrderChartsResult,
    documentsChartsResult,
    isAnalyzing 
  } = useAnalysis();

  // Установка начальных данных из конфигурации при монтировании компонента
  useEffect(() => {
    const defaultLawsuitData = transformLawsuitV2Data([]);
    const defaultOrderData = transformOrderV2Data([]);
    const defaultDocumentsData = transformDocumentsData([]);
    
    setLawsuitData(defaultLawsuitData);
    setOrderData(defaultOrderData);
    setDocumentsData(defaultDocumentsData);
  }, []);

  // Эффект загружает данные из контекста анализа для всех типов процессов
useEffect(() => {
  // Если данные для диаграмм еще не загружены - выходим
  if (!termsV2LawsuitChartsResult && !termsV2OrderChartsResult && !documentsChartsResult) {
    return;
  }
  const extractDataArray = (res: any) => {
    if (!res) return [];
    if (Array.isArray(res)) return res;
    if (res.data && Array.isArray(res.data)) return res.data;
    return [];
  };

  // Обработка данных для искового производства
  if (termsV2LawsuitChartsResult) {
    const lawsuitRaw = extractDataArray(termsV2LawsuitChartsResult);
    if (lawsuitRaw.length > 0) {
      setLawsuitData(transformLawsuitV2Data(lawsuitRaw));
      setLawsuitTotalCases(termsV2LawsuitChartsResult.total || 0);
      console.log('Set lawsuit total cases:', termsV2LawsuitChartsResult.total);
    }
  }

  // Обработка данных для приказного производства
  if (termsV2OrderChartsResult) {
    const orderRaw = extractDataArray(termsV2OrderChartsResult);
    if (orderRaw.length > 0) {
      setOrderData(transformOrderV2Data(orderRaw));
      setOrderTotalCases(termsV2OrderChartsResult.total || 0);
      console.log('Set order total cases:', termsV2OrderChartsResult.total);
    }
  }

  // Обработка данных для документов
  if (documentsChartsResult) {
    const documentsRaw = extractDataArray(documentsChartsResult);
    if (documentsRaw.length > 0) {
      setDocumentsData(transformDocumentsData(documentsRaw));
      setDocumentsTotalCount(documentsChartsResult.total || 0);
      console.log('Set documents total count:', documentsChartsResult.total);
    }
  }
}, [
  termsV2LawsuitChartsResult, 
  termsV2OrderChartsResult,
  documentsChartsResult 
  // Убрал termsV2LawsuitResult и termsV2OrderResult - они не нужны здесь
]);

  // Обработчик изменения выбранного типа процесса
  const handleProcessChange = (value: string) => {
    setSelectedProcess(value);
  };

  // Обработчик клика по сегменту диаграммы для фильтрации дел
  const handleSegmentClick = async (stage: string, status: string, count: number) => {
    if (count > 0) {
      // Поиск технического имени этапа для соответствующего процесса
      let technicalStage = '';
      const stageMapping = selectedProcess === 'lawsuit' ? lawsuitChecksToLabel : orderChecksToLabel;
      
      for (const [engName, rusLabel] of Object.entries(stageMapping)) {
        if (rusLabel === stage) {
          technicalStage = engName;
          break;
        }
      }

      const technicalStatus = status;

      navigate(`/filtered-cases?source=terms&process=${selectedProcess}&stage=${encodeURIComponent(technicalStage)}&status=${encodeURIComponent(technicalStatus)}&count=${count}`);
    }
  };

  // Обработчик клика по сегменту диаграммы документов
  const handleDocumentsSegmentClick = async (documentType: string, status: string, count: number) => {
    if (count > 0) {
      navigate(`/filtered-cases?source=documents&documentType=${encodeURIComponent(documentType)}&status=${encodeURIComponent(status)}&count=${count}`);
    }
  };

  const currentData = selectedProcess === 'lawsuit' ? lawsuitData : orderData;
  const currentTotalCases = selectedProcess === 'lawsuit' ? lawsuitTotalCases : orderTotalCases;

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Сроки сопровождения</h1>
        <p className="text-gray-600">Всего дел: {currentTotalCases.toLocaleString()}</p>
        {isAnalyzing && <p className="text-blue-500">Идет анализ...</p>}
        {isLoading && <p className="text-blue-500">Загрузка данных...</p>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div>
          <RadioButtonGroup
            options={[processOptions[0]]}
            value={selectedProcess}
            onChange={handleProcessChange}
            name="processType"
          />
        </div>
        <div>
          <RadioButtonGroup
            options={[processOptions[1]]}
            value={selectedProcess} 
            onChange={handleProcessChange} 
            name="processType"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        <div className="space-y-4">
          <SegmentedChart 
            data={currentData} 
            onSegmentClick={handleSegmentClick}
          />
        </div>
        
        <div className="space-y-4">
          <TermsOfSupportMeanings/>
        </div>
      </div>

      {/* Раздел мониторинга документов */}
      <div className="mt-12 pt-8 border-t border-gray-200">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-2">Мониторинг документов</h2>
          <p className="text-gray-600">Всего документов: {documentsTotalCount.toLocaleString()}</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-4">
            <SegmentedChart 
              data={documentsData} 
              onSegmentClick={handleDocumentsSegmentClick}
            />
          </div>
          
          <div className="space-y-4">
            {/* Резервный блок для будущего контента */}
          </div>
        </div>
      </div>
    </PageContainer>
  );
}