// SortButton.tsx
import { useState, useRef, useEffect } from 'react';
import { Filter, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SortButtonProps {
  onSortChange: (direction: 'asc' | 'desc' | null) => void;
  onFilterChange?: (selectedValues: string[]) => void;
  filterOptions?: { value: string; label: string }[];
  selectedFilterValues?: string[];
  isActive: boolean;
  currentDirection?: 'asc' | 'desc';
}

export function SortButton({ 
  onSortChange, 
  onFilterChange,
  filterOptions = [],
  selectedFilterValues = [],
  isActive, 
  currentDirection 
}: SortButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [localSelectedValues, setLocalSelectedValues] = useState<string[]>(selectedFilterValues);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<'left' | 'right'>('right');

  // Синхронизируем локальное состояние с пропсами
  useEffect(() => {
    setLocalSelectedValues(selectedFilterValues);
  }, [selectedFilterValues]);

  // Фильтрация опций по поиску
  const filteredOptions = searchTerm 
    ? filterOptions.filter(option => 
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : filterOptions;

  // Закрытие при клике вне области
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

const handleButtonClick = () => {
  if (!isOpen && dropdownRef.current) {
    const rect = dropdownRef.current.getBoundingClientRect();
    const spaceOnRight = window.innerWidth - rect.right;
    const newPosition = spaceOnRight < 400 ? 'right' : 'left';
    setPosition(newPosition);
  }
  setIsOpen(!isOpen);
};

  const handleSortClick = (direction: 'asc' | 'desc' | null) => {
    onSortChange(direction);
  };

  const handleFilterToggle = (value: string) => {
    const newSelectedValues = localSelectedValues.includes(value)
      ? localSelectedValues.filter(v => v !== value)
      : [...localSelectedValues, value];
    
    setLocalSelectedValues(newSelectedValues);
  };

  const handleApply = () => {
    onFilterChange?.(localSelectedValues);
    setIsOpen(false);
  };

  const handleCancel = () => {
    onFilterChange?.([]);
    setIsOpen(false);
  };

  const handleClearSearch = () => {
    setSearchTerm('');
  };

  const sortOptions = [
    { value: 'asc' as const, label: 'А-Я' },
    { value: 'desc' as const, label: 'Я-А' },
  ];

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      <button
        onClick={handleButtonClick}
        className={`
          ml-2 p-1 rounded hover:bg-gray-100 transition-colors
          ${isActive ? 'text-blue-500' : 'text-gray-500'}
        `}
        title="Сортировка и фильтрация"
      >
        <Filter className="h-4 w-4" /> 
      </button>
      
      {/* Расширенное окно фильтрации и сортировки */}
      {isOpen && (
        <div className={`absolute top-full ${position === 'right' ? 'right-0' : 'left-0'} mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-10 w-[36rem] overflow-hidden`}>
          <div className="flex">
            {/* Левая часть - 2/3 (фильтрация) */}
            <div className="flex-1 p-4 border-r border-gray-200">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Фильтрация</h3>
              
              {/* Поле поиска */}
              <div className="relative mb-3">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Поиск..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-8 pr-8 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                />
                {searchTerm && (
                  <button
                    onClick={handleClearSearch}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 p-0.5 hover:bg-gray-100 rounded"
                  >
                    <X className="h-3 w-3 text-gray-400" />
                  </button>
                )}
              </div>

              {/* Список значений с чекбоксами */}
              <div className="max-h-48 overflow-y-auto mb-4 border border-gray-200 rounded-lg">
                {filteredOptions.length > 0 ? (
                  filteredOptions.map((option) => (
                    <label
                      key={option.value}
                      className="flex items-center px-3 py-2 text-sm cursor-pointer hover:bg-gray-50 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={localSelectedValues.includes(option.value)}
                        onChange={() => handleFilterToggle(option.value)}
                        className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 mr-3"
                      />
                      <span className="flex-1">{option.label}</span>
                    </label>
                  ))
                ) : (
                  <div className="px-3 py-2 text-sm text-gray-500 text-center">
                    Ничего не найдено
                  </div>
                )}
              </div>

              {/* Кнопки ОК и Отмена */}
              <div className="flex gap-2">
                <Button variant="green" size="rounded" onClick={handleApply} className="flex-1">
                  ОК
                </Button>
                <Button variant="grayOutline" size="rounded" onClick={handleCancel} className="flex-1">
                  Сбросить
                </Button>
              </div>
            </div>

            {/* Правая часть - 1/3 (сортировка) */}
            <div className="w-1/3 p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Сортировка</h3>
              <div className="space-y-1">
                {sortOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleSortClick(option.value)}
                    className={`
                      block w-full px-3 py-2 text-left text-sm hover:bg-gray-50 rounded transition-colors
                      ${
                        isActive && currentDirection === option.value 
                          ? 'bg-blue-50 text-blue-600 font-medium' 
                          : 'text-gray-700'
                      }
                    `}
                  >
                    {option.label}
                  </button>
                ))}
                {isActive && (
                  <button
                    onClick={() => handleSortClick(null)}
                    className="block w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 rounded transition-colors border-t border-gray-100 mt-2 pt-2"
                  >
                    ✕ Сбросить
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}