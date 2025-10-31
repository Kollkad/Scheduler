// src/components/DynamicCaseDetail.tsx
import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { TabsContainer } from "@/components/TabsContainer";
import { FieldGroup } from "@/components/FieldGroup";
import { CaseService, CaseDetails } from "@/services/case/caseService";

export function DynamicCaseDetail() {
  const navigate = useNavigate();
  const { caseCode } = useParams<{ caseCode: string }>();
  const [caseData, setCaseData] = useState<CaseDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (caseCode) {
      loadCaseData(caseCode);
    }
  }, [caseCode]);

  // Функция загружает детальную информацию о деле по коду
  const loadCaseData = async (code: string) => {
    try {
      setLoading(true);
      console.log('Загрузка данных для дела:', code);
      const data = await CaseService.getCaseDetails(code);
      console.log('Данные получены:', data);
      
      // Проверка выполняется для обеспечения корректности полученных данных
      if (data && data.success) {
        setCaseData(data);
      } else {
        throw new Error('Данные не найдены или некорректны');
      }
    } catch (err) {
      console.error('Ошибка загрузки:', err);
      setError(err instanceof Error ? err.message : 'Ошибка загрузки данных');
      setCaseData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center h-64">
          <Loader className="h-8 w-8 animate-spin" />
        </div>
      </PageContainer>
    );
  }

  if (error || !caseData) {
    return (
      <PageContainer>
        <div className="text-center text-red-600">
          {error || 'Данные не найдены'}
        </div>
      </PageContainer>
    );
  }

  // Отладочная информация о структуре данных полей
  console.log('Структура fieldGroups:', caseData.fieldGroups);

  // Формирование вкладок из сгруппированных полей для навигации по данным дела
  const tabs = Object.entries(caseData.fieldGroups).map(([groupName, fields]) => ({
    id: groupName,
    label: getGroupLabel(groupName),
    content: (
      <FieldGroup
        fields={fields}
        columns={2}
      />
    )
  }));

  return (
    <PageContainer>
      {/* Блок навигации и отображения общего количества полей */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-full hover:bg-gray-50 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Вернуться назад
        </button>
        
        <div className="text-sm text-gray-500">
          Всего полей: {caseData.totalFields}
        </div>
      </div>

      {/* Заголовок с основной информацией о деле */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Дело: {caseData.caseCode}
        </h1>
        {/* Условное отображение информации о колонке поиска */}
        {caseData.foundInColumn && (
          <p className="text-sm text-gray-500 mt-1">
            Найдено в колонке: {caseData.foundInColumn}
          </p>
        )}
      </div>

      {/* Динамические вкладки для отображения сгруппированных данных дела */}
      {tabs.length > 0 ? (
        <TabsContainer tabs={tabs} defaultTab={tabs[0]?.id || 'general'} />
      ) : (
        <div className="text-center text-gray-500 py-8">
          Нет данных для отображения
        </div>
      )}
    </PageContainer>
  );
}

// Функция возвращает читаемые названия для групп полей дела
function getGroupLabel(groupKey: string): string {
  const labels: Record<string, string> = {
    'general': 'Общая информация',
    'court': 'Судебные данные',
    'financial': 'Финансовые данные',
    'dates': 'Даты и сроки',
    'other': 'Прочие данные'
  };
  return labels[groupKey] || groupKey;
}

export default DynamicCaseDetail;