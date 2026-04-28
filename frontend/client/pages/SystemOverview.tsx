// frontend/client/pages/SystemOverview.tsx

import { PageContainer } from "@/components/PageContainer";
import { TabsContainer } from "@/components/TabsContainer";
import { SystemOverviewIntroduction } from "@/components/system-overview/SystemOverviewIntroduction";
import { SystemOverviewRainbow } from "@/components/system-overview/SystemOverviewRainbow";
import { SystemOverviewTerms } from "@/components/system-overview/SystemOverviewTerms";
import { SystemOverviewComparison } from "@/components/system-overview/SystemOverviewComparison";
import { SystemOverviewEmployeeTasks } from "@/components/system-overview/SystemOverviewEmployeeTasks";
import { featureFlags } from '@/config/featureFlags';

export function SystemOverview() {
  const tabs = [
    {
      id: 'introduction',
      label: 'Введение',
      content: <SystemOverviewIntroduction />
    },
    {
      id: 'rainbow',
      label: 'Rainbow',
      content: <SystemOverviewRainbow />
    },
    {
      id: 'terms',
      label: 'Сроки сопровождения',
      content: <SystemOverviewTerms />
    },
    ...(featureFlags.enableComparison ? [{
      id: 'comparison',
      label: 'Сравнение периодов',
      content: <SystemOverviewComparison />
    }] : []),
    {
      id: 'employee-tasks',
      label: 'Задачи сотрудника',
      content: <SystemOverviewEmployeeTasks />
    }
  ];

  return (
    <PageContainer>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary">Планировщик судебных дел</h1>
        <p className="text-text-secondary">Инструкция по работе с системой мониторинга судебных дел</p>
      </div>

      <TabsContainer tabs={tabs} defaultTab="introduction" />
    </PageContainer>
  );
}

