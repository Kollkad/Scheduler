// frontend/client/components/tasks/TaskFilterDropdown.tsx

import { useState, useRef, useEffect } from "react";
import { Filter } from "lucide-react";

export type TaskFilter = 
  | "all" 
  | "overdue"
  | "today" 
  | "week" 
  | "completed" 
  | "shifted";

interface TaskFilterDropdownProps {
  value: TaskFilter;
  onChange: (filter: TaskFilter) => void;
}

const filterOptions: { value: TaskFilter; label: string }[] = [
  { value: "all", label: "Все задачи" },
  { value: "overdue", label: "Просроченные задачи" },
  { value: "today", label: "Необходимо сделать сегодня" },
  { value: "week", label: "Необходимо сделать в ближайшую неделю" },
  { value: "completed", label: "Выполненные задачи" },
  { value: "shifted", label: "Задачи со смещённой плановой датой" },
];

export function TaskFilterDropdown({ value, onChange }: TaskFilterDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Закрытие по клику вне
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={ref} className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-1 hover:bg-bg-light-grey rounded transition-colors"
      >
        <Filter className="h-4 w-4 text-text-secondary" />
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full mt-1 bg-white border border-border-default rounded-lg shadow-lg z-50 w-72">
          {filterOptions.map(option => (
            <label
              key={option.value}
              className="flex items-center gap-2 px-4 py-2 hover:bg-bg-light-grey cursor-pointer text-sm text-text-primary"
            >
              <input
                type="radio"
                name="taskFilter"
                checked={value === option.value}
                onChange={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className="w-4 h-4 text-blue focus:ring-blue"
              />
              {option.label}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
