// ReusableDataTable.tsx
import { TableProps } from './TableTypes';
import { SortButton } from './SortButton';
import { useState, useMemo } from 'react';

export function ReusableDataTable({ 
  columns, 
  data, 
  className = "", 
  onRowClick,
  isLoading = false,
  loadingMessage = "Загрузка данных...",
  sortConfig,
  onSortChange
}: TableProps) {

  const [localSortConfig, setLocalSortConfig] = useState<{key: string; direction: 'asc' | 'desc'} | null>(null);
  const [filters, setFilters] = useState<Record<string, string[]>>({});

  const currentSortConfig = sortConfig || localSortConfig;

  const getUniqueValuesForColumn = (columnKey: string) => {
    const values = data.map(row => row[columnKey]).filter(value => value != null && value !== '');
    const uniqueValues = [...new Set(values)];
    
    return uniqueValues.map(value => ({
      value: String(value),
      label: String(value)
    }));
  };

  const handleSortChange = (columnKey: string, direction: 'asc' | 'desc' | null) => {
    if (direction === null) {
      if (onSortChange) {
        onSortChange(null);
      } else {
        setLocalSortConfig(null);
      }
      return;
    }

    const newSortConfig = { key: columnKey, direction };
    
    if (onSortChange) {
      onSortChange(newSortConfig);
    } else {
      setLocalSortConfig(newSortConfig);
    }
  };

  const handleFilterChange = (columnKey: string, selectedValues: string[]) => {
    setFilters(prev => ({
      ...prev,
      [columnKey]: selectedValues
    }));
  };

  const filteredData = useMemo(() => {
    let result = data;
    
    Object.entries(filters).forEach(([columnKey, selectedValues]) => {
      if (selectedValues.length > 0) {
        result = result.filter(row => 
          selectedValues.includes(String(row[columnKey]))
        );
      }
    });
    
    return result;
  }, [data, filters]);

  const sortedData = useMemo(() => {
    if (!currentSortConfig) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = a[currentSortConfig.key];
      const bValue = b[currentSortConfig.key];

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return currentSortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
      }

      const aString = String(aValue || '').toLowerCase();
      const bString = String(bValue || '').toLowerCase();

      if (currentSortConfig.direction === 'asc') {
        return aString.localeCompare(bString, 'ru');
      } else {
        return bString.localeCompare(aString, 'ru');
      }
    });
  }, [filteredData, currentSortConfig]);

  const formatValue = (key: string, value: any) => {
    if (!value) return '';
    if (typeof value === 'string') {
      if (/^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?$/.test(value)) {
        const date = new Date(value.replace(' ', 'T'));
        if (!isNaN(date.getTime())) return date.toLocaleDateString('ru-RU');
      }
    }
    return value;
  };

  const getRowBackgroundColor = (index: number) => index % 2 === 0 ? 'white' : '#F3F3FD';

  if (isLoading) {
    return (
      <div className={`mt-6 overflow-x-auto ${className}`}>
        <div className="flex justify-center items-center h-48">
          <div className="text-gray-600 text-xs">{loadingMessage}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`mt-6 overflow-x-auto ${className}`}>
      <table 
        className="w-full text-xs table-fixed"
        style={{ border: '1px solid #BDBDCC', borderCollapse: 'collapse' }}
      >
        <thead>
          <tr style={{ backgroundColor: '#E3E3F1' }}>
            {columns.map((column) => (
              <th 
                key={column.key}
                className="px-3 py-2 text-left font-medium"
                style={{ 
                  color: '#171A1F',
                  border: '1px solid #BDBDCC',
                  fontSize: '11px',
                  width: column.width || 'auto',
                  textAlign: column.align || 'left'
                }}
              >
                <div className="flex items-center justify-between">
                  <span dangerouslySetInnerHTML={{ __html: column.title }} />
                  {column.sortable !== false && (
                    <SortButton
                      onSortChange={(direction) => handleSortChange(column.key, direction)}
                      onFilterChange={(selectedValues) => handleFilterChange(column.key, selectedValues)}
                      filterOptions={getUniqueValuesForColumn(column.key)}
                      selectedFilterValues={filters[column.key] || []}
                      isActive={currentSortConfig?.key === column.key || (filters[column.key] && filters[column.key].length > 0)}
                      currentDirection={currentSortConfig?.key === column.key ? currentSortConfig.direction : undefined}
                    />
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, index) => (
            <tr
              key={index}
              onClick={() => onRowClick?.(row, index)}
              className={onRowClick ? "cursor-pointer hover:bg-blue-50" : ""}
              style={{ backgroundColor: getRowBackgroundColor(index) }}
            >
              {columns.map((column) => (
                <td 
                  key={column.key}
                  className="px-3 py-2"
                  style={{ 
                    color: '#171A1F',
                    border: '1px solid #BDBDCC',
                    fontSize: '11px',
                    textAlign: column.align || 'left'
                  }}
                >
                  {formatValue(column.key, row[column.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}