// SortButton.tsx
import { useState } from 'react';

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

  // Список доступных фильтров
  const filterOptions = [
    { value: null as 'asc' | 'desc' | null, label: '✕ Сбросить', show: isActive },
    { value: 'asc' as const, label: 'А-Я' },
    { value: 'desc' as const, label: 'Я-А' },
  ];

  // Иконка фильтра в SVG
  const FilterIcon = () => (
    <svg 
      width="16" 
      height="16" 
      viewBox="0 0 16 16" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={`${isActive ? 'text-blue-500' : 'text-gray-500'}`}
    >
      <path 
        d="M14 2H2L6.5 8.5V14L9.5 12V8.5L14 2Z" 
        stroke="currentColor" 
        strokeWidth="1.5" 
        strokeLinecap="round" 
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );

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
        <FilterIcon />
      </button>
      
      {isOpen && (
        <div className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-32 overflow-hidden">
          {/* Список фильтров */}
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