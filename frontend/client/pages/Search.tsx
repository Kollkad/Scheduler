// src/pages/Search.tsx
import { PageContainer } from "@/components/PageContainer";

export function Search() {
  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-text-primary mb-6">Поиск</h1>
      <div className="bg-white rounded-lg border border-border-default p-6">
        <p className="text-text-secondary">
          Функция поиска будет реализована здесь. 
          Эта страница в настоящее время выделена в боковой панели навигации.
        </p>
      </div>
    </PageContainer>
  );
}