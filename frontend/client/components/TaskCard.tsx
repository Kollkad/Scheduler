// frontend/client/components/TaskCard.tsx

import { Check, CheckCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/utils/dateFormat";

interface TaskCardProps {
  taskCode: string;
  taskText: string;
  reasonText?: string;
  isCompleted?: boolean;
  executionDatePlan?: string;
  executionDateFact?: string;
}

export function TaskCard({
  taskCode,
  taskText,
  reasonText,
  isCompleted,
  executionDatePlan,
  executionDateFact
}: TaskCardProps) {
  const navigate = useNavigate();

  const handleNavigate = () => {
    navigate(`/task/${taskCode}`);
  };

  return (
    <div className="bg-white rounded-lg border border-border p-4 flex flex-col h-full">
      {/* Верхняя часть — заполняет доступное пространство */}
      <div className="flex-1">
        {/* Заголовок с иконкой статуса */}
        <div className="flex items-center gap-2 mb-3">
          {isCompleted ? (
            <CheckCircle className="h-5 w-5 text-green" />
          ) : (
            <Check className="h-5 w-5 text-text-primary" />
          )}
          <span className="text-text-primary font-medium">Задача: {taskCode}</span>
        </div>

        {/* Текст задачи */}
        <div className="text-text-primary text-sm mb-2">{taskText}</div>

        {/* Причина постановки */}
        {reasonText && (
          <div className="text-text-primary text-sm">{reasonText}</div>
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
              {executionDatePlan ? formatDate(executionDatePlan) : "—"}
            </div>
          </div>

          {/* Разделитель */}
          <div className="w-px bg-border" />

          {/* Правая половина - факт */}
          <div className="flex-1 py-2 px-3 text-center bg-bg-default-light-field rounded-r-full">
            <div className="text-text-primary text-sm">
              {executionDateFact ? formatDate(executionDateFact) : "—"}
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