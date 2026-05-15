// frontend/client/components/profile/ProfileTasksTab.tsx

import { useState, useEffect, useMemo } from "react";
import { Loader } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { TaskCardList } from "@/components/tasks/TaskCardList";
import { DefaultChart } from "@/components/DefaultChart";
import { Task } from "@/services/api/taskTypes";
import { TaskFilterButton } from "@/components/tasks/TaskFilterButton";
import type { TaskFilter } from "@/components/tasks/TaskFilterButton";

interface ProfileTasksTabProps {
  userName: string;
}

export function ProfileTasksTab({ userName }: ProfileTasksTabProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [taskFilter, setTaskFilter] = useState<TaskFilter>("all");
  const [selectedTaskText, setSelectedTaskText] = useState<string | null>(null);
  const [selectedTaskTexts, setSelectedTaskTexts] = useState<string[]>([]);

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

  // Все уникальные тексты задач (для фильтрации)
  const taskTextOptions = useMemo(() => {
    const texts = new Set<string>();
    tasks.forEach(t => texts.add(t.taskText || "Без названия"));
    return Array.from(texts).sort();
  }, [tasks]);

  const filteredTasks = useMemo(() => {
    let filtered = tasks;

    // Фильтр по тексту задачи из графика (одиночный)
    if (selectedTaskText) {
      filtered = filtered.filter(t => (t.taskText || "Без названия") === selectedTaskText);
    }

    // Фильтр по текстам задач из чекбоксов
    if (selectedTaskTexts.length > 0) {
      filtered = filtered.filter(t => selectedTaskTexts.includes(t.taskText || "Без названия"));
    }

    // Фильтр по сроку (сортировка)
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const weekLater = new Date(today);
    weekLater.setDate(weekLater.getDate() + 7);

    switch (taskFilter) {
      case "overdue":
        return filtered.filter(t => {
          if (!t.executionDatePlan || t.isCompleted) return false;
          const planDate = new Date(t.executionDatePlan);
          planDate.setHours(0, 0, 0, 0);
          return planDate < today;
        });
      case "today":
        return filtered.filter(t => {
          if (!t.executionDatePlan) return false;
          const planDate = new Date(t.executionDatePlan);
          planDate.setHours(0, 0, 0, 0);
          return planDate.getTime() === today.getTime();
        });
      case "week":
        return filtered.filter(t => {
          if (!t.executionDatePlan) return false;
          const planDate = new Date(t.executionDatePlan);
          planDate.setHours(0, 0, 0, 0);
          return planDate >= today && planDate <= weekLater;
        });
      case "completed":
        return filtered.filter(t => t.isCompleted);
      case "shifted":
        return filtered.filter(t => t.hasOverride && t.shiftName);
      default:
        return filtered;
    }
  }, [tasks, taskFilter, selectedTaskText, selectedTaskTexts]);

  // Данные для графика
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

  // Сброс всех фильтров
  const handleResetAll = () => {
    setSelectedTaskText(null);
    setSelectedTaskTexts([]);
    setTaskFilter("all");
  };

  const hasActiveFilters = selectedTaskText || selectedTaskTexts.length > 0 || taskFilter !== "all";

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader className="h-6 w-6 animate-spin text-blue" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Диаграмма распределения задач */}
      {chartData.length > 0 && (
        <div>
          <DefaultChart 
            data={chartData} 
            onBarClick={(item) => setSelectedTaskText(item.label)} 
          />
        </div>
      )}

      <div>
        {/* Заголовок списка + фильтр */}
        <div className="flex items-center gap-2 mb-1">
          <h3 className="text-lg font-medium text-text-primary">Список задач</h3>
          <TaskFilterButton
            filter={taskFilter}
            onFilterChange={setTaskFilter}
            taskTextOptions={taskTextOptions}
            selectedTaskTexts={selectedTaskTexts}
            onTaskTextsChange={setSelectedTaskTexts}
            onReset={handleResetAll}
          />
        </div>

        {/* Количество задач */}
        <p className="text-sm text-text-primary mb-4">
          Найдено задач: {filteredTasks.length}
          {hasActiveFilters && (
            <button 
              onClick={handleResetAll}
              className="text-xs text-blue hover:underline ml-2"
            >
              Сбросить фильтры
            </button>
          )}
        </p>
      </div>

      {/* Список задач */}
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
