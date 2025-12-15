// SortButton.tsx
import { useState, useRef, useEffect, useLayoutEffect } from 'react';
import { Filter, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DropdownPortal } from '@/components/DropdownPortal';

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
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const [placement, setPlacement] = useState<'left' | 'right'>('right');

  useEffect(() => {
    setLocalSelectedValues(selectedFilterValues);
  }, [selectedFilterValues]);

  const filteredOptions = searchTerm
    ? filterOptions.filter(option =>
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : filterOptions;

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(target) &&
        buttonRef.current &&
        !buttonRef.current.contains(target)
      ) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // При ресайзе закрываем / перерасчитываем
  useEffect(() => {
    function onResize() {
      setIsOpen(false);
    }
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const handleButtonClick = () => {
    if (!isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();

      // начальные предположения: позиционируем под кнопкой, по левому краю кнопки
      const initialLeft = rect.left;
      const initialTop = rect.bottom + 4;

      setCoords({ top: initialTop, left: initialLeft });
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  };

  // После рендера popup — корректируем позицию, чтобы он не вылезал за экран и выбрать сторону
  useLayoutEffect(() => {
    if (!isOpen) return;
    if (!buttonRef.current) return;

    const btnRect = buttonRef.current.getBoundingClientRect();
    const dropdownEl = dropdownRef.current;
    if (!dropdownEl) return;

    const ddRect = dropdownEl.getBoundingClientRect();
    const dropdownWidth = ddRect.width;
    const dropdownHeight = ddRect.height;

    const spaceOnRight = window.innerWidth - btnRect.right;
    const spaceOnLeft = btnRect.left;
    const spaceBelow = window.innerHeight - btnRect.bottom;
    const spaceAbove = btnRect.top;

    // Выбор horizontal placement: если справа мало места — привязываем к правому краю кнопки
    let newLeft: number;
    let newPlacement: 'left' | 'right' = 'left';
    if (spaceOnRight >= dropdownWidth) {
      newLeft = btnRect.left; // помещается справа (выравнивание по левому краю кнопки)
      newPlacement = 'left';
    } else if (spaceOnLeft >= dropdownWidth) {
      newLeft = btnRect.right - dropdownWidth; // помещается слева (align to right of button)
      newPlacement = 'right';
    } else {
      // никуда полностью не помещается — стараемся держать в видимой области
      newLeft = Math.max(8, Math.min(btnRect.left, window.innerWidth - dropdownWidth - 8));
      newPlacement = spaceOnRight >= spaceOnLeft ? 'left' : 'right';
    }

    // Выбор vertical placement: открывать сверху или снизу
    let newTop: number;
    if (spaceBelow >= dropdownHeight + 8) {
      newTop = btnRect.bottom + 4; // открываем вниз
    } else if (spaceAbove >= dropdownHeight + 8) {
      newTop = btnRect.top - dropdownHeight - 4; // открываем вверх
    } else {
      // подстраиваем чтобы не выйти за пределы экрана
      if (spaceBelow >= spaceAbove) {
        newTop = btnRect.bottom + 4;
        // если всё равно выходит — уменьшаем top чтобы влезло
        if (newTop + dropdownHeight > window.innerHeight) {
          newTop = Math.max(8, window.innerHeight - dropdownHeight - 8);
        }
      } else {
        newTop = Math.max(8, btnRect.top - dropdownHeight - 4);
      }
    }

    setCoords({ top: Math.round(newTop), left: Math.round(newLeft) });
    setPlacement(newPlacement);
  }, [isOpen]);

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
    <div className="relative inline-block">
      <button
        ref={buttonRef}
        onClick={handleButtonClick}
        className={`
          ml-2 p-1 rounded hover:bg-gray-100 transition-colors
          ${isActive ? 'text-blue-500' : 'text-gray-500'}
        `}
        title="Сортировка и фильтрация"
      >
        <Filter className="h-4 w-4" />
      </button>

      {isOpen && (
        <DropdownPortal>
          <div
            ref={dropdownRef}
            style={{
              position: 'absolute',
              top: coords.top,
              left: coords.left,
              zIndex: 9999,
              minWidth: 320
            }}
            className="bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden w-[36rem]"
          >
            <div className="flex">
              <div className="flex-1 p-4 border-r border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Фильтрация</h3>

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

                <div className="flex gap-2">
                  <Button variant="green" size="rounded" onClick={handleApply} className="flex-1">
                    ОК
                  </Button>
                  <Button variant="grayOutline" size="rounded" onClick={handleCancel} className="flex-1">
                    Сбросить
                  </Button>
                </div>
              </div>

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
        </DropdownPortal>
      )}
    </div>
  );
}
