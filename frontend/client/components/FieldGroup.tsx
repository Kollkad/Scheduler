// frontend/client/components/FieldGroup.tsx
import { CircleAlert } from "lucide-react";
import { formatDate } from "@/utils/dateFormat";

interface Field {
  id: string;
  label: string;
  value?: any;
  type?: 'text' | 'date' | 'number' | 'currency' | 'boolean';
  isEmpty?: boolean;
}

interface FieldGroupProps {
  title?: string;
  fields: Field[];
  columns?: 1 | 2 | 3;
  showAlertIcon?: boolean;  // true только для группы "general"
}

export function FieldGroup({ title, fields, columns = 2, showAlertIcon = false }: FieldGroupProps) {
  // Функция форматирует значение поля в зависимости от его типа
  const getDisplayValue = (field: Field): string => {
    if (field.isEmpty) return '—';
    
    switch (field.type) {
      case 'boolean':
        return field.value === true ? 'Да' : 'Нет';
      case 'currency':
        return `${field.value} ₽`;
      case 'date':
        return formatDate(field.value);
      case 'number':
        return String(field.value);
      default:
        return field.value || '—';
    }
  };

  // Конфигурация колонок для разных разрешений экрана
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-3'
  };
    if (!fields || fields.length === 0) {
      return null;
    }

  return (
    <div className="bg-white rounded-lg border border-border p-6 mb-6">
      {title && (
        <h3 className="text-lg font-semibold text-text-primary mb-4 pb-2 border-b border-border">
          {title}
        </h3>
      )}
      
      <div className={`grid ${gridCols[columns]} gap-4`}>
        {fields.map((field) => {
          const isEmpty = field.isEmpty === true;
          const displayValue = getDisplayValue(field);
          
          return (
            <div key={field.id} className="space-y-1">
              <label className="text-sm font-medium text-text-primary">
                {field.label}
              </label>
              <div 
                className={`
                  text-sm text-text-primary rounded px-3 py-2 min-h-[36px] flex items-center justify-between
                  ${isEmpty ? 'bg-white border border-red' : 'bg-bg-default-light-field'}
                `}
              >
                <span>{displayValue}</span>
                {showAlertIcon && isEmpty && (
                  <CircleAlert className="h-4 w-4 text-red flex-shrink-0 ml-2" />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}