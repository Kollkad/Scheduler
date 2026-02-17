// src/hooks/useCaseSearch.ts
import { useState, useEffect, useRef } from 'react';
import { apiClient } from '@/services/api/client';
import { API_ENDPOINTS } from '@/services/api/endpoints';

interface SearchResponse {
  success: boolean;
  results: Array<{ caseCode: string; source: string }>;
  total: number;
}

// Кэш запросов в памяти
const searchCache = new Map<string, string[]>();

export function useCaseSearch() {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Очистка предыдущего таймера
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Пустой поиск
    if (!searchTerm.trim()) {
      setSearchResults([]);
      setIsLoading(false);
      return;
    }

    // Проверка кэша
    const cached = searchCache.get(searchTerm);
    if (cached) {
      setSearchResults(cached);
      setIsLoading(false);
      return;
    }

    // Debounced запрос
    setIsLoading(true);
    timeoutRef.current = setTimeout(async () => {
      try {
        const response = await apiClient.get<SearchResponse>(
          `${API_ENDPOINTS.SEARCH_CASES}?q=${encodeURIComponent(searchTerm)}&limit=20`
        );
        
        if (response.success) {
          const codes = response.results.map(r => r.caseCode);
          searchCache.set(searchTerm, codes);
          setSearchResults(codes);
        }
      } catch (error) {
        console.error('Ошибка поиска:', error);
        setSearchResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 400);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [searchTerm]);

  return {
    searchTerm,
    setSearchTerm,
    searchResults,
    hasResults: searchResults.length > 0,
    isLoading
  };
}