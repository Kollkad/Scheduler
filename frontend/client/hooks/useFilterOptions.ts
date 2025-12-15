// src/hooks/useFilterOptions.ts
import { useState } from 'react';
import { FilterService } from '@/services';

// Кэш фильтров на время сессии, чтобы не дергать эндпоинт повторно
let cachedOptions: Record<string, any[]> | null = null;

export const useFilterOptions = () => {
  const [options, setOptions] = useState<Record<string, any[]>>(cachedOptions || {});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Загружает фильтры с сервера и сохраняет их в кэш
  const loadOptions = async (columns?: string[]) => {
    if (cachedOptions) {
      setOptions(cachedOptions);
      return cachedOptions;
    }

    setLoading(true);
    setError(null);

    try {
      const filterOptions = await FilterService.getFilterOptions(columns);
      cachedOptions = filterOptions; // сохраняем в кэш
      localStorage.setItem('filterOptions', JSON.stringify(filterOptions)); // сохраняем для перезагрузки
      setOptions(filterOptions);
      return filterOptions;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Очищает кэш фильтров
  const clearCache = () => {
    cachedOptions = null;
    setOptions({});
    localStorage.removeItem('filterOptions');
  };

  // Возвращает опции для конкретного поля
  const getOptionsForField = (fieldName: string) => options[fieldName] || [];

  return {
    options,
    loading,
    error,
    loadOptions,
    getOptionsForField,
    clearCache
  };
};

