// services/filter/FilterService.ts
import { apiClient } from '../api/client';
import { API_ENDPOINTS } from '../api/endpoints';

export interface FilterOption {
  name: string;
  label: string;
}

export interface FilterOptionsResponse {
  success: boolean;
  data: Record<string, FilterOption[]>;
  message?: string;
}

export interface FilterMetadata {
  name: string;
  type: string;
  column: string;
}

export interface FiltersMetadataResponse {
  success: boolean;
  data: {
    filters: FilterMetadata[];
    total_filters: number;
  };
  message?: string;
}

export class FilterService {
  // Метод получает опции фильтров для указанных колонок
  static async getFilterOptions(columns?: string[]): Promise<Record<string, FilterOption[]>> {
    try {
      const params = columns ? `?${columns.map(col => `columns=${encodeURIComponent(col)}`).join('&')}` : '';
      const response = await apiClient.get<FilterOptionsResponse>(
        `${API_ENDPOINTS.FILTER_OPTIONS}${params}`
      );
      
      if (response.success) {
        return response.data;
      }
      throw new Error(response.message || 'Failed to fetch filter options');
    } catch (error) {
      console.error('Error fetching filter options:', error);
      throw error;
    }
  }

  // Метод получает метаданные всех доступных фильтров
  static async getFiltersMetadata(): Promise<FilterMetadata[]> {
    try {
      const response = await apiClient.get<FiltersMetadataResponse>(
        API_ENDPOINTS.FILTERS_METADATA
      );
      
      if (response.success) {
        return response.data.filters;
      }
      throw new Error(response.message || 'Failed to fetch filters metadata');
    } catch (error) {
      console.error('Error fetching filters metadata:', error);
      throw error;
    }
  }

  // Метод применяет указанные фильтры к данным и возвращает результат
  static async applyFilters(filters: Record<string, any>): Promise<any> {
    try {
      const response = await apiClient.post(API_ENDPOINTS.APPLY_FILTERS, filters);
      return response;
    } catch (error) {
      console.error('Error applying filters:', error);
      throw error;
    }
  }
}