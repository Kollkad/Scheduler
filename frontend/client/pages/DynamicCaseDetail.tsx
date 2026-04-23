// frontend/client/components/DynamicCaseDetail.tsx

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader, Search, X } from "lucide-react";
import { PageContainer } from "@/components/PageContainer";
import { TabsContainer } from "@/components/TabsContainer";
import { FieldGroup } from "@/components/FieldGroup";
import { CaseService, CaseDetails, CaseField } from "@/services/case/caseService";
import { Button } from "@/components/ui/button";
import { CaseLifecycleTimeline } from "@/components/ui/CaseLifecycleTimeline";
import { TaskCardList } from "@/components/TaskCardList";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { Task } from "@/services/api/taskTypes";

export function DynamicCaseDetail() {
  const navigate = useNavigate();
  const { caseCode } = useParams<{ caseCode: string }>();
  const [caseData, setCaseData] = useState<CaseDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const [relatedTasks, setRelatedTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);

  useEffect(() => {
    if (caseCode) {
      loadCaseData(caseCode);
      loadRelatedTasks(caseCode);
    }
  }, [caseCode]);

  // Функция загружает детальную информацию о деле по коду
  const loadCaseData = async (code: string) => {
    try {
      setLoading(true);
      const data = await CaseService.getCaseDetails(code);
      
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


  // Получение ответственного исполнителя из general полей
  const getResponsibleExecutor = (): string => {
    if (!caseData?.fieldGroups?.general) return '';
    const executorField = caseData.fieldGroups.general.find(
      (f) => f.label.includes('Ответственный') || f.label.includes('исполнитель')
    );
    return executorField?.value || 'Не указан';
  };

  // Получение цвета радуги
  const getRainbowColor = (): string => {
    return caseData?.rainbowColor || '';
  };

  // Фильтрация полей для группы "Прочее" по поисковому запросу
  const getFilteredOtherFields = (): CaseField[] => {
    if (!caseData?.fieldGroups?.other) return [];
    if (!searchTerm.trim()) return caseData.fieldGroups.other;
    
    return caseData.fieldGroups.other.filter((field) =>
      field.label.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  // Функция загружает задачи, связанные с текущим делом
  const loadRelatedTasks = async (code: string) => {
    try {
      setTasksLoading(true);
      const filters = {
        caseCode: code
      };
      const response = await apiClient.get<{ 
        success: boolean; 
        tasks: Task[];
        filteredCount: number;
      }>(`${API_ENDPOINTS.TASKS_LIST}?filters=${encodeURIComponent(JSON.stringify(filters))}`);
      
      if (response?.success && response.tasks) {
        setRelatedTasks(response.tasks);
      }
    } catch (err) {
      console.error('Ошибка загрузки связанных задач:', err);
      setRelatedTasks([]);
    } finally {
      setTasksLoading(false);
    }
  };

  // Определение типа производства по данным дела
  const getProductionType = (): 'lawsuit' | 'courtOrder' => {
    // Проверка типа дела по полям в general или other
    if (!caseData?.fieldGroups?.general) return 'lawsuit';
    
    const productionTypeField = caseData.fieldGroups.general.find(
      (f) => f.label === 'Способ судебной защиты'
    );
    
    const productionTypeValue = productionTypeField?.value?.toLowerCase() || '';
    
    if (productionTypeValue.includes('приказ') || productionTypeValue.includes('court order')) {
      return 'courtOrder';
    }
    
    return 'lawsuit';
  };

  // Формирование вкладок для отображения
  const getTabs = () => {
    const tabs = [];
    const filteredOtherFields = getFilteredOtherFields();
    
    if (caseData?.fieldGroups?.general && caseData.fieldGroups.general.length > 0) {
      tabs.push({
        id: 'general',
        label: 'Общая информация',
        content: (
          <FieldGroup
            fields={caseData.fieldGroups.general}
            columns={2}
            showAlertIcon={true}
          />
        )
      });
    }
    
    if (caseData?.fieldGroups?.dates && caseData.fieldGroups.dates.length > 0) {
      tabs.push({
        id: 'dates',
        label: 'Даты и сроки',
        content: (
          <FieldGroup
            fields={caseData.fieldGroups.dates}
            columns={2}
            showAlertIcon={false}
          />
        )
      });
    }
    
    if (caseData?.fieldGroups?.financial && caseData.fieldGroups.financial.length > 0) {
      tabs.push({
        id: 'financial',
        label: 'Финансовые данные',
        content: (
          <FieldGroup
            fields={caseData.fieldGroups.financial}
            columns={2}
            showAlertIcon={false}
          />
        )
      });
    }
    
    if (caseData?.fieldGroups?.court && caseData.fieldGroups.court.length > 0) {
      tabs.push({
        id: 'court',
        label: 'Судебные данные',
        content: (
          <FieldGroup
            fields={caseData.fieldGroups.court}
            columns={2}
            showAlertIcon={false}
          />
        )
      });
    }
    
    if (filteredOtherFields.length > 0 || (caseData?.fieldGroups?.other && caseData.fieldGroups.other.length > 0)) {
      tabs.push({
        id: 'other',
        label: 'Прочее',
        content: (
          <div>
            {/* Поле поиска для группы "Прочее" - половина ширины */}
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
            
            {/* Сообщение об отсутствии результатов */}
            {filteredOtherFields.length === 0 && (
              <div className="text-center text-text-secondary py-8">
                Поля не найдены
              </div>
            )}
            
            {/* Группа полей с отфильтрованными данными */}
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

  if (error || !caseData) {
    return (
      <PageContainer>
        <div className="text-center text-red py-8">
          {error || 'Данные не найдены'}
        </div>
      </PageContainer>
    );
  }

  const tabs = getTabs();
  const responsibleExecutor = getResponsibleExecutor();
  const rainbowColor = getRainbowColor();

  return (
    <PageContainer>
      {/* Кнопка назад */}
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
          Всего полей: {caseData.totalFields}
        </div>
      </div>

      {/* Заголовок дела */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-text-primary">
          Дело: {caseData.caseCode}
        </h1>
      </div>

      {/* Подзаголовки */}
      <div className="mb-6 space-y-1">
        {responsibleExecutor && (
          <p className="text-base text-text-primary">
            Ответственный исполнитель: {responsibleExecutor}
          </p>
        )}
        {rainbowColor && (
          <p className="text-base text-text-primary">
            Цвет в радуге: {rainbowColor}
          </p>
        )}
      </div>

      {/* Жизненная линия дела */}
      {caseData.stageCode && (
        <div className="mb-8">
          <CaseLifecycleTimeline 
            stageCode={caseData.stageCode} 
            productionType={getProductionType()}
          />
        </div>
      )}

      {/* Вкладки с группами полей */}
      {tabs.length > 0 ? (
        <TabsContainer tabs={tabs} defaultTab={tabs[0]?.id || 'general'} />
      ) : (
        <div className="text-center text-text-secondary py-8">
          Нет данных для отображения
        </div>
      )}
      
      {/* Блок связанных задач */}
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

export default DynamicCaseDetail;