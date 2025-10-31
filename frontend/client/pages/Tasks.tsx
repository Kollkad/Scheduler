// frontend/client/pages/Tasks.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "@/components/PageContainer";
import { SettingsForm } from "@/components/sorter/SettingsForm";
import { ReusableDataTable } from "@/components/tables/ReusableDataTable";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { apiClient } from "@/services/api/client";
import { sorterConfig } from "@/config/sorterConfig";
import { tasksTableConfig, mapBackendDataTasks } from "@/config/tableConfig";

type TaskItem = {
  taskCode: string;
  taskType: string; 
  caseCode: string;
  responsibleExecutor: string;
  caseStage: string;
  taskText: string;
  monitoringStatus: string;
  isCompleted?: boolean;
  failedChecksCount?: number;
};

export default function Tasks() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [selectedExecutor, setSelectedExecutor] = useState<string>("");
  const [filteredCount, setFilteredCount] = useState<number>(0);

  // Обработчик клика по строке таблицы для перехода к деталям задачи
  const handleRowClick = (task: TaskItem) => {
    if (task.taskCode && task.taskCode !== "Выберите сотрудника и нажмите 'Найти задачи'") {
      navigate(`/task/${task.taskCode}`);
    }
  };

  // Конфигурация полей формы с динамической загрузкой опций
  const formFields = sorterConfig.rainbow.fields
    .filter((f) => f.id === "responsibleExecutor")
    .map((f) => ({ ...f, options: [] }));

  // Конфигурация кнопок формы с обработчиками
  const formButtons = [
    {
      type: "secondary" as const,
      text: "Очистить",
      onClick: () => {
        setFilters({});
        setTasks([]);
        setSelectedExecutor("");
      },
    },
    {
      type: "primary" as const,
      text: "Найти задачи",
      onClick: async () => {
        await handleFindTasks();
      },
    },
  ];

  // Данные по умолчанию для таблицы до поиска
  const defaultTableData = [
    {
      taskCode: "Выберите сотрудника и нажмите 'Найти задачи'", 
      taskType: "-", 
      caseCode: "-",
      responsibleExecutor: "-",
      caseStage: "-",
      taskText: "-",
      monitoringStatus: "-",
    },
  ];

  // Обработчик изменений фильтров в форме
  const handleFiltersChange = (newFilters: Record<string, string>) => {
    setFilters(newFilters);
    setSelectedExecutor(newFilters["responsibleExecutor"] || "");
  };

  // Функция выполняет поиск задач по выбранному исполнителю
  const handleFindTasks = async () => {
    const executor = filters["responsibleExecutor"];
    if (!executor) {
      console.warn("Выберите ответственного исполнителя");
      return;
    }

    setIsLoading(true);
    try {
      const url = `${API_ENDPOINTS.TASKS_LIST}?responsibleExecutor=${encodeURIComponent(executor)}`;
      
      const response = await apiClient.get<{ 
        success: boolean; 
        tasks: TaskItem[]; 
        message?: string;
        filteredCount?: number;    
      }>(url);

      if (response && response.success) {
        const tasksData = response.tasks || [];
        const mappedTasks = mapBackendDataTasks(tasksData);
        const count = response.filteredCount || tasksData.length;
        setFilteredCount(count);
        
        // Формирование данных для таблицы с обработкой отсутствующих значений
        const tableData = mappedTasks.map(task => ({
          taskCode: task.taskCode || "Не указан",
          taskType: task.taskType || "Не указан",
          caseCode: task.caseCode || "Не указан",
          responsibleExecutor: task.responsibleExecutor || executor,
          caseStage: task.caseStage,
          taskText: task.taskText || "Не указано",
          monitoringStatus: task.monitoringStatus,
          isCompleted: task.isCompleted,
          failedChecksCount: task.failedChecksCount
        }));

        setTasks(tableData);
        console.log(`Найдено задач: ${count}`);
      } else {
        console.error("Ошибка при получении задач:", response?.message || "unknown");
        setTasks([]);
        setFilteredCount(0);
      }
    } catch (e) {
      console.error("Ошибка загрузки задач:", e);
      setTasks([]);
      setFilteredCount(0);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Задачи сотрудников</h1>
        <p className="text-gray-600">
          Выберите сотрудника для просмотра его задач
        </p>
      </div>

      <SettingsForm
        title="Поиск задач по сотруднику"
        fields={formFields}
        buttons={formButtons}
        onFiltersChange={handleFiltersChange}
      />

      {/* Блок отображения результатов поиска */}
      {tasks.length > 0 && (
        <div className="mt-4 flex items-center gap-2 text-gray-600">
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          <span>
            Найдено <span className="font-bold">{filteredCount}</span> задач для <span className="font-bold">{selectedExecutor}</span>
          </span>
        </div>
      )}

      <div className="mt-6">
        <ReusableDataTable
          columns={tasksTableConfig.columns}
          data={tasks.length > 0 ? tasks : defaultTableData}
          isLoading={isLoading}
          loadingMessage="Поиск задач..."
          onRowClick={handleRowClick}
        />
      </div>
    </PageContainer>
  );
}