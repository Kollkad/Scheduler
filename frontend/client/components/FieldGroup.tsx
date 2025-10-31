// FieldGroup.tsx
interface Field {
  id: string;
  label: string;
  value?: string;
  type?: 'text' | 'date' | 'number' | 'currency' | 'boolean';
}

interface FieldGroupProps {
  title?: string;
  fields: Field[];
  columns?: 1 | 2 | 3;
}

export function FieldGroup({ title, fields, columns = 2 }: FieldGroupProps) {
  // Функция форматирует значение поля в зависимости от его типа
  const getDisplayValue = (field: Field) => {
    if (!field.value) return '—';
    
    switch (field.type) {
      case 'boolean':
        return field.value === 'true' ? 'Да' : 'Нет';
      case 'currency':
        return `${field.value} ₽`;
      default:
        return field.value;
    }
  };

  // Конфигурация колонок для разных разрешений экрана
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-3'
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
          {title}
        </h3>
      )}
      
      <div className={`grid ${gridCols[columns]} gap-4`}>
        {fields.map((field) => (
          <div key={field.id} className="space-y-1">
            <label className="text-sm font-medium text-gray-700">
              {field.label}
            </label>
            <div className="text-sm text-gray-900 bg-gray-50 rounded px-3 py-2 min-h-[36px] flex items-center">
              {getDisplayValue(field)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}