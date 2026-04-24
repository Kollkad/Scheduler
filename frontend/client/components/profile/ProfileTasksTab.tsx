// client/components/profile/ProfileTasksTab.tsx

import { useState, useEffect, useMemo } from "react";
import { Loader } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { TaskCardList } from "@/components/TaskCardList";
import { DefaultChart } from "@/components/DefaultChart";
import { Task } from "@/services/api/taskTypes";

interface ProfileTasksTabProps {
  userName: string;
}

export function ProfileTasksTab({ userName }: ProfileTasksTabProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

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

  // Подготовка данных для диаграммы распределения задач
  const chartData = useMemo(() => {
    if (!tasks.length) return [];

    const taskCountMap = new Map<string, number>();
    tasks.forEach(task => {
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
  }, [tasks]);

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
      <div>
        <p className="text-sm text-text-secondary mb-4">Всего задач: {tasks.length}</p>
      </div>

      {/* Диаграмма распределения задач */}
      {chartData.length > 0 && (
        <div>
          <DefaultChart data={chartData} />
        </div>
      )}

      {/* Список задач */}
      <div>
        <h3 className="text-base font-medium text-text-primary mb-4">Список задач</h3>
        {tasks.length > 0 ? (
          <TaskCardList tasks={tasks} />
        ) : (
          <div className="text-center text-text-secondary py-8">
            У пользователя нет задач
          </div>
        )}
      </div>
    </div>
  );
}
