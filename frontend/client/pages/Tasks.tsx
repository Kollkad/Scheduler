// frontend/client/pages/Tasks.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "@/components/PageContainer";
import { SettingsForm } from "@/components/sorter/SettingsForm";
import { ReusableDataTable } from "@/components/tables/ReusableDataTable";
import { tasksTableConfig, mapBackendDataTasks } from "@/config/tableConfig";
import { sorterConfig } from "@/config/sorterConfig";
import { Button } from "@/components/ui/button";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { apiClient } from "@/services/api/client";
import { CompactTaskList } from "@/components/CompactTaskList";

type TaskItem = {
  taskCode: string;
  failedCheck: string;
  caseCode: string;
  responsibleExecutor: string;
  caseStage: string;
  taskText: string;
  monitoringStatus: string;
  isCompleted?: boolean;
};

export default function Tasks() {
  const navigate = useNavigate();

  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [selectedExecutor, setSelectedExecutor] = useState<string>("");
  const [filteredCount, setFilteredCount] = useState<number>(0);
  const [reportStatus, setReportStatus] = useState<"idle" | "loading" | "ready">("idle");
  const [viewMode, setViewMode] = useState<"table" | "compact">("table");

  const handleClearAll = () => {
    setFilters({});
    setTasks([]);
    setSelectedExecutor("");
    setFilteredCount(0);
    setReportStatus("idle");
  };

  const handleTaskClick = (task: TaskItem) => {
    if (task.taskCode) {
      navigate(`/task/${task.taskCode}`);
    }
  };

  const formFields = sorterConfig.rainbow.fields
    .filter((f) => f.id === "responsibleExecutor")
    .map((f) => ({ ...f, options: [] }));

  const formButtons = [
    { type: "secondary" as const, text: "Очистить", onClick: handleClearAll, onClearAll: handleClearAll },
    { type: "primary" as const, text: "Найти задачи", onClick: async () => await handleFindTasks() },
  ];

  const handleFiltersChange = (newFilters: Record<string, string>) => {
    setFilters(newFilters);
    setSelectedExecutor(newFilters["responsibleExecutor"] || "");
  };

  const handleFindTasks = async () => {
    const executor = filters["responsibleExecutor"];
    if (!executor) return;

    setIsLoading(true);
    setReportStatus("loading");

    try {
      const url = `${API_ENDPOINTS.TASKS_LIST}?responsibleExecutor=${encodeURIComponent(executor)}`;
      const response = await apiClient.get<{ success: boolean; tasks: TaskItem[]; filteredCount?: number }>(url);

      if (response?.success) {
        const mappedTasks = mapBackendDataTasks(response.tasks || []);
        setTasks(mappedTasks);
        setFilteredCount(response.filteredCount || mappedTasks.length);
        setReportStatus("ready");
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

  const hasSelectedExecutor = Boolean(filters["responsibleExecutor"]);

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Задачи сотрудников</h1>
        <p className="text-gray-600">Выберите сотрудника для просмотра его задач</p>
      </div>

      <SettingsForm
        title="Поиск задач по сотруднику"
        fields={formFields}
        buttons={formButtons}
        onFiltersChange={handleFiltersChange}
      />

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-gray-600">
          {tasks.length > 0 && (
            <>
              <span>
                Найдено <span className="font-bold">{filteredCount}</span> задач для <span className="font-bold">{selectedExecutor}</span>
              </span>
            </>
          )}
        </div>

        <div className="flex gap-2 ml-auto">
          <Button variant={viewMode === "table" ? "green" : "grayOutline"} size="rounded" onClick={() => setViewMode("table")}>
            Таблица
          </Button>
          <Button variant={viewMode === "compact" ? "green" : "grayOutline"} size="rounded" onClick={() => setViewMode("compact")}>
            Компактный вид
          </Button>
        </div>
      </div>

      <div className="mt-6">
        {reportStatus === "idle" && (
          <div className="text-gray-500 text-center py-6">
            Выберите сотрудника и нажмите "Найти задачи"
          </div>
        )}

        {reportStatus === "loading" && (
          <div className="text-gray-500 text-center py-6">Задачи формируются...</div>
        )}

        {reportStatus === "ready" && viewMode === "table" && (
          <ReusableDataTable
            columns={tasksTableConfig.columns}
            data={tasks.length > 0 ? tasks : []}
            isLoading={isLoading}
            onRowClick={handleTaskClick}
          />
        )}

        {reportStatus === "ready" && viewMode === "compact" && (
          <CompactTaskList
            tasks={tasks}
            onTaskClick={handleTaskClick}
            isLoading={isLoading}
            emptyMessage={hasSelectedExecutor ? "Задачи не найдены" : "Выберите сотрудника"}
          />
        )}


        {reportStatus === "ready" && tasks.length === 0 && hasSelectedExecutor && (
          <div className="text-gray-500 text-center py-6">Задачи не найдены</div>
        )}
      </div>
    </PageContainer>
  );
}
