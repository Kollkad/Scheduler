// src/pages/TermsOfSupport.tsx
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "@/components/PageContainer";
import { RadioButtonGroup } from "@/components/RadioButtonGroup";
import { SegmentedChart } from "@/components/SegmentedChart";
import { TermsOfSupportMeanings } from "@/components/TermsOfSupportMeanings";
import { useAnalysis } from "@/contexts/AnalysisContext";
import {
  lawsuitChecksToLabel, 
  orderChecksToLabel
} from '@/config/chartConfig';
import { transformLawsuitV2Data, transformOrderV2Data, transformDocumentsData } from '@/utils/dataTransform';
import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';

// Константы кэша
const LAWSUIT_CHARTS_CACHE_KEY = 'terms_lawsuit_charts_cache';
const ORDER_CHARTS_CACHE_KEY = 'terms_order_charts_cache';
const DOCUMENTS_CHARTS_CACHE_KEY = 'terms_documents_charts_cache';
const CACHE_TTL = 5 * 60 * 1000;

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

interface ChartsResponse {
    success: boolean;
    data?: any[];
    totalCases?: number;
    totalDocuments?: number;
    message?: string;
  }

export function TermsOfSupport() {
  const [selectedProcess, setSelectedProcess] = useState('lawsuit');
  const [lawsuitData, setLawsuitData] = useState<TransformedTermsGroup[]>(() => 
    transformLawsuitV2Data([])
  );
  const [orderData, setOrderData] = useState<TransformedTermsGroup[]>(() => 
    transformOrderV2Data([])
  );
  const [documentsData, setDocumentsData] = useState<TransformedTermsGroup[]>(() => 
    transformDocumentsData([])
  );
  const [lawsuitTotalCases, setLawsuitTotalCases] = useState(0);
  const [orderTotalCases, setOrderTotalCases] = useState(0);
  const [documentsTotalCount, setDocumentsTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const isMounted = useRef(true);
  
  const { isAnalyzing, termsTrigger } = useAnalysis();

  // Отслеживание монтирования компонента
  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);


  // Функция загрузки данных искового производства
  const loadLawsuitChartData = async (force = false) => {
    try {
      const cached = localStorage.getItem(LAWSUIT_CHARTS_CACHE_KEY);
      if (!force && cached) {
        const parsed = JSON.parse(cached);
        const isExpired = Date.now() - parsed.timestamp > CACHE_TTL;
        if (!isExpired && isMounted.current) {
          setLawsuitData(transformLawsuitV2Data(parsed.data));
          setLawsuitTotalCases(parsed.total || 0);
          return;
        }
      }

      if (isMounted.current) setIsLoading(true);
      const response = await apiClient.get<ChartsResponse>(API_ENDPOINTS.TERMS_V2_LAWSUIT_CHARTS);
      
      if (response.success && isMounted.current) {
        const chartData = response.data || [];
        const total = response.totalCases || 0;
        
        localStorage.setItem(LAWSUIT_CHARTS_CACHE_KEY, JSON.stringify({
          data: chartData,
          total: total,
          timestamp: Date.now()
        }));
        
        setLawsuitData(transformLawsuitV2Data(chartData));
        setLawsuitTotalCases(total);
      }
    } catch (error) {
      console.error('Ошибка загрузки данных искового:', error);
    } finally {
      if (isMounted.current) setIsLoading(false);
    }
  };

  // Функция загрузки данных приказного производства
  const loadOrderChartData = async (force = false) => {
    try {
      const cached = localStorage.getItem(ORDER_CHARTS_CACHE_KEY);
      if (!force && cached) {
        const parsed = JSON.parse(cached);
        const isExpired = Date.now() - parsed.timestamp > CACHE_TTL;
        if (!isExpired && isMounted.current) {
          setOrderData(transformOrderV2Data(parsed.data));
          setOrderTotalCases(parsed.total || 0);
          return;
        }
      }

      if (isMounted.current) setIsLoading(true);
      const response = await apiClient.get<ChartsResponse>(API_ENDPOINTS.TERMS_V2_ORDER_CHARTS);
      
      if (response.success && isMounted.current) {
        const chartData = response.data || [];
        const total = response.totalCases || 0;
        
        localStorage.setItem(ORDER_CHARTS_CACHE_KEY, JSON.stringify({
          data: chartData,
          total: total,
          timestamp: Date.now()
        }));
        
        setOrderData(transformOrderV2Data(chartData));
        setOrderTotalCases(total);
      }
    } catch (error) {
      console.error('Ошибка загрузки данных приказного:', error);
    } finally {
      if (isMounted.current) setIsLoading(false);
    }
  };

  // Функция загрузки данных документов
  const loadDocumentsChartData = async (force = false) => {
    try {
      const cached = localStorage.getItem(DOCUMENTS_CHARTS_CACHE_KEY);
      if (!force && cached) {
        const parsed = JSON.parse(cached);
        const isExpired = Date.now() - parsed.timestamp > CACHE_TTL;
        if (!isExpired && isMounted.current) {
          setDocumentsData(transformDocumentsData(parsed.data));
          setDocumentsTotalCount(parsed.total || 0);
          return;
        }
      }

      if (isMounted.current) setIsLoading(true);
      const response = await apiClient.get<ChartsResponse>(API_ENDPOINTS.DOCUMENTS_CHARTS);
      
      if (response.success && isMounted.current) {
        const chartData = response.data || [];
        const total = response.totalDocuments || 0;
        
        localStorage.setItem(DOCUMENTS_CHARTS_CACHE_KEY, JSON.stringify({
          data: chartData,
          total: total,
          timestamp: Date.now()
        }));
        
        setDocumentsData(transformDocumentsData(chartData));
        setDocumentsTotalCount(total);
      }
    } catch (error) {
      console.error('Ошибка загрузки данных документов:', error);
    } finally {
      if (isMounted.current) setIsLoading(false);
    }
  };

  // Инициализация данных при монтировании
  useEffect(() => {
    // Загрузка из кэша
    const cachedLawsuit = localStorage.getItem(LAWSUIT_CHARTS_CACHE_KEY);
    if (cachedLawsuit && isMounted.current) {
      const parsed = JSON.parse(cachedLawsuit);
      const isExpired = Date.now() - parsed.timestamp > CACHE_TTL;
      if (!isExpired) {
        setLawsuitData(transformLawsuitV2Data(parsed.data));
        setLawsuitTotalCases(parsed.total || 0);
      }
    }

    const cachedOrder = localStorage.getItem(ORDER_CHARTS_CACHE_KEY);
    if (cachedOrder && isMounted.current) {
      const parsed = JSON.parse(cachedOrder);
      const isExpired = Date.now() - parsed.timestamp > CACHE_TTL;
      if (!isExpired) {
        setOrderData(transformOrderV2Data(parsed.data));
        setOrderTotalCases(parsed.total || 0);
      }
    }

    const cachedDocs = localStorage.getItem(DOCUMENTS_CHARTS_CACHE_KEY);
    if (cachedDocs && isMounted.current) {
      const parsed = JSON.parse(cachedDocs);
      const isExpired = Date.now() - parsed.timestamp > CACHE_TTL;
      if (!isExpired) {
        setDocumentsData(transformDocumentsData(parsed.data));
        setDocumentsTotalCount(parsed.total || 0);
      }
    }

    // Фоновая загрузка свежих данных
    setTimeout(() => {
      if (isMounted.current) {
        Promise.allSettled([
          loadLawsuitChartData(),
          loadOrderChartData(),
          loadDocumentsChartData()
        ]);
      }
    }, 100);
  }, []);

  // Обработчик изменения выбранного типа процесса
  const handleProcessChange = (value: string) => {
    setSelectedProcess(value);
  };

  // Обработчик клика по сегменту диаграммы для фильтрации дел
  const handleSegmentClick = async (stage: string, status: string, count: number) => {
    if (count > 0) {
      let technicalStage = '';
      const stageMapping = selectedProcess === 'lawsuit' ? lawsuitChecksToLabel : orderChecksToLabel;
      
      for (const [engName, rusLabel] of Object.entries(stageMapping)) {
        if (rusLabel === stage) {
          technicalStage = engName;
          break;
        }
      }

      navigate(`/filtered-cases?source=terms&process=${selectedProcess}&stage=${encodeURIComponent(technicalStage)}&status=${encodeURIComponent(status)}&count=${count}`);
    }
  };

  // Обработчик клика по сегменту диаграммы документов
  const handleDocumentsSegmentClick = async (documentType: string, status: string, count: number) => {
    if (count > 0) {
      navigate(`/filtered-cases?source=documents&documentType=${encodeURIComponent(documentType)}&status=${encodeURIComponent(status)}&count=${count}`);
    }
  };

  // Эффект для обновления после завершения анализа
  useEffect(() => {
    const refreshAfterAnalysis = async () => {
      if (isAnalyzing) return;
      console.log('Обновление данных сроков после анализа');
      
      // force=true - игнорируем кэш
      await Promise.allSettled([
        loadLawsuitChartData(true),
        loadOrderChartData(true),
        loadDocumentsChartData(true)
      ]);
    };

    refreshAfterAnalysis();
  }, [termsTrigger, isAnalyzing]);

  const currentData = selectedProcess === 'lawsuit' ? lawsuitData : orderData;
  const currentTotalCases = selectedProcess === 'lawsuit' ? lawsuitTotalCases : orderTotalCases;

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">Сроки сопровождения</h1>
        <p className="text-text-secondary">Всего дел: {currentTotalCases.toLocaleString()}</p>
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
      <div className="mt-12 pt-8 border-t border-border">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-text-primary mb-2">Мониторинг документов</h2>
          <p className="text-text-secondary">Всего документов: {documentsTotalCount.toLocaleString()}</p>
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