// frontend/client/components/profile/ProfileCasesTab.tsx

import { useState, useEffect, useMemo } from "react";
import { Loader } from "lucide-react";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { CaseCardList } from "@/components/cases/CaseCardList";
import { SortButton } from "@/components/tables/SortButton";

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

interface CasesResponse {
  success: boolean;
  cases: CaseItem[];
  tasks: CaseTask[];
  totalCases: number;
  message: string;
}

interface ProfileCasesTabProps {
  userName: string;
}

export function ProfileCasesTab({ userName }: ProfileCasesTabProps) {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCaseCodes, setSelectedCaseCodes] = useState<string[]>([]);

  useEffect(() => {
    if (!userName) return;

    setLoading(true);
    const url = `${API_ENDPOINTS.CASE_WITH_TASKS}?executor=${encodeURIComponent(userName)}`;
    apiClient.get<CasesResponse>(url)
      .then(data => {
        if (data.success) {
          // Задачи группируются по caseCode
          const tasksByCase = new Map<string, CaseTask[]>();
          data.tasks.forEach(task => {
            const caseCode = (task as any).caseCode;
            if (!tasksByCase.has(caseCode)) tasksByCase.set(caseCode, []);
            tasksByCase.get(caseCode)!.push({
              taskCode: task.taskCode,
              taskText: task.taskText,
              isCompleted: task.isCompleted,
            });
          });

          const enrichedCases = data.cases.map(c => ({
            ...c,
            tasks: tasksByCase.get(c.caseCode) || [],
          }));

          setCases(enrichedCases);
        }
      })
      .catch(() => setCases([]))
      .finally(() => setLoading(false));
  }, [userName]);

  // Все коды дел для фильтрации
  const caseCodeOptions = useMemo(() => {
    return cases.map(c => c.caseCode).sort();
  }, [cases]);

  // Фильтрация
  const filteredCases = useMemo(() => {
    if (selectedCaseCodes.length === 0) return cases;
    return cases.filter(c => selectedCaseCodes.includes(c.caseCode));
  }, [cases, selectedCaseCodes]);

  const hasActiveFilter = selectedCaseCodes.length > 0;

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader className="h-6 w-6 animate-spin text-blue" />
      </div>
    );
  }

  return (
    <div>
      {/* Заголовок + фильтр */}
      <div className="flex items-center gap-2 mb-1">
        <h3 className="text-lg font-medium text-text-primary">Дела</h3>
        <SortButton
          onSortChange={() => {}}
          onFilterChange={setSelectedCaseCodes}
          filterOptions={caseCodeOptions.map(code => ({ value: code, label: code }))}
          selectedFilterValues={selectedCaseCodes}
          isActive={hasActiveFilter}
        />
      </div>

      {/* Количество дел */}
      <p className="text-sm text-text-primary mb-4">
        Найдено дел: {filteredCases.length}
        {hasActiveFilter && (
          <button
            onClick={() => setSelectedCaseCodes([])}
            className="text-xs text-blue hover:underline ml-2"
          >
            Сбросить фильтр
          </button>
        )}
      </p>

      {/* Список дел */}
      {filteredCases.length > 0 ? (
        <CaseCardList cases={filteredCases} />
      ) : (
        <div className="text-center text-text-secondary py-8">
          Нет дел
        </div>
      )}
    </div>
  );
}
