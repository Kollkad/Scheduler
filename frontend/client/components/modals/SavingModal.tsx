// frontend/client/components/modals/SavingModal.tsx
import { useState, useRef, useEffect } from "react";
import { X, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { savingService, SaveDataType } from "@/services/saving/SavingService";
import { SmartSelect } from "@/components/sorter/SmartSelect";
import { SelectOption } from "@/components/sorter/SorterTypes";

// Тип статуса доступных данных
interface DataStatus {
  loaded: boolean;
  row_count: number;
}

interface AvailableDataStatus {
  detailed_report: DataStatus;
  documents_report: DataStatus;
  stages: DataStatus;
  checks: DataStatus;
  check_results: DataStatus;
  tasks: DataStatus;
  user_overrides: DataStatus;
}

interface SavingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SavingModal({ isOpen, onClose }: SavingModalProps) {
  const [selectedType, setSelectedType] = useState<SaveDataType>();
  const [isSaving, setIsSaving] = useState(false);
  const [availableData, setAvailableData] = useState<AvailableDataStatus | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  // Опции выбора типа данных для сохранения
  const dataTypeOptions: SelectOption[] = [
    { value: 'detailed-report', label: 'Детальный отчет' },
    { value: 'documents-report', label: 'Отчет документов' },
    { value: 'stages', label: 'Этапы документов и дел' },
    { value: 'checks', label: 'Проверки документов и дел' },
    { value: 'check-results-cases', label: 'Результаты проверок (дела)' },
    { value: 'check-results-documents', label: 'Результаты проверок (документы)' },
    { value: 'tasks', label: 'Все задачи' },
    { value: 'user-overrides', label: 'Мои изменения задач' },
  ];

  // Описания типов данных для отображения
  const dataTypeDescriptions: Record<SaveDataType, string> = {
    'detailed-report': 'Очищенный детальный отчет по судебной работе',
    'documents-report': 'Очищенный отчет по полученным и переданным документам',
    'stages': 'Сводка всех этапов документов и дел',
    'checks': 'Сводка всех проверок документов и дел',
    'check-results-cases': 'Результаты проведенных проверок для дел',
    'check-results-documents': 'Результаты проведенных проверок для документов',
    'tasks': 'Все поставленные задачи',
    'user-overrides': 'Внесенные изменения в задачи (текущий пользователь)',
  };

  // Загрузка статуса доступных данных при открытии
  useEffect(() => {
    if (isOpen) {
      loadAvailableDataStatus();
    }
  }, [isOpen]);

  // Закрытие по клику вне модального окна и по Escape
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

  // Загружает статус доступных данных с бэкенда
  const loadAvailableDataStatus = async () => {
    try {
      const response = await savingService.getAvailableDataStatus();
      if (response.success) {
        setAvailableData(response.status);
      }
    } catch (error) {
      console.error('Ошибка загрузки статуса данных:', error);
    }
  };

  // Получает статус для выбранного типа данных
  const getDataStatusInfo = (type: SaveDataType): DataStatus | null => {
    if (!availableData) return null;
    
    const statusMap: Record<SaveDataType, keyof AvailableDataStatus> = {
      'detailed-report': 'detailed_report',
      'documents-report': 'documents_report',
      'stages': 'stages',
      'checks': 'checks',
      'check-results-cases': 'check_results',
      'check-results-documents': 'check_results',
      'tasks': 'tasks',
      'user-overrides': 'user_overrides',
    };
    
    const statusKey = statusMap[type];
    return availableData[statusKey] || null;
  };

  // Выполняет сохранение выбранного типа данных
  const handleSave = async () => {
    if (!selectedType) return;

    try {
      setIsSaving(true);
      
      const selectedOption = dataTypeOptions.find(opt => opt.value === selectedType);
      const extension = 'xlsx';
      const fileName = `${selectedOption?.label || 'data'}.${extension}`;
      
      const link = document.createElement('a');
      link.style.display = 'none';
      document.body.appendChild(link);
      
      const blob = await savingService.saveData(selectedType);
      
      const url = window.URL.createObjectURL(blob);
      link.href = url;
      link.download = fileName;
      link.click();
      
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
      }, 100);
      
    } catch (error) {
      console.error('Ошибка сохранения файла:', error);
      alert('Ошибка при сохранении файла. Проверьте консоль для подробностей.');
    } finally {
      setIsSaving(false);
    }
  };

  // Обработчик изменения выбранного типа
  const handleTypeChange = (value: string) => {
    setSelectedType(value as SaveDataType);
  };

  // Обработчик очистки выбора
  const handleClearType = () => {
    setSelectedType(undefined);
  };

  const selectedOption = dataTypeOptions.find(opt => opt.value === selectedType);
  const statusInfo = selectedType ? getDataStatusInfo(selectedType) : null;

  if (!isOpen) return null;

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
        <h2 className="text-xl font-semibold text-text-primary mb-6 pr-8">
          Сохранение Excel-файлов
        </h2>

        {/* Выбор типа данных */}
        <div className="space-y-4 mb-6">
          <label className="block text-sm font-medium text-text-secondary mb-2">
            Выберите тип данных для сохранения:
          </label>
          
          <SmartSelect
            placeholder="Выберите тип данных..."
            options={dataTypeOptions}
            value={selectedType}
            onValueChange={handleTypeChange}
            onClear={handleClearType}
            isSelected={!!selectedType}
          />

          {/* Описание и статус */}
          {selectedType && (
            <div className="p-4 bg-default-light-field rounded-lg space-y-3">
              <div>
                <p className="text-sm font-medium text-text-primary mb-1">Описание:</p>
                <p className="text-sm text-text-primary">
                  {dataTypeDescriptions[selectedType]}
                </p>
              </div>
              
              {/* Статус доступности данных */}
              {statusInfo && (
                <div>
                  <p className="text-sm font-medium text-text-primary mb-1">Статус данных:</p>
                  <div className="text-xs">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full ${
                      statusInfo.loaded 
                        ? 'bg-bg-light-green text-green-dark' 
                        : 'bg-bg-yellow text-dark-default'
                    }`}>
                      {statusInfo.loaded 
                        ? `✓ Данные доступны (${statusInfo.row_count} записей)`
                        : '⚠ Данные не загружены'
                      }
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Кнопка сохранения */}
        <div className="flex justify-center">
          <Button
            variant="green"
            size="rounded"
            onClick={handleSave}
            disabled={isSaving || !selectedType || (statusInfo && !statusInfo.loaded)}
            className="w-4/5 flex items-center justify-center gap-2"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Сохранение...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Сохранить файл
              </>
            )}
          </Button>
        </div>

        {/* Информация о недоступности */}
        {statusInfo && !statusInfo.loaded && (
          <div className="mt-3 text-center">
            <p className="text-xs text-text-primary">
              Сохранение недоступно: данные не загружены
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
