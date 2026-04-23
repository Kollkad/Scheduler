// frontend/client/components/TaskEditModal.tsx

import { useState, useEffect, useRef } from "react";
import { X, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SmartSelect } from "@/components/sorter/SmartSelect";
import { SelectOption } from "@/components/sorter/SorterTypes";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { Task } from "@/services/api/taskTypes";
import { formatDate } from "@/utils/dateFormat";

interface TaskEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: Task;
  onSuccess?: () => void;
}

interface ShiftReason {
  shiftCode: string;
  shiftName: string;
  daysToAdd: number;
}

export function TaskEditModal({ isOpen, onClose, task, onSuccess }: TaskEditModalProps) {
  const [isCompleted, setIsCompleted] = useState<boolean>(task.isCompleted);
  const [shiftEnabled, setShiftEnabled] = useState<boolean>(false);
  const [selectedShiftCode, setSelectedShiftCode] = useState<string>("");
  const [shiftReasons, setShiftReasons] = useState<ShiftReason[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  // Загрузка причин переноса при открытии
  useEffect(() => {
    if (isOpen && task.taskCode) {
      loadShiftReasons();
    }
  }, [isOpen, task.taskCode]);

  // Сброс состояния при закрытии
  useEffect(() => {
    if (!isOpen) {
      setShiftEnabled(false);
      setSelectedShiftCode("");
      setIsCompleted(task.isCompleted);
    }
  }, [isOpen, task.isCompleted]);

  // Обработчик клика вне модального окна и нажатия Escape
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  // Загрузка списка допустимых причин переноса
  const loadShiftReasons = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<{
        success: boolean;
        shiftReasons: ShiftReason[];
      }>(`${API_ENDPOINTS.TASK_SHIFT_REASONS}/${task.taskCode}/shift-reasons`);
      
      if (response.success) {
        setShiftReasons(response.shiftReasons || []);
      }
    } catch (error) {
      console.error('Ошибка загрузки причин переноса:', error);
      setShiftReasons([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Получение опций для SmartSelect
  const shiftReasonOptions: SelectOption[] = shiftReasons.map(reason => ({
    value: reason.shiftCode,
    label: reason.shiftName
  }));

  // Получение выбранной причины
  const selectedReason = shiftReasons.find(r => r.shiftCode === selectedShiftCode);

  // Расчет новой плановой даты
  const calculateNewPlannedDate = (): string => {
    if (!task.executionDatePlan || !selectedReason) return "—";
    
    const currentDate = new Date(task.executionDatePlan);
    currentDate.setDate(currentDate.getDate() + selectedReason.daysToAdd);
    return currentDate.toISOString().split('T')[0];
  };

  // Сохранение изменений
  const handleSave = async () => {
    if (!task.taskCode) return;

    setIsSaving(true);
    try {
      const body: { is_completed?: boolean; shift_code?: string } = {};

    if (isCompleted !== task.isCompleted) {
    body.is_completed = isCompleted;
    }

    if (shiftEnabled && selectedShiftCode) {
    body.shift_code = selectedShiftCode;
    }

      await apiClient.patch(`${API_ENDPOINTS.TASK_UPDATE}/${task.taskCode}`, body);
      
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Ошибка сохранения изменений:', error);
      alert('Не удалось сохранить изменения');
    } finally {
      setIsSaving(false);
    }
  };

  const handleShiftEnabledChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setShiftEnabled(e.target.checked);
    if (!e.target.checked) {
      setSelectedShiftCode("");
    }
  };

  if (!isOpen) return null;

  const newPlannedDate = calculateNewPlannedDate();
  const hasChanges = (isCompleted !== task.isCompleted) || (shiftEnabled && selectedShiftCode);

  return (
    <div className="fixed inset-0 bg-bg-medium-gray flex items-center justify-center z-50 p-4">
      <div
        ref={modalRef}
        className="bg-white rounded-2xl p-6 max-w-2xl w-full relative border border-border-default"
        style={{
          boxShadow: '2px 4px 8px rgba(0, 0, 0, 0.1), -2px 0 8px rgba(0, 0, 0, 0.05)'
        }}
      >
        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-bg-light-grey rounded-full transition-colors"
          disabled={isSaving}
        >
          <X className="h-5 w-5 text-dark-default" />
        </button>

        {/* Заголовок */}
        <h2 className="text-xl font-semibold text-text-primary mb-4 pr-8">
          Изменить задачу {task.taskCode}
        </h2>

        {/* Текст задачи */}
        <p className="mb-6 text-sm text-text-primary">{task.taskText}</p>
      
        {/* Радио-кнопки статуса */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-text-primary mb-3">
            Статус выполнения:
          </label>
          <div className="flex gap-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="completionStatus"
                checked={isCompleted}
                onChange={() => setIsCompleted(true)}
                className="w-4 h-4 text-green focus:ring-green"
              />
              <span className="text-sm text-text-primary">Выполнено</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="completionStatus"
                checked={!isCompleted}
                onChange={() => setIsCompleted(false)}
                className="w-4 h-4 text-blue focus:ring-blue"
              />
              <span className="text-sm text-text-primary">Не выполнено</span>
            </label>
          </div>
        </div>

        {/* Чекбокс переноса срока */}
        <div className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={shiftEnabled}
              onChange={handleShiftEnabledChange}
              className="w-4 h-4 text-blue focus:ring-blue rounded"
            />
            <span className="text-sm text-text-primary">
              Изменить плановую дату выполнения
            </span>
          </label>
        </div>

        {/* Блок переноса срока */}
        {shiftEnabled && (
          <div className="space-y-4 mb-6">
            {/* Выбор причины */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Выберите причину изменения срока:
              </label>
              <SmartSelect
                placeholder={isLoading ? "Загрузка..." : "Выберите причину..."}
                options={shiftReasonOptions}
                value={selectedShiftCode}
                onValueChange={setSelectedShiftCode}
                onClear={() => setSelectedShiftCode("")}
                isSelected={!!selectedShiftCode}
              />
            </div>

            {/* Информация о переносе */}
            {selectedReason && (
              <>
                <div className="p-3 bg-bg-default-light-field rounded-lg">
                  <p className="text-sm text-text-primary">
                    Плановая дата выполнения задачи будет сдвинута на{" "}
                    <span className="font-semibold">{selectedReason.daysToAdd}</span>{" "}
                    {selectedReason.daysToAdd === 1 ? "день" : 
                     selectedReason.daysToAdd < 5 ? "дня" : "дней"}.
                  </p>
                </div>

                {/* Овальный блок с датами */}
                <div>
                  <div className="grid grid-cols-2 gap-0 mb-1">
                    <div className="text-text-primary text-xs text-left pl-3">
                      Дата план (до)
                    </div>
                    <div className="text-text-primary text-xs text-left pl-3">
                      Дата план (после)
                    </div>
                  </div>

                  <div className="flex rounded-full border border-border overflow-hidden">
                    <div className="flex-1 py-2 px-3 text-center rounded-l-full">
                      <div className="text-text-primary text-sm">
                        {task.executionDatePlan ? formatDate(task.executionDatePlan) : "—"}
                      </div>
                    </div>
                    <div className="w-px bg-border" />
                    <div className="flex-1 py-2 px-3 text-center bg-bg-default-light-field rounded-r-full">
                      <div className="text-text-primary text-sm">
                        {newPlannedDate ? formatDate(newPlannedDate) : "—"}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* Кнопка сохранения */}
        <div className="flex justify-center">
          <Button
            variant="green"
            size="rounded"
            onClick={handleSave}
            disabled={isSaving || !hasChanges}
            className="w-4/5 flex items-center justify-center gap-2"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Сохранение...
              </>
            ) : (
              <>
                <Pencil className="h-4 w-4" />
                Внести изменения
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
