// src/hooks/useFilterOptions.ts
import { useState, useEffect } from 'react';
import { FilterService } from '@/services';

export const useFilterOptions = () => {
  const [options, setOptions] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Функция загружает опции фильтров для указанных колонок
  const loadOptions = async (columns?: string[]) => {
    console.log('Loading filter options...');
    setLoading(true);
    setError(null);
    
    try {
        const filterOptions = await FilterService.getFilterOptions(columns);
        console.log('Filter options received:', filterOptions);
        setOptions(filterOptions);
        return filterOptions;
    } catch (err) {
        console.error('Error loading options:', err);
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        throw err;
    } finally {
        setLoading(false);
    }
    };

  // Функция возвращает опции для конкретного поля фильтра
  const getOptionsForField = (fieldName: string) => {
    return options[fieldName] || [];
  };

  return {
    options,
    loading,
    error,
    loadOptions,
    getOptionsForField
  };
};