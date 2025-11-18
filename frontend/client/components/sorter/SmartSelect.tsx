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
        className={`relative flex items-center bg-white rounded-xl px-3 py-2 cursor-pointer transition-colors ${
          isSelected ? 'ring-2 ring-blue-400' : ''
        }`}
        style={{
          border: '1px solid #BDBDCC',
          minHeight: '36px' // было 44px
        }}
      >
        <span className={`flex-1 text-left text-sm ${value ? 'text-gray-900' : 'text-gray-500'}`}>
          {displayValue}
        </span>
        
        <div className="flex items-center space-x-2 ml-2">
          {isLoading && (
            <Loader className="h-4 w-4 animate-spin" style={{ color: '#1F1F1F' }} />
          )}
          {hasSearch && !isLoading && (
            <Search className="h-4 w-4" style={{ color: '#1F1F1F' }} />
          )}
          <ChevronDown
            className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            style={{ color: '#1F1F1F' }}
          />
          <button
            type="button"
            onClick={handleClear}
            className="p-0.5 hover:bg-gray-100 rounded"
          >
            <X className="h-4 w-4" style={{ color: '#1F1F1F' }} />
          </button>
        </div>
      </div>

      {isOpen && (
        <div 
          className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-lg border z-50 overflow-hidden"
          style={{ border: '1px solid #BDBDCC' }}
        >
          {hasSearch && (
            <div className="p-2 border-b" style={{ borderColor: '#BDBDCC' }}> {/* было p-3 */}
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" /> {/* было left-3 */}
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Поиск..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                  className="w-full pl-8 pr-2 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent" // было pl-10, py-2
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            </div>
          )}
          
          <div className="max-h-48 overflow-y-auto"> {/* было max-h-60 */}
            {isLoading ? (
              <div className="px-3 py-2 text-sm text-gray-500 flex justify-center"> {/* было px-4 py-3 */}
                <Loader className="h-4 w-4 animate-spin" />
              </div>
            ) : filteredOptions.length > 0 ? (
              filteredOptions.map((option, index) => (
                <div
                  key={option.value}
                  onClick={() => handleOptionSelect(option.value)}
                  className={`relative flex items-center px-3 py-3 text-sm cursor-pointer transition-colors ${
                    index === highlightedIndex ? 'bg-blue-50' : 'hover:bg-gray-50'
                  }`} // было px-4 py-3
                >
                  {option.label}
                </div>
              ))
            ) : (
              <div className="px-3 py-2 text-sm text-gray-500"> {/* было px-4 py-3 */}
                Ничего не найдено
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}