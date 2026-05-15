// frontend/client/pages/Tasks.tsx

import { useState, useEffect, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { PageContainer } from "@/components/PageContainer";
import { SettingsForm } from "@/components/sorter/SettingsForm";
import { ReusableDataTable } from "@/components/tables/ReusableDataTable";
import { tasksTableConfig, mapBackendDataTasks } from "@/config/tableConfig";
import { sorterConfig } from "@/config/sorterConfig";
import { Button } from "@/components/ui/button";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { apiClient } from "@/services/api/client";
import { TaskCardList } from "@/components/tasks/TaskCardList";
import { DefaultChart } from "@/components/DefaultChart";
import { useTableFiltersWithUrl } from "@/hooks/useTableFiltersWithUrl";
import { TaskItem, TasksListResponse } from "@/services/api/taskTypes";

export default function Tasks() {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);

  // Состояния
  const [tasks, setTasks] = useState<TaskItem[]>([]);           // задачи выбранного сотрудника
  const [allTasks, setAllTasks] = useState<TaskItem[]>([]);     // все задачи (для общего графика)
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [filteredCount, setFilteredCount] = useState<number>(0);
  const [reportStatus, setReportStatus] = useState<"idle" | "loading" | "ready">("idle");
  const [viewMode, setViewMode] = useState<"table" | "cards">("table");

  const { sortConfig, filterConfig, onSortChange, onFilterChange } = useTableFiltersWithUrl({
    tableKey: 'tasks'
  });

  const selectedExecutor = filters["responsibleExecutor"] || "";

  // При монтировании загружаем все задачи для общего графика
  useEffect(() => {
    const loadAllTasks = async () => {
      try {
        const url = `${API_ENDPOINTS.TASKS_LIST}?filters=${encodeURIComponent(JSON.stringify({}))}`;
        const response = await apiClient.get<TasksListResponse>(url);
        if (response?.success) {
          setAllTasks(mapBackendDataTasks(response.tasks || []));
        }
      } catch (e) {
        console.error("Ошибка загрузки всех задач:", e);
      }
    };
    loadAllTasks();
  }, []);

  // Данные для графика распределения задач
  // По умолчанию показывает общий график (allTasks).
  // После успешного поиска переключается на задачи сотрудника (tasks).
  const chartData = useMemo(() => {
    const sourceData = reportStatus === "ready" ? tasks : allTasks;
    if (!sourceData.length) return [];

    const taskCountMap = new Map<string, number>();
    sourceData.forEach(task => {
      const taskText = task.taskText || "Без названия";
      taskCountMap.set(taskText, (taskCountMap.get(taskText) || 0) + 1);
    });

    let items = Array.from(taskCountMap.entries()).map(([label, value]) => ({
      label,
      value,
      color: "#86efac",
    }));

    // Сортировка по убыванию количества
    items.sort((a, b) => b.value - a.value);

    // Если больше 10 категорий — объединяем остальные в "Остальные"
    if (items.length > 10) {
      const topItems = items.slice(0, 9);
      const otherValue = items.slice(9).reduce((sum, item) => sum + item.value, 0);
      items = [...topItems, { label: "Остальные", value: otherValue, color: "#86efac" }];
    }

    return items;
  }, [tasks, allTasks, reportStatus]);

  // Количество задач после применения табличных фильтров
  const tableFilteredCount = useMemo(() => {
    if (!filterConfig || tasks.length === 0) return tasks.length;
    
    let filtered = [...tasks];
    
    Object.entries(filterConfig).forEach(([column, values]) => {
      if (values && values.length > 0) {
        filtered = filtered.filter(item => {
          const val = String(item[column] ?? "").toLowerCase();
          return values.some(v => val.includes(String(v).toLowerCase()));
        });
      }
    });
    
    return filtered.length;
  }, [tasks, filterConfig]);

  // Сброс всех фильтров и задач
  const handleClearAll = () => {
    setFilters({});
    setTasks([]);
    setFilteredCount(0);
    setReportStatus("idle");
    sessionStorage.removeItem("last_tasks");
    navigate("/tasks", { replace: true });
  };

  // Переход к деталям задачи при клике
  const handleTaskClick = (task: TaskItem) => {
    if (task.taskCode) {
      navigate(`/task/${task.taskCode}`);
    }
  };

  // Поля формы: только фильтр по исполнителю
  const formFields = sorterConfig.rainbow.fields
    .filter((f) => f.id === "responsibleExecutor")
    .map((f) => ({ ...f, options: [] }));

  const handleFiltersChange = (newFilters: Record<string, string>) => {
    setFilters(newFilters);
  };

  // Поиск задач по выбранному сотруднику
  const handleFindTasks = async () => {
    const executor = filters["responsibleExecutor"];
    if (!executor) return;

    setIsLoading(true);
    setReportStatus("loading");

    try {
      const filtersParam = {
        responsibleExecutor: executor
      };
      const url = `${API_ENDPOINTS.TASKS_LIST}?filters=${encodeURIComponent(JSON.stringify(filtersParam))}`;
      const response = await apiClient.get<TasksListResponse>(url);

      if (response?.success) {
        const mappedTasks = mapBackendDataTasks(response.tasks || []);
        setTasks(mappedTasks);
        setFilteredCount(response.filteredCount || mappedTasks.length);
        setReportStatus("ready");
        sessionStorage.setItem("last_tasks", JSON.stringify(mappedTasks));
        navigate(`/tasks?executor=${encodeURIComponent(executor)}`, { replace: true });
      } else {
        setTasks([]);
        setFilteredCount(0);
        setReportStatus("ready");
      }
    } catch (e) {
      console.error("Ошибка загрузки задач:", e);
      setTasks([]);
      setFilteredCount(0);
      setReportStatus("ready");
    } finally {
      setIsLoading(false);
    }
  };

  // Сохранение задач выбранного сотрудника в Excel
  const handleSaveTasks = async () => {
    if (!selectedExecutor || tasks.length === 0) return;

    try {
      setIsLoading(true);
      
      const blob = await apiClient.downloadFile(
        API_ENDPOINTS.SAVE_TASKS_BY_EXECUTOR,
        { responsibleExecutor: selectedExecutor }
      );
      
      const fileName = `Задачи_${selectedExecutor}_${new Date().toLocaleDateString('ru-RU')}.xlsx`;
      
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);

    } catch (error) {
      console.error('Ошибка сохранения:', error);
      alert(error instanceof Error ? error.message : 'Не удалось сохранить');
    } finally {
      setIsLoading(false);
    }
  };

  // Кнопки формы поиска
  const formButtons = [
    {
      type: "secondary" as const,
      text: "Очистить",
      onClick: handleClearAll,
      onClearAll: handleClearAll,
    },
    {
      type: "primary" as const,
      text: "Найти задачи",
      onClick: handleFindTasks,
    },
    {
      type: "primary" as const,
      text: "Сохранить задачи",
      onClick: handleSaveTasks,
    }
  ];

  // Восстановление состояния из URL и sessionStorage при загрузке страницы
  useEffect(() => {
    const executorFromUrl = searchParams.get("executor");
    if (executorFromUrl) {
      setFilters({ responsibleExecutor: executorFromUrl });

      const savedTasks = sessionStorage.getItem("last_tasks");
      if (savedTasks) {
        try {
          const parsedTasks = JSON.parse(savedTasks);
          setTasks(parsedTasks);
          setFilteredCount(parsedTasks.length);
          setReportStatus("ready");
        } catch (e) {
          console.error("Ошибка восстановления задач:", e);
        }
      }
    }
  }, [location.search]);

  const hasSelectedExecutor = Boolean(filters["responsibleExecutor"]);

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">Задачи сотрудников</h1>
        <p className="text-text-secondary">Выберите сотрудника для просмотра его задач</p>
      </div>

      {/* График распределения задач */}
      {chartData.length > 0 && (
        <div className="mb-6">
          <DefaultChart data={chartData} />
        </div>
      )}

      {/* Форма поиска по сотруднику */}
      <SettingsForm
        title="Поиск задач по сотруднику"
        fields={formFields}
        buttons={formButtons}
        onFiltersChange={handleFiltersChange}
        initialValues={filters}
      />

      {/* Информация о количестве найденных задач и переключатель вида */}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-text-secondary">
          {reportStatus === "ready" && (
            <span>
              Найдено <span className="font-bold">{tableFilteredCount}</span> задач для{" "}
              <span className="font-bold">{selectedExecutor}</span>
            </span>
          )}
        </div>

        <div className="flex gap-2 ml-auto">
          <Button
            variant={viewMode === "table" ? "green" : "grayOutline"}
            size="rounded"
            onClick={() => setViewMode("table")}
          >
            Таблица
          </Button>
          <Button
            variant={viewMode === "cards" ? "green" : "grayOutline"}
            size="rounded"
            onClick={() => setViewMode("cards")}
          >
            Карточки
          </Button>
        </div>
      </div>

      {/* Таблица / карточки задач */}
      <div className="mt-6">
        {reportStatus === "idle" && (
          <div className="text-text-secondary text-center py-6">
            Выберите сотрудника и нажмите "Найти задачи"
          </div>
        )}

        {reportStatus === "loading" && (
          <div className="text-text-secondary text-center py-6">Задачи формируются...</div>
        )}

        {reportStatus === "ready" && viewMode === "table" && (
          <ReusableDataTable
            columns={tasksTableConfig.columns}
            data={tasks.length > 0 ? tasks : []}
            isLoading={isLoading}
            sortConfig={sortConfig}
            onSortChange={onSortChange}
            filterConfig={filterConfig}
            onFilterChange={onFilterChange}
            onRowClick={handleTaskClick}
          />
        )}

        {reportStatus === "ready" && viewMode === "cards" && (
          <TaskCardList tasks={tasks} />
        )}

        {reportStatus === "ready" && tasks.length === 0 && hasSelectedExecutor && (
          <div className="text-text-secondary text-center py-6">Задачи не найдены</div>
        )}
      </div>
    </PageContainer>
  );
}
