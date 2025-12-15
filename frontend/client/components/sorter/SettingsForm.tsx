// SettingsForm.tsx
import { useState, useEffect } from "react";
import { EyeOff, Eye } from "lucide-react";
import { SmartSelect } from "./SmartSelect";
import { SorterFormProps } from "./SorterTypes";
import { useFilterOptions } from '@/hooks/useFilterOptions';
import { Button } from "@/components/ui/button";
import { useAnalysis } from "@/contexts/AnalysisContext";

export function SettingsForm({ 
  title, 
  fields, 
  buttons, 
  additionalFiltersButton = true,
  onFiltersChange,
}: SorterFormProps) {
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const { options, loading, loadOptions } = useFilterOptions();
  const [showAdditionalFilters, setShowAdditionalFilters] = useState(false);
  const { analysisStatus } = useAnalysis();

  // Загрузка опций фильтров после завершения анализа (или если фильтры ещё не загружены)
  useEffect(() => {
    if (Object.keys(options).length === 0) {
      const loadFilters = async () => {
        try { await loadOptions(); } 
        catch (err) { console.error(err); }
      };
      loadFilters();
    }
  }, [analysisStatus.isComplete]);


  // Функция получает опции для конкретного поля
  const getOptionsForField = (fieldId: string) => {
    if (options[fieldId]) {
      return options[fieldId].map(option => ({
        value: option.name,
        label: option.label || option.name
      }));
    }
    
    return [];
  };

  // Обработчик изменения значения поля
  const handleValueChange = (fieldId: string, value: string) => {
    const newValues = { ...formValues, [fieldId]: value };
    setFormValues(newValues);
    onFiltersChange?.(newValues);
  };

  // Обработчик очистки значения поля
  const handleClear = (fieldId: string) => {
    const newValues = { ...formValues };
    delete newValues[fieldId];
    setFormValues(newValues);
    onFiltersChange?.(newValues);
  };

  // Обработчик очистки всей формы
  const handleClearForm = () => {
    setFormValues({});
    onFiltersChange?.({});
  };

  return (
    <div
      className="bg-white rounded-2xl p-6 mt-8"
      style={{
        border: '1px solid #BDBDCC',
        boxShadow: '2px 4px 8px rgba(0, 0, 0, 0.1), -2px 0 8px rgba(0, 0, 0, 0.05)'
      }}
    >
      <h2 className="text-xl font-semibold text-gray-900 mb-6">{title}</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {fields.map((field) => {
          const dynamicOptions = getOptionsForField(field.id);
          
          return (
            <SmartSelect
              key={field.id}
              placeholder={field.placeholder}
              options={dynamicOptions}
              hasSearch={field.hasSearch}
              value={formValues[field.id] || ""}
              onValueChange={(value) => handleValueChange(field.id, value)}
              onClear={() => handleClear(field.id)}
              isSelected={field.isSelected}
              isLoading={loading}
              onSearch={() => {}}
            />
          );
        })}
      </div>

      {/* TODO: фильтры пользователя*/}
      {showAdditionalFilters && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 text-center">
            Нет дополнительных фильтров
          </p>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex space-x-4">
          {buttons.map((button, index) => (
            <Button
              key={index}
              variant={button.type === 'primary' ? 'green' : 'grayOutline'}
              size="rounded"
              onClick={
                button.type === 'secondary'
                  ? () => {
                      handleClearForm();
                      buttons[index].onClearAll?.();
                    }
                  : button.onClick
              }
            >
              {button.text}
            </Button>
          ))}
        </div>

        {additionalFiltersButton && (
          <button 
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-full hover:bg-gray-50 transition-colors"
            onClick={() => setShowAdditionalFilters(!showAdditionalFilters)}
          >
            <span>Дополнительные фильтры</span>
            {showAdditionalFilters ? (
              <Eye className="h-4 w-4 ml-2" style={{ color: '#1F1F1F' }} />
            ) : (
              <EyeOff className="h-4 w-4 ml-2" style={{ color: '#1F1F1F' }} />
            )}
          </button>
        )}
      </div>
    </div>
  );

}