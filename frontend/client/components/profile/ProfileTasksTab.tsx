// frontend/client/components/profile/ProfileTasksTab.tsx

import { useState, useEffect, useMemo } from "react";
import { Loader } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { TaskCardList } from "@/components/tasks/TaskCardList";
import { DefaultChart } from "@/components/DefaultChart";
import { Task } from "@/services/api/taskTypes";
import { TaskFilterDropdown } from "@/components/tasks/TaskFilterDropdown";
import type { TaskFilter } from "@/components/tasks/TaskFilterDropdown";

interface ProfileTasksTabProps {
  userName: string;
}

export function ProfileTasksTab({ userName }: ProfileTasksTabProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [taskFilter, setTaskFilter] = useState<TaskFilter>("all");

  // Загрузка задач при изменении имени пользователя
  useEffect(() => {
    if (!userName) return;
    
    setLoading(true);
    const filters = { responsibleExecutor: userName };
    
    apiClient.get<{ success: boolean; tasks: Task[]; filteredCount: number }>(
      `${API_ENDPOINTS.TASKS_LIST}?filters=${encodeURIComponent(JSON.stringify(filters))}`
    )
      .then(response => {
        if (response?.success && response.tasks) {
          setTasks(response.tasks);
        } else {
          setTasks([]);
        }
      })
      .catch(() => setTasks([]))
      .finally(() => setLoading(false));
  }, [userName]);

  // Фильтрация задач
  const filteredTasks = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const weekLater = new Date(today);
    weekLater.setDate(weekLater.getDate() + 7);

    switch (taskFilter) {
      case "overdue":
        return tasks.filter(t => {
          if (!t.executionDatePlan || t.isCompleted) return false;
          const planDate = new Date(t.executionDatePlan);
          planDate.setHours(0, 0, 0, 0);
          return planDate < today;
        });
      case "today":
        return tasks.filter(t => {
          if (!t.executionDatePlan) return false;
          const planDate = new Date(t.executionDatePlan);
          planDate.setHours(0, 0, 0, 0);
          return planDate.getTime() === today.getTime();
        });
      
      case "week":
        return tasks.filter(t => {
          if (!t.executionDatePlan) return false;
          const planDate = new Date(t.executionDatePlan);
          planDate.setHours(0, 0, 0, 0);
          return planDate >= today && planDate <= weekLater;
        });
      
      case "completed":
        return tasks.filter(t => t.isCompleted);
      
      case "shifted":
        return tasks.filter(t => t.hasOverride && t.shiftName);
      
      default:
        return tasks;
    }
  }, [tasks, taskFilter]);

  // Подготовка данных для диаграммы распределения задач
  const chartData = useMemo(() => {
    if (!filteredTasks.length) return [];

    const taskCountMap = new Map<string, number>();
    filteredTasks.forEach(task => {
      const taskText = task.taskText || "Без названия";
      taskCountMap.set(taskText, (taskCountMap.get(taskText) || 0) + 1);
    });

    let items = Array.from(taskCountMap.entries()).map(([label, value]) => ({
      label,
      value,
      color: "#86efac",
    }));

    items.sort((a, b) => b.value - a.value);

    if (items.length > 10) {
      const topItems = items.slice(0, 9);
      const otherValue = items.slice(9).reduce((sum, item) => sum + item.value, 0);
      items = [...topItems, { label: "Остальные", value: otherValue, color: "#86efac" }];
    }

    return items;
  }, [filteredTasks]);

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader className="h-6 w-6 animate-spin text-blue" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Статистика */}
      <p className="text-sm text-text-secondary mb-4">
        Всего задач: {tasks.length}
        {taskFilter !== "all" && ` (показано: ${filteredTasks.length})`}
      </p>

      {/* Диаграмма распределения задач */}
      {chartData.length > 0 && (
        <div>
          <DefaultChart data={chartData} />
        </div>
      )}

      {/* Список задач */}
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-base font-medium text-text-primary">Список задач</h3>
        <TaskFilterDropdown value={taskFilter} onChange={setTaskFilter} />
      </div>

      {filteredTasks.length > 0 ? (
        <TaskCardList tasks={filteredTasks} />
      ) : (
        <div className="text-center text-text-secondary py-8">
          Нет задач по выбранному фильтру
        </div>
      )}
    </div>
  );
}
