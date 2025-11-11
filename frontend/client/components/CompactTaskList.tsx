// frontend/client/components/CompactTaskList.tsx
import { useState } from "react";

interface CompactTaskListProps {
  tasks: any[];
  onTaskClick: (task: any) => void;
  isLoading?: boolean;
  emptyMessage?: string;
}

export function CompactTaskList({ 
  tasks, 
  onTaskClick, 
  isLoading = false,
  emptyMessage = "Задачи не найдены"
}: CompactTaskListProps) {
  const [hoveredTask, setHoveredTask] = useState<string | null>(null);

  const getStatusColor = (isCompleted?: boolean): string => {
    if (isCompleted) return "#10B981";
    return "#EF4444";
  };

  const truncateText = (text: string, maxLength: number = 120): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="text-gray-600">Загрузка задач...</div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="text-gray-500">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {tasks.map((task, index) => (
        <div
          key={task.taskCode || index}
          className="bg-white rounded-lg border border-gray-200 shadow-sm cursor-pointer transition-all duration-200 hover:shadow-md hover:border-blue-300"
          style={{ borderRadius: '8px', marginBottom: '4px' }}
          onClick={() => onTaskClick(task)}
          onMouseEnter={() => setHoveredTask(task.taskCode)}
          onMouseLeave={() => setHoveredTask(null)}
        >
          <div className="flex items-center px-4 py-3">
            {/* Индикатор статуса */}
            <div 
              className="w-3 h-3 rounded-full mr-4 flex-shrink-0"
              style={{
                backgroundColor: getStatusColor(task.isCompleted)
              }}
            />
            
            {/* Код дела */}
            <div className="w-1/6 pr-4 border-r border-gray-200">
              <span className="text-sm font-medium text-gray-900">
                {task.caseCode || "Не указан"}
              </span>
            </div>
            
            {/* Этап дела */}
            <div className="w-1/5 px-4 border-r border-gray-200">
              <span className="text-sm text-gray-700">
                {task.caseStage || "Не указан"}
              </span>
            </div>
            
            {/* Проваленная проверка */}
            <div className="flex-1 px-4">
              <span className="text-sm text-gray-900">
                {truncateText(task.failedCheck || "Проверка не указана")}
              </span>
            </div>

            {/* Текст задачи */}
            <div className="flex-1 px-4">
              <span className="text-sm text-gray-900">
                {truncateText(task.taskText || "Текст задачи не указан")}
              </span>
            </div>
            
          </div>
        </div>
      ))}
    </div>
  );
}