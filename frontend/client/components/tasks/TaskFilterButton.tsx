// frontend/client/components/tasks/TaskFilterButton.tsx

import { useState, useRef, useEffect, useLayoutEffect } from 'react';
import { Filter, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DropdownPortal } from '@/components/DropdownPortal';

export type TaskFilter =
  | "all"
  | "overdue"
  | "today"
  | "week"
  | "completed"
  | "shifted";

interface TaskFilterButtonProps {
  filter: TaskFilter;
  onFilterChange: (filter: TaskFilter) => void;
  taskTextOptions: string[];
  selectedTaskTexts: string[];
  onTaskTextsChange: (texts: string[]) => void;
  onReset: () => void;
}

export function TaskFilterButton({
  filter,
  onFilterChange,
  taskTextOptions,
  selectedTaskTexts,
  onTaskTextsChange,
  onReset,
}: TaskFilterButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [localSelectedTexts, setLocalSelectedTexts] = useState<string[]>(selectedTaskTexts);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [coords, setCoords] = useState({ top: 0, left: 0 });

  // Синхронизация локального состояния
  useEffect(() => {
    setLocalSelectedTexts(selectedTaskTexts);
  }, [selectedTaskTexts]);

  // Фильтрация опций по поиску
  const filteredOptions = searchTerm
    ? taskTextOptions.filter(opt =>
        opt.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : taskTextOptions;

  // Закрытие по клику вне
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

  // Закрытие при ресайзе
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
      setCoords({ top: rect.bottom + 4, left: rect.left });
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  };

  // Авто-позиционирование
  useLayoutEffect(() => {
    if (!isOpen) return;
    if (!buttonRef.current || !dropdownRef.current) return;

    const btnRect = buttonRef.current.getBoundingClientRect();
    const ddRect = dropdownRef.current.getBoundingClientRect();

    let newLeft = btnRect.left;
    if (newLeft + ddRect.width > window.innerWidth - 8) {
      newLeft = Math.max(8, window.innerWidth - ddRect.width - 8);
    }

    let newTop = btnRect.bottom + 4;
    if (newTop + ddRect.height > window.innerHeight - 8) {
      newTop = Math.max(8, btnRect.top - ddRect.height - 4);
    }

    setCoords({ top: Math.round(newTop), left: Math.round(newLeft) });
  }, [isOpen]);

  const handleToggleText = (text: string) => {
    setLocalSelectedTexts(prev =>
      prev.includes(text) ? prev.filter(t => t !== text) : [...prev, text]
    );
  };

  const handleApply = () => {
    onTaskTextsChange(localSelectedTexts);
    setIsOpen(false);
  };

  const handleCancel = () => {
    setLocalSelectedTexts([]);
    onTaskTextsChange([]);
    setIsOpen(false);
  };

  const handleClearSearch = () => {
    setSearchTerm('');
  };

  const isActive = filter !== "all" || selectedTaskTexts.length > 0;

  const sortOptions: { value: TaskFilter; label: string }[] = [
    { value: "overdue", label: "Просроченные задачи" },
    { value: "today", label: "Необходимо сделать сегодня" },
    { value: "week", label: "Необходимо сделать в ближайшую неделю" },
    { value: "completed", label: "Выполненные задачи" },
    { value: "shifted", label: "Задачи со смещённой плановой датой" },
  ];

  return (
    <div className="relative inline-block">
      <button
        ref={buttonRef}
        onClick={handleButtonClick}
        className={`
          ml-2 p-1 rounded hover:bg-bg-light-grey transition-colors
          ${isActive ? 'text-blue' : 'text-text-primary'}
        `}
        title="Сортировка и фильтрация"
      >
        <Filter className="h-5 w-5" />
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
            className="bg-white border border-border rounded-xl shadow-lg overflow-hidden w-[36rem]"
          >
            <div className="flex">
              {/* Блок фильтрации */}
              <div className="flex-1 p-4 border-r border-border">
                <h3 className="text-sm font-medium text-text-primary mb-3">Фильтрация</h3>

                <div className="relative mb-3">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-text-tertiary" />
                  <input
                    type="text"
                    placeholder="Поиск по тексту задачи..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-8 pr-8 py-2 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue focus:border-transparent text-text-primary bg-white"
                  />
                  {searchTerm && (
                    <button
                      onClick={handleClearSearch}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 p-0.5 hover:bg-bg-light-grey rounded"
                    >
                      <X className="h-3 w-3 text-text-tertiary" />
                    </button>
                  )}
                </div>

                <div className="max-h-48 overflow-y-auto mb-4 border border-border rounded-lg">
                  {filteredOptions.length > 0 ? (
                    filteredOptions.map((option) => (
                      <label
                        key={option}
                        className="flex items-center px-3 py-2 text-sm cursor-pointer hover:bg-bg-default-light-field transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={localSelectedTexts.includes(option)}
                          onChange={() => handleToggleText(option)}
                          className="h-4 w-4 text-blue rounded border-border focus:ring-blue mr-3"
                        />
                        <span className="flex-1 text-text-primary">{option}</span>
                      </label>
                    ))
                  ) : (
                    <div className="px-3 py-2 text-sm text-text-tertiary text-center">
                      Ничего не найдено
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button variant="green" size="rounded" onClick={handleApply} className="flex-1">
                    Применить
                  </Button>
                  <Button variant="grayOutline" size="rounded" onClick={handleCancel} className="flex-1">
                    Сбросить
                  </Button>
                </div>
              </div>

              {/* Блок сортировки */}
              <div className="w-72 p-4">
                <h3 className="text-sm font-medium text-text-primary mb-3">Сортировка</h3>
                <div className="space-y-1">
                  {sortOptions.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => {
                        onFilterChange(option.value);
                        setIsOpen(false);
                      }}
                      className={`
                        block w-full px-3 py-2 text-left text-sm hover:bg-bg-default-light-field rounded transition-colors
                        ${filter === option.value
                          ? 'bg-blue-light text-blue font-medium'
                          : 'text-text-primary'
                        }
                      `}
                    >
                      {option.label}
                    </button>
                  ))}
                  {filter !== "all" && (
                    <button
                      onClick={() => {
                        onReset();
                        setIsOpen(false);
                      }}
                      className="block w-full px-3 py-2 text-left text-sm text-text-primary hover:bg-bg-default-light-field rounded transition-colors border-t border-border mt-2 pt-2"
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

