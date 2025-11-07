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

  // Используем переданную конфигурацию сортировки или локальную
  const currentSortConfig = sortConfig || localSortConfig;

  // Функция для обработки сортировки
  const handleSortChange = (columnKey: string, direction: 'asc' | 'desc' | null) => {
    if (direction === null) {
      // Сброс сортировки
      if (onSortChange) {
        onSortChange(null);
      } else {
        setLocalSortConfig(null);
      }
      return;
    }

    const newSortConfig = { key: columnKey, direction };
    
    if (onSortChange) {
      // Если передан внешний обработчик, используем его
      onSortChange(newSortConfig);
    } else {
      // Иначе используем локальное состояние
      setLocalSortConfig(newSortConfig);
    }
  };

  // Сортируем данные
  const sortedData = useMemo(() => {
    if (!currentSortConfig) return data;

    return [...data].sort((a, b) => {
      const aValue = a[currentSortConfig.key];
      const bValue = b[currentSortConfig.key];

      // Для числовых значений
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return currentSortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
      }

      // Для строковых значений (и других типов)
      const aString = String(aValue || '').toLowerCase();
      const bString = String(bValue || '').toLowerCase();

      if (currentSortConfig.direction === 'asc') {
        return aString.localeCompare(bString, 'ru');
      } else {
        return bString.localeCompare(aString, 'ru');
      }
    });
  }, [data, currentSortConfig]);

  // Функция форматирует значения ячеек таблицы
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

  // Функция определяет цвет фона строки для чередования
  const getRowBackgroundColor = (index: number) => index % 2 === 0 ? 'white' : '#F3F3FD';

  if (isLoading) {
    return (
      <div className={`mt-8 overflow-x-auto ${className}`}>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-600">{loadingMessage}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`mt-8 overflow-x-auto ${className}`}>
      <table 
        className="w-full text-sm"
        style={{ border: '1px solid #BDBDCC', borderCollapse: 'collapse' }}
      >
        <thead>
          <tr style={{ backgroundColor: '#E3E3F1' }}>
            {columns.map((column) => (
              <th 
                key={column.key}
                className="px-4 py-3 text-left font-medium"
                style={{ 
                  color: '#171A1F',
                  border: '1px solid #BDBDCC',
                  fontSize: '13px',
                  width: column.width || 'auto',
                  textAlign: column.align || 'left'
                }}
              >
                <div className="flex items-center justify-between">
                  <span dangerouslySetInnerHTML={{ __html: column.title }} />
                  {column.sortable !== false && (
                    <SortButton
                      onSortChange={(direction) => handleSortChange(column.key, direction)}
                      isActive={currentSortConfig?.key === column.key}
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
                  className="px-4 py-3"
                  style={{ 
                    color: '#171A1F',
                    border: '1px solid #BDBDCC',
                    fontSize: '13px',
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