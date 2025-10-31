// src/components/DocumentDetail.tsx
import { useState, useEffect } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { TabsContainer } from "@/components/TabsContainer";
import { FieldGroup } from "@/components/FieldGroup";
import { CaseService, DocumentDetails } from "@/services/case/caseService";

export function DocumentDetail() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [documentData, setDocumentData] = useState<DocumentDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const caseCode = searchParams.get('caseCode');
  const documentType = searchParams.get('documentType');
  const department = searchParams.get('department');

  useEffect(() => {
    if (caseCode && documentType && department) {
      loadDocumentData(caseCode, documentType, department);
    }
  }, [caseCode, documentType, department]);

  // Функция загружает данные документа по указанным параметрам
  const loadDocumentData = async (code: string, type: string, dept: string) => {
    try {
      setLoading(true);
      console.log('Загрузка данных для документа:', { code, type, dept });
      const data = await CaseService.getDocumentDetails(code, type, dept);
      console.log('Данные документа получены:', data);
      
      if (data && data.success) {
        setDocumentData(data);
      } else {
        throw new Error('Данные документа не найдены или некорректны');
      }
    } catch (err) {
      console.error('Ошибка загрузки документа:', err);
      setError(err instanceof Error ? err.message : 'Ошибка загрузки данных документа');
      setDocumentData(null);
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

  if (error || !documentData) {
    return (
      <PageContainer>
        <div className="text-center text-red-600">
          {error || 'Данные документа не найдены'}
        </div>
      </PageContainer>
    );
  }

  // Создание групп полей для организации данных документа
  const fieldGroups = createDocumentFieldGroups(documentData.document);

  // Формирование вкладок из сгруппированных полей для отображения
  const tabs = Object.entries(fieldGroups).map(([groupName, fields]) => ({
    id: groupName,
    label: getDocumentGroupLabel(groupName),
    content: (
      <FieldGroup
        fields={fields}
        columns={2}
      />
    )
  }));

  return (
    <PageContainer>
      {/* Блок навигации и информации о количестве полей */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-full hover:bg-gray-50 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Вернуться назад
        </button>
        
        <div className="text-sm text-gray-500">
          Всего полей: {Object.keys(documentData.document).length}
        </div>
      </div>

      {/* Заголовок с основной информацией о документе */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Документ: {documentData.documentType}
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Код дела: {documentData.caseCode} • Подразделение: {documentData.department}
        </p>
      </div>

      {/* Контейнер с вкладками для отображения сгруппированных данных */}
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

// Функция группирует поля документа по категориям для структурированного отображения
function createDocumentFieldGroups(document: Record<string, any>) {
  const groups: Record<string, any[]> = {
    'general': [],
    'dates': [],
    'status': [],
    'other': []
  };

  // Цикл перебирает все поля документа и распределяет их по соответствующим группам
  Object.entries(document).forEach(([key, value]) => {
    const field = {
      id: key,
      label: key,
      value: value,
      type: getFieldType(value)
    };

    // Распределение полей по группам на основе ключевых слов в названиях
    if (key.toLowerCase().includes('date') || key.toLowerCase().includes('дата')) {
      groups.dates.push(field);
    } else if (key.toLowerCase().includes('status') || key.toLowerCase().includes('статус')) {
      groups.status.push(field);
    } else if (['caseCode', 'document', 'department', 'requestCode'].includes(key)) {
      groups.general.push(field);
    } else {
      groups.other.push(field);
    }
  });

  // Фильтрация удаляет пустые группы для чистого отображения
  return Object.fromEntries(
    Object.entries(groups).filter(([_, fields]) => fields.length > 0)
  );
}

// Функция определяет тип значения поля для корректного отображения
function getFieldType(value: any): 'text' | 'number' | 'date' | 'boolean' | 'currency' {
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  if (typeof value === 'string' && !isNaN(Date.parse(value))) return 'date';
  return 'text';
}

// Функция возвращает читаемые названия для групп полей документа
function getDocumentGroupLabel(groupKey: string): string {
  const labels: Record<string, string> = {
    'general': 'Общая информация',
    'dates': 'Даты и сроки',
    'status': 'Статусы мониторинга',
    'other': 'Прочие данные'
  };
  return labels[groupKey] || groupKey;
}

export default DocumentDetail;