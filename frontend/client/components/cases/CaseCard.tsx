// frontend/client/components/cases/CaseCard.tsx

import { useMemo } from "react";
import { Check, CheckCircle, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { rainbowChartConfig } from "@/config/chartConfig";

interface CaseTask {
  taskCode: string;
  taskText: string;
  isCompleted: boolean;
}

interface CaseItem {
  caseCode: string;
  currentPeriodColor: string;
  stageCode: string;
  responsibleExecutor: string;
  caseStatus: string;
  tasks: CaseTask[];
}

interface CaseCardProps {
  caseItem: CaseItem;
}

export function CaseCard({ caseItem }: CaseCardProps) {
  const navigate = useNavigate();

  const handleCaseClick = () => {
    navigate(`/case/${caseItem.caseCode}`);
  };

  const handleTaskClick = (taskCode: string) => {
    navigate(`/task/${taskCode}`);
  };

  const colorMap = useMemo(() => {
  const map: Record<string, string> = {};
  rainbowChartConfig.items.forEach(item => {
    map[item.label] = item.color;
  });
  return map;
  }, []);

  const dotColor = colorMap[caseItem.currentPeriodColor] || "#D0D0D0";

  return (
    <div className="bg-white rounded-2xl border border-border p-4 flex flex-col h-full">
      {/* Верхняя часть */}
      <div className="flex-1">
        {/* Код дела + цвет */}
        <div className="flex items-center gap-2 mb-2">
          <span
            className="inline-block w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: dotColor, border: "1px solid rgba(0,0,0,0.15)" }}
          />
          <span className="text-text-primary font-medium">{caseItem.caseCode}</span>
        </div>

        {/* Статус дела */}
        <div className="text-text-primary text-sm mb-3">
          Статус дела: {caseItem.caseStatus || "Не указан"}
        </div>

        {/* Задачи дела */}
        {caseItem.tasks.length > 0 && (
          <div className="space-y-1.5 mb-3">
            {caseItem.tasks.map(task => (
              <button
                key={task.taskCode}
                onClick={() => handleTaskClick(task.taskCode)}
                className="w-full flex items-center gap-2 bg-white border border-border rounded-lg px-3 py-1.5 hover:bg-bg-light-grey transition-colors"
              >
                {task.isCompleted ? (
                  <CheckCircle className="h-4 w-4 text-green flex-shrink-0" />
                ) : (
                  <Check className="h-4 w-4 text-text-pimary flex-shrink-0" />
                )}
                <span className="text-sm text-text-primary flex-1 text-left">
                  Задача: {task.taskCode}
                </span>
                <ChevronRight className="h-4 w-4 text-text-pimary flex-shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Кнопка внизу */}
      <Button variant="green" size="rounded" className="w-full mt-2" onClick={handleCaseClick}>
        Перейти к деталям
      </Button>
    </div>
  );
}
