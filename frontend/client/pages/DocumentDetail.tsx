// frontend/client/components/DocumentDetail.tsx

import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader, Search, X } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { TabsContainer } from "@/components/TabsContainer";
import { FieldGroup } from "@/components/FieldGroup";
import { CaseService, DocumentDetails } from "@/services/case/caseService";
import { Button } from "@/components/ui/button";
import { Task } from "@/services/api/taskTypes";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { TaskCardList } from "@/components/TaskCardList";

export function DocumentDetail() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [documentData, setDocumentData] = useState<DocumentDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const [relatedTasks, setRelatedTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);

  const transferCode = searchParams.get('transferCode');

  useEffect(() => {
    if (transferCode) {
      loadDocumentData(transferCode);
    } else {
      setError('Код передачи не указан');
      setLoading(false);
    }
  }, [transferCode]);

  useEffect(() => {
    if (documentData) {
      loadRelatedTasks();
    }
  }, [documentData]);

  // Функция загружает данные документа по коду передачи
  const loadDocumentData = async (code: string) => {
    try {
      setLoading(true);
      const data = await CaseService.getDocumentDetails(code);
      
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

  // Получение ответственного исполнителя из general полей
  const getResponsibleExecutor = (): string => {
    if (!documentData?.fieldGroups?.general) return '';
    const executorField = documentData.fieldGroups.general.find(
      (f) => f.label.includes('Ответственный') || f.label.includes('исполнитель')
    );
    return executorField?.value || 'Не указан';
  };

  // Фильтрация полей для группы "Прочее" по поисковому запросу
  const getFilteredOtherFields = () => {
    if (!documentData?.fieldGroups?.other) return [];
    if (!searchTerm.trim()) return documentData.fieldGroups.other;
    
    return documentData.fieldGroups.other.filter((field) =>
      field.label.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  // Функция загружает задачи, связанные с текущим документом по transferCode
  const loadRelatedTasks = async () => {
    if (!documentData) return;
    
    const filters = {
      transferCode: documentData.transferCode
    };
    
    try {
      setTasksLoading(true);
      const response = await apiClient.get<{ 
        success: boolean; 
        tasks: Task[];
        filteredCount: number;
      }>(`${API_ENDPOINTS.TASKS_LIST}?filters=${encodeURIComponent(JSON.stringify(filters))}`);
      
      if (response?.success && response.tasks) {
        setRelatedTasks(response.tasks);
      } else {
        setRelatedTasks([]);
      }
    } catch (err) {
      console.error('Ошибка загрузки связанных задач:', err);
      setRelatedTasks([]);
    } finally {
      setTasksLoading(false);
    }
  };

  // Формирование вкладок для отображения
  const getTabs = () => {
    const tabs = [];
    const filteredOtherFields = getFilteredOtherFields();
    
    // Общая информация
    if (documentData?.fieldGroups?.general && documentData.fieldGroups.general.length > 0) {
      tabs.push({
        id: 'general',
        label: 'Общая информация',
        content: (
          <FieldGroup
            fields={documentData.fieldGroups.general}
            columns={2}
            showAlertIcon={true}
          />
        )
      });
    }
    
    // Даты и сроки
    if (documentData?.fieldGroups?.dates && documentData.fieldGroups.dates.length > 0) {
      tabs.push({
        id: 'dates',
        label: 'Даты и сроки',
        content: (
          <FieldGroup
            fields={documentData.fieldGroups.dates}
            columns={2}
            showAlertIcon={false}
          />
        )
      });
    }
    
    // Финансовые данные
    if (documentData?.fieldGroups?.financial && documentData.fieldGroups.financial.length > 0) {
      tabs.push({
        id: 'financial',
        label: 'Финансовые данные',
        content: (
          <FieldGroup
            fields={documentData.fieldGroups.financial}
            columns={2}
            showAlertIcon={false}
          />
        )
      });
    }
    
    // Судебные данные
    if (documentData?.fieldGroups?.court && documentData.fieldGroups.court.length > 0) {
      tabs.push({
        id: 'court',
        label: 'Судебные данные',
        content: (
          <FieldGroup
            fields={documentData.fieldGroups.court}
            columns={2}
            showAlertIcon={false}
          />
        )
      });
    }
    
    // Прочее с поиском
    if (filteredOtherFields.length > 0 || (documentData?.fieldGroups?.other && documentData.fieldGroups.other.length > 0)) {
      tabs.push({
        id: 'other',
        label: 'Прочее',
        content: (
          <div>
            <div className="relative mb-4 max-w-[50%]">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-tertiary h-4 w-4" />
              <input
                type="text"
                placeholder="Поиск по полям..."
                className="w-full pl-10 pr-10 py-2 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue focus:border-transparent text-text-primary bg-white"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              {searchTerm && (
                <X 
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-text-tertiary h-4 w-4 cursor-pointer hover:text-text-primary"
                  onClick={() => setSearchTerm('')}
                />
              )}
            </div>
            
            {filteredOtherFields.length === 0 && (
              <div className="text-center text-text-secondary py-8">
                Поля не найдены
              </div>
            )}
            
            {filteredOtherFields.length > 0 && (
              <FieldGroup
                fields={filteredOtherFields}
                columns={2}
                showAlertIcon={false}
              />
            )}
          </div>
        )
      });
    }
    
    return tabs;
  };

  if (loading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center h-64">
          <Loader className="h-8 w-8 animate-spin text-blue" />
        </div>
      </PageContainer>
    );
  }

  if (error || !documentData) {
    return (
      <PageContainer>
        <div className="text-center text-red py-8">
          {error || 'Данные документа не найдены'}
        </div>
      </PageContainer>
    );
  }

  const tabs = getTabs();
  const responsibleExecutor = getResponsibleExecutor();

  return (
    <PageContainer>
      <div className="flex items-center justify-between mb-6">
        <Button 
          variant="grayOutline"
          size="rounded"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Вернуться назад
        </Button>
        
        <div className="text-sm text-text-secondary">
          Всего полей: {documentData.totalFields}
        </div>
      </div>

      <div className="mb-4">
        <h1 className="text-2xl font-bold text-text-primary">
          Документ: {documentData.documentType}
        </h1>
      </div>

      <div className="mb-2">
        <p className="text-base text-text-primary">
          Код дела: {documentData.caseCode} • Подразделение: {documentData.department}
        </p>
      </div>

      {responsibleExecutor && (
        <div className="mb-6">
          <p className="text-base text-text-primary">
            Ответственный исполнитель: {responsibleExecutor}
          </p>
        </div>
      )}

      {tabs.length > 0 ? (
        <TabsContainer tabs={tabs} defaultTab={tabs[0]?.id || 'general'} />
      ) : (
        <div className="text-center text-text-secondary py-8">
          Нет данных для отображения
        </div>
      )}
      
      <div className="mt-10">
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          Связанные задачи
        </h2>
        {tasksLoading ? (
          <div className="flex justify-center py-8">
            <Loader className="h-6 w-6 animate-spin text-blue" />
          </div>
        ) : (
          <TaskCardList tasks={relatedTasks} />
        )}
      </div>
    </PageContainer>
  );
}

export default DocumentDetail;
