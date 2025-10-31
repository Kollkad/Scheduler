// ReusableDataTable.tsx
import { TableProps } from './TableTypes';

export function ReusableDataTable({ 
  columns, 
  data, 
  className = "", 
  onRowClick,
  isLoading = false,
  loadingMessage = "Загрузка данных..."
}: TableProps) {

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
                dangerouslySetInnerHTML={{ __html: column.title }}
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
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