// frontend/client/components/documents/DocumentCard.tsx

import { Check, CheckCircle, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface DocumentTask {
  taskCode: string;
  taskText: string;
  isCompleted: boolean;
  docTransferCode: string;
}

interface DocumentItem {
  transferCode: string;
  caseCode: string;
  documentType: string;
  department: string;
  responsibleExecutor: string;
  tasks: DocumentTask[];
}

interface DocumentCardProps {
  document: DocumentItem;
}

export function DocumentCard({ document }: DocumentCardProps) {
  const navigate = useNavigate();

  const handleDocumentClick = () => {
    navigate(`/document/${document.transferCode}`);
  };

  const handleTaskClick = (taskCode: string) => {
    navigate(`/task/${taskCode}`);
  };

  return (
    <div className="bg-white rounded-2xl border border-border p-4 flex flex-col h-full">
      <div className="flex-1">
        {/* Код передачи */}
        <div className="text-text-primary font-medium mb-2">{document.transferCode}</div>

        {/* Информация о документе */}
        <div className="text-sm text-text-secondary space-y-0.5 mb-3">
          {document.documentType && (
            <div>Документ: {document.documentType}</div>
          )}
          {document.department && (
            <div>Подразделение: {document.department}</div>
          )}
          {document.caseCode && (
            <div>Код дела: {document.caseCode}</div>
          )}
        </div>

        {/* Задачи документа */}
        {document.tasks.length > 0 && (
          <div className="space-y-1.5 mb-3">
            {document.tasks.map(task => (
              <button
                key={task.taskCode}
                onClick={() => handleTaskClick(task.taskCode)}
                className="w-full flex items-center gap-2 bg-white border border-border rounded-lg px-3 py-1.5 hover:bg-bg-light-grey transition-colors"
              >
                {task.isCompleted ? (
                  <CheckCircle className="h-4 w-4 text-green flex-shrink-0" />
                ) : (
                  <Check className="h-4 w-4 text-text-tertiary flex-shrink-0" />
                )}
                <span className="text-sm text-text-primary flex-1 text-left">
                  Задача: {task.taskCode}
                </span>
                <ChevronRight className="h-4 w-4 text-text-tertiary flex-shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Кнопка внизу */}
      <Button variant="green" size="rounded" className="w-full mt-2" onClick={handleDocumentClick}>
        Перейти к деталям
      </Button>
    </div>
  );
}
