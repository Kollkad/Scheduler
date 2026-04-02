// SmartSelect.tsx
import { useState, useEffect, useRef, useCallback } from "react";
import { Search, ChevronDown, X, Loader } from "lucide-react";
import { SmartSelectProps } from "./SorterTypes";

export function SmartSelect({ 
  placeholder, 
  options, 
  hasSearch = false, 
  value = "", 
  onValueChange,
  onClear,
  isSelected = false,
  isLoading = false,
  onSearch,
  endpoint
}: SmartSelectProps & { endpoint?: string }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Фильтрация опций на основе поискового запроса
  const filteredOptions = hasSearch 
    ? options.filter(option => 
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;

  // Закрытие выпадающего списка при клике вне области
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Очистка поиска при закрытии выпадающего списка
  useEffect(() => {
    if (!isOpen) {
      setSearchTerm("");
      setHighlightedIndex(-1);
    } else if (hasSearch && searchInputRef.current) {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [isOpen, hasSearch]);

  // Обработчик изменения поискового запроса
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSearchTerm = e.target.value;
    setSearchTerm(newSearchTerm);
    onSearch?.(newSearchTerm);
  };

  // Обработчик навигации с клавиатуры
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex(prev => 
            prev < filteredOptions.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex(prev => 
            prev > 0 ? prev - 1 : filteredOptions.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (highlightedIndex >= 0 && filteredOptions[highlightedIndex]) {
            handleOptionSelect(filteredOptions[highlightedIndex].value);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredOptions, highlightedIndex]);

  // Функция переключает состояние открытия выпадающего списка
  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  // Функция обрабатывает выбор опции
  const handleOptionSelect = (optionValue: string) => {
    onValueChange?.(optionValue);
    setIsOpen(false);
    setSearchTerm("");
  };

  // Функция очищает выбранное значение
  const handleClear = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onClear?.();
    setSearchTerm("");
  };

  const displayValue = value ? options.find(opt => opt.value === value)?.label : placeholder;

  return (
    <div className="relative" ref={dropdownRef}>
      <div 
        onClick={handleToggle}
        className={`relative flex items-center bg-white rounded-xl px-3 py-2 cursor-pointer transition-colors border border-border-default ${
          isSelected ? 'ring-2 ring-blue-transparent' : ''
        }`}
        style={{ minHeight: '36px' }}
      >
        <span className={`flex-1 text-left text-sm ${value ? 'text-text-primary' : 'text-text-secondary'}`}>
          {displayValue}
        </span>
        
        <div className="flex items-center space-x-2 ml-2">
          {isLoading && (
            <Loader className="h-4 w-4 animate-spin text-text-primary" />
          )}
          {hasSearch && !isLoading && (
            <Search className="h-4 w-4 text-text-primary" />
          )}
          <ChevronDown
            className={`h-4 w-4 transition-transform text-text-primary ${isOpen ? 'rotate-180' : ''}`}
          />
          <button
            type="button"
            onClick={handleClear}
            className="p-0.5 hover:bg-bg-light-grey rounded"
          >
            <X className="h-4 w-4 text-text-primary" />
          </button>
        </div>
      </div>

      {isOpen && (
        <div 
          className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-lg border border-border-default z-50 overflow-hidden"
        >
          {/* Поле поиска */}
          {hasSearch && (
            <div className="p-2 border-b border-border-default">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-text-tertiary" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Поиск..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                  className="w-full pl-8 pr-2 py-2 text-sm text-text-secondary border border-border-default rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-transparent focus:border-transparent"
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            </div>
          )}
          
          {/* Список опций */}
          <div className="max-h-48 overflow-y-auto">
            {isLoading ? (
              <div className="px-3 py-2 text-sm text-text-secondary flex justify-center">
                <Loader className="h-4 w-4 animate-spin" />
              </div>
            ) : filteredOptions.length > 0 ? (
              filteredOptions.map((option, index) => (
                <div
                  key={option.value}
                  onClick={() => handleOptionSelect(option.value)}
                  className={`relative flex items-center px-3 py-3 text-sm text-text-secondary cursor-pointer transition-colors ${
                    index === highlightedIndex ? 'bg-blue-transparent' : 'hover:bg-bg-default-light-field'
                  }`}
                >
                  {option.label}
                </div>
              ))
            ) : (
              <div className="px-3 py-2 text-sm text-text-tertiary">
                Ничего не найдено
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}