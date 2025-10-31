// src/pages/Search.tsx
import { PageContainer } from "@/components/PageContainer";

export function Search() {
  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Поиск</h1>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-600">
          Функция поиска будет реализована здесь. 
          Эта страница в настоящее время выделена в боковой панели навигации.
        </p>
      </div>
    </PageContainer>
  );
}