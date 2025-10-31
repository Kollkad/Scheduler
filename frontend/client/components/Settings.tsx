// Settings.tsx
import { Search, ChevronDown, X } from "lucide-react";

interface FilterFieldProps {
  label: string;
  placeholder: string;
  hasSearch?: boolean;
  isSelected?: boolean;
}

function FilterField({ label, placeholder, hasSearch = false, isSelected = false }: FilterFieldProps) {
  return (
    <div
      className={`relative flex items-center bg-white rounded-2xl px-4 py-3 cursor-pointer transition-colors ${
        isSelected ? 'ring-2 ring-blue-400' : ''
      }`}
      style={{
        border: '1px solid #BDBDCC',
        minHeight: '44px'
      }}
    >
      <span className="flex-1 text-gray-500 text-sm">{placeholder}</span>
      <div className="flex items-center space-x-2 ml-2">
        {hasSearch && (
          <Search className="h-4 w-4" style={{ color: '#1F1F1F' }} />
        )}
        <ChevronDown className="h-4 w-4" style={{ color: '#1F1F1F' }} />
        <X className="h-4 w-4" style={{ color: '#1F1F1F' }} />
      </div>
    </div>
  );
}

export function Settings() {
  return (
    <div 
      className="bg-white rounded-2xl p-6 mt-8"
      style={{
        border: '1px solid #BDBDCC',
        boxShadow: '2px 4px 8px rgba(0, 0, 0, 0.1), -2px 0 8px rgba(0, 0, 0, 0.05)'
      }}
    >
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Настройка отчета</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <FilterField
          label="Список судебной защиты"
          placeholder="Список судебной защиты"
          hasSearch={false}
        />
        <FilterField
          label="ГОСБ"
          placeholder="ГОСБ"
          hasSearch={true}
        />
        <FilterField
          label="ОКР"
          placeholder="ОКР"
          hasSearch={false}
        />
        <FilterField
          label="Ответственный исполнитель"
          placeholder="Ответственный исполнитель"
          hasSearch={true}
        />
        <FilterField
          label="Цвет (текущий период)"
          placeholder="Цвет (текущий период)"
          hasSearch={false}
        />
        <FilterField
          label="Суд, рассматривающий дело"
          placeholder="Суд, рассматривающий дело"
          hasSearch={true}
          isSelected={true}
        />
        <FilterField
          label="Цвет (прошедший период)"
          placeholder="Цвет (прошедший период)"
          hasSearch={false}
        />
      </div>

      <div className="flex items-center justify-between">
        <div className="flex space-x-4">
          <button 
            className="px-6 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-full hover:bg-gray-50 transition-colors"
          >
            Очистить форму
          </button>
          <button 
            className="px-6 py-2 text-sm font-medium text-white rounded-full transition-colors"
            style={{ backgroundColor: '#1CC53C' }}
          >
            Сформировать отчет
          </button>
        </div>
        
        <button className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-full hover:bg-gray-50 transition-colors">
          <span>Дополнительные фильтры</span>
          <ChevronDown className="h-4 w-4 ml-2" style={{ color: '#1F1F1F' }} />
        </button>
      </div>
    </div>
  );
}