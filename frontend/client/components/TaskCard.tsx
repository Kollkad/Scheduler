// frontend/client/components/TaskCard.tsx

import { Check, CheckCircle, Pencil } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/utils/dateFormat";
import { Task } from "@/services/api/taskTypes";

interface TaskCardProps {
  task: Task;
}

export function TaskCard({ task }: TaskCardProps) {
  const navigate = useNavigate();

  const handleNavigate = () => {
    navigate(`/task/${task.taskCode}`);
  };

  return (
    <div className="bg-white rounded-lg border border-border p-4 flex flex-col h-full">
      {/* Верхняя часть — заполняет доступное пространство */}
      <div className="flex-1">
        {/* Заголовок с иконкой статуса */}
        <div className="flex items-center gap-2 mb-3">
          {task.isCompleted ? (
            <CheckCircle className="h-5 w-5 text-green" />
          ) : (
            <Check className="h-5 w-5 text-text-primary" />
          )}
          {task.hasOverride && (
            <Pencil className="h-4 w-4 text-text-tertiary" />
          )}
          <span className="text-text-primary font-medium">Задача: {task.taskCode}</span>
        </div>

        {/* Текст задачи */}
        <div className="text-text-primary text-sm mb-2">{task.taskText}</div>

        {/* Причина постановки */}
        {task.reasonText && (
          <div className="text-text-primary text-sm">{task.reasonText}</div>
        )}
      </div>

      {/* Нижняя часть — фиксированная, прижата к низу */}
      <div className="mt-4">
        {/* Заголовки над полем дат */}
        <div className="grid grid-cols-2 gap-0 mb-1">
          <div className="text-text-primary text-xs text-left pl-3">
            Дата исполнения (план)
          </div>
          <div className="text-text-primary text-xs text-left pl-3">
            Дата исполнения (факт)
          </div>
        </div>

        {/* Блок дат - полностью круглые края*/}
        <div className="flex rounded-full border border-border overflow-hidden mb-4">
          {/* Левая половина - план */}
          <div className="flex-1 py-2 px-3 text-center rounded-l-full">
            <div className="text-text-primary text-sm">
              {task.executionDatePlan ? formatDate(task.executionDatePlan) : "—"}
            </div>
          </div>

          {/* Разделитель */}
          <div className="w-px bg-border" />

          {/* Правая половина - факт */}
          <div className="flex-1 py-2 px-3 text-center bg-bg-default-light-field rounded-r-full">
            <div className="text-text-primary text-sm">
              {task.executionDateTimeFact ? formatDate(task.executionDateTimeFact) : "—"}
            </div>
          </div>
        </div>

        {/* Кнопка перехода - растянута на всю ширину */}
        <Button variant="green" size="rounded" className="w-full" onClick={handleNavigate}>
          Перейти к деталям
        </Button>
      </div>
    </div>
  );
}