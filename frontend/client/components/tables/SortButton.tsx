// SortButton.tsx
import { useState } from 'react';
import { Filter } from 'lucide-react';

interface SortButtonProps {
  onSortChange: (direction: 'asc' | 'desc' | null) => void;
  isActive: boolean;
  currentDirection?: 'asc' | 'desc';
}

export function SortButton({ onSortChange, isActive, currentDirection }: SortButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleButtonClick = () => {
    setIsOpen(!isOpen);
  };

  const handleSortClick = (direction: 'asc' | 'desc' | null) => {
    onSortChange(direction);
    setIsOpen(false);
  };

  const filterOptions = [
    { value: null as 'asc' | 'desc' | null, label: '✕ Сбросить', show: isActive },
    { value: 'asc' as const, label: 'А-Я' },
    { value: 'desc' as const, label: 'Я-А' },
  ];

  return (
    <div className="relative inline-block">
      <button
        onClick={handleButtonClick}
        className={`
          ml-2 p-1 rounded hover:bg-gray-100 transition-colors
          ${isActive ? 'text-blue-500' : 'text-gray-500'}
        `}
        title="Сортировка"
      >
        <Filter className="h-4 w-4" /> 
      </button>
      
      {/* Список фильтров */}
      {isOpen && (
        <div className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-32 overflow-hidden">
          {filterOptions
            .filter(option => option.show !== false)
            .map((option, index) => (
              <button
                key={option.value || 'reset'}
                onClick={() => handleSortClick(option.value)}
                className={`
                  block w-full px-3 py-2 text-left text-sm hover:bg-gray-50 whitespace-nowrap 
                  transition-colors
                  ${index > 0 ? 'border-t border-gray-100' : ''}
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
        </div>
      )}
    </div>
  );
}