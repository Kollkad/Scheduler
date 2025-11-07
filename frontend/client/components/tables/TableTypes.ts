// TableTypes.ts
export interface TableColumn {
  key: string;
  title: string;
  width?: string;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
}

export interface TableConfig {
  columns: TableColumn[];
  pageSize?: number;
  sortable?: boolean;
}

export interface TableProps {
  columns: TableColumn[];
  data: Record<string, any>[];
  className?: string;
  onRowClick?: (row: Record<string, any>, index: number) => void;
  // Поля для будущей функциональности
  isLoading?: boolean;
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  onSort?: (columnKey: string, direction: 'asc' | 'desc') => void;
  // Поля для состояния загрузки и пустых данных
  emptyMessage?: string;
  loadingMessage?: string;
  // Поля сортировки
  sortConfig?: {
    key: string;
    direction: 'asc' | 'desc';
  } | null;
  onSortChange?: (sortConfig: { key: string; direction: 'asc' | 'desc' } | null) => void;
}
