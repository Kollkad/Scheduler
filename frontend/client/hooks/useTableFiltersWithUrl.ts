// frontend/client/hooks/useTableFiltersWithUrl.ts
import { useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

interface FilterConfig {
  [columnKey: string]: string[];
}

interface UseTableFiltersWithUrlOptions {
  tableKey: string; // Уникальный идентификатор таблицы для формирования ключей в URL (например, 'tasks', 'cases')
  defaultSort?: { key: string; direction: 'asc' | 'desc' } | null;
  defaultFilters?: FilterConfig;
}

interface UseTableFiltersWithUrlReturn {
  sortConfig: { key: string; direction: 'asc' | 'desc' } | null;
  filterConfig: FilterConfig;
  onSortChange: (newSortConfig: { key: string; direction: 'asc' | 'desc' } | null) => void;
  onFilterChange: (newFilterConfig: FilterConfig) => void;
}

export function useTableFiltersWithUrl({
  tableKey,
  defaultSort = null,
  defaultFilters = {}
}: UseTableFiltersWithUrlOptions): UseTableFiltersWithUrlReturn {
  const location = useLocation();
  const navigate = useNavigate();

  // Парсинг параметров из строки запроса URL
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);

  // Чтение параметра сортировки из URL
  const sortParam = searchParams.get(`${tableKey}_sort`);
  const sortDirectionParam = searchParams.get(`${tableKey}_sort_dir`);
  
  const sortConfig = useMemo(() => {
    if (sortParam && sortDirectionParam) {
      return { key: sortParam, direction: sortDirectionParam as 'asc' | 'desc' };
    }
    return defaultSort;
  }, [sortParam, sortDirectionParam, defaultSort]);

  // Чтение параметра фильтров из URL (JSON строка в encodeURIComponent)
  const filterParam = searchParams.get(`${tableKey}_filters`);
  const filterConfig = useMemo(() => {
    if (filterParam) {
      try {
        return JSON.parse(decodeURIComponent(filterParam));
      } catch {
        return defaultFilters;
      }
    }
    return defaultFilters;
  }, [filterParam, defaultFilters]);

  // Функция обновления параметров в URL без перезагрузки страницы
  const updateUrl = useCallback((newSortConfig: typeof sortConfig, newFilterConfig: FilterConfig) => {
    const params = new URLSearchParams(location.search);
    
    // Обновление параметров сортировки
    if (newSortConfig) {
      params.set(`${tableKey}_sort`, newSortConfig.key);
      params.set(`${tableKey}_sort_dir`, newSortConfig.direction);
    } else {
      params.delete(`${tableKey}_sort`);
      params.delete(`${tableKey}_sort_dir`);
    }
    
    // Обновление параметров фильтрации
    if (Object.keys(newFilterConfig).length > 0) {
      params.set(`${tableKey}_filters`, encodeURIComponent(JSON.stringify(newFilterConfig)));
    } else {
      params.delete(`${tableKey}_filters`);
    }
    
    // Замена URL без добавления записи в историю браузера
    navigate(`${location.pathname}?${params.toString()}`, { replace: true });
  }, [tableKey, location.pathname, location.search, navigate]);

  // Обработчик изменения сортировки
  const onSortChange = useCallback((newSortConfig: { key: string; direction: 'asc' | 'desc' } | null) => {
    updateUrl(newSortConfig, filterConfig);
  }, [updateUrl, filterConfig]);

  // Обработчик изменения фильтров
  const onFilterChange = useCallback((newFilterConfig: FilterConfig) => {
    updateUrl(sortConfig, newFilterConfig);
  }, [updateUrl, sortConfig]);

  return {
    sortConfig,
    filterConfig,
    onSortChange,
    onFilterChange
  };
}

