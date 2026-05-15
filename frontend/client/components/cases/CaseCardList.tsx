// frontend/client/components/cases/CaseCardList.tsx

import { CaseCard } from "@/components/cases/CaseCard";

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

interface CaseCardListProps {
  cases: CaseItem[];
}

export function CaseCardList({ cases }: CaseCardListProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cases.map(caseItem => (
        <CaseCard key={caseItem.caseCode} caseItem={caseItem} />
      ))}
    </div>
  );
}