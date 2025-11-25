// SavingModal.tsx
import { useState, useEffect, useRef } from "react";
import { X, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { savingService, SaveDataType } from "@/services/saving/SavingService";
import { SmartSelect } from "@/components/sorter/SmartSelect";
import { SelectOption } from "@/components/sorter/SorterTypes";

interface SavingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface AvailableDataStatus {
  detailed_report: {
    loaded: boolean;
    row_count: number;
  };
  documents_report: {
    loaded: boolean;
    row_count: number;
  };
  lawsuit_production: {
    loaded: boolean;
    row_count: number;
  };
  order_production: {
    loaded: boolean;
    row_count: number;
  };
  documents_analysis: {
    loaded: boolean;
    row_count: number;
  };
  tasks: {
    loaded: boolean;
    row_count: number;
  };
}

interface StatusResponse {
  success: boolean;
  status: AvailableDataStatus;
  message: string;
}

export function SavingModal({ isOpen, onClose }: SavingModalProps) {
  const [selectedType, setSelectedType] = useState<SaveDataType>();
  const [isSaving, setIsSaving] = useState(false);
  const [availableData, setAvailableData] = useState<AvailableDataStatus | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const dataTypeOptions: SelectOption[] = [
    { 
      value: 'detailed-report', 
      label: 'Детальный отчет', 
    },
    { 
      value: 'documents-report', 
      label: 'Отчет документов', 
    },
    { 
      value: 'lawsuit-production', 
      label: 'Исковое производство', 
    },
    { 
      value: 'order-production', 
      label: 'Приказное производство', 
    },
    { 
      value: 'documents-analysis', 
      label: 'Анализ документов', 
    },
    { 
      value: 'tasks', 
      label: 'Задачи', 
    },
    { 
      value: 'rainbow-analysis', 
      label: 'Радуга', 
    },
    { 
      value: 'all-analysis', 
      label: 'Все анализы (ZIP)', 
    }
  ];

  const dataTypeDescriptions: Record<SaveDataType, string> = {
    'detailed-report': 'Очищенный детальный отчет по судебной работе',
    'documents-report': 'Очищенный отчет по полученным и переданным документам',
    'lawsuit-production': 'Результаты анализа искового производства',
    'order-production': 'Результаты анализа приказного производства',
    'documents-analysis': 'Результаты анализа документов',
    'tasks': 'Рассчитанные задачи на основании анализов',
    'rainbow-analysis': 'Результаты цветовой классификации (радуга)',
    'all-analysis': 'Все виды анализа в одном ZIP-архиве'
  };

  // Загрузка статуса доступных данных при открытии модального окна
  useEffect(() => {
    if (isOpen) {
      loadAvailableDataStatus();
    }
  }, [isOpen]);

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

  // Функция загружает статус доступных данных
  const loadAvailableDataStatus = async () => {
    try {
      const status = await savingService.getAllProcessedDataStatus() as StatusResponse;
      if (status.success) {
        setAvailableData(status.status);
      }
    } catch (error) {
      console.error('Ошибка загрузки статуса данных:', error);
    }
  };

  // Функция выполняет сохранение выбранного типа данных
  const handleSave = async () => {
    if (!selectedType) return;

    try {
        setIsSaving(true);
        
        // Подготовка данных для скачивания
        const selectedOption = dataTypeOptions.find(opt => opt.value === selectedType);
        const isZip = selectedType === 'all-analysis';
        const extension = isZip ? 'zip' : 'xlsx';
        const fileName = `${selectedOption?.label || 'data'}.${extension}`;
        
        // Создание скрытой ссылки для скачивания
        const link = document.createElement('a');
        link.style.display = 'none';
        document.body.appendChild(link);
        
        // Запуск загрузки
        const blob = await savingService.saveData(selectedType);
        
        // Создание URL для скачивания
        const url = window.URL.createObjectURL(blob);
        link.href = url;
        link.download = fileName;
        
        // Автоматический запуск скачивания
        link.click();
        
        // Очистка ресурсов
        setTimeout(() => {
          window.URL.revokeObjectURL(url);
          document.body.removeChild(link);
        }, 100);
        
    } catch (error) {
        console.error('Ошибка загрузки файла:', error);
        alert('Ошибка при загрузке файла. Проверьте консоль для подробностей.');
    } finally {
        setIsSaving(false);
    }
  };

  // Функция получает информацию о статусе данных для выбранного типа
  const getDataStatusInfo = (type: SaveDataType) => {
    if (!availableData) return null;
    
    const statusMap: Record<SaveDataType, keyof AvailableDataStatus> = {
      'detailed-report': 'detailed_report',
      'documents-report': 'documents_report', 
      'lawsuit-production': 'lawsuit_production',
      'order-production': 'order_production',
      'documents-analysis': 'documents_analysis',
      'tasks': 'tasks',
      'rainbow-analysis': 'detailed_report', // rainbow использует detailed_report как основу
      'all-analysis': 'detailed_report' // all-analysis проверяет все типы
    };
    
    const statusKey = statusMap[type];
    return availableData[statusKey];
  };

  const handleTypeChange = (value: string) => {
    setSelectedType(value as SaveDataType);
  };

  const handleClearType = () => {
    setSelectedType(undefined);
  };

  const selectedOption = dataTypeOptions.find(opt => opt.value === selectedType);
  const statusInfo = getDataStatusInfo(selectedType);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div
        ref={modalRef}
        className="bg-white rounded-2xl p-6 max-w-2xl w-full relative"
        style={{
          border: '1px solid #BDBDCC',
          boxShadow: '2px 4px 8px rgba(0, 0, 0, 0.1), -2px 0 8px rgba(0, 0, 0, 0.05)'
        }}
      >
        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-full transition-colors"
          disabled={isSaving}
        >
          <X className="h-5 w-5" style={{ color: '#1F1F1F' }} />
        </button>

        {/* Заголовок */}
        <h2 className="text-xl font-semibold text-gray-900 mb-6 pr-8">
          Выгрузка данных
        </h2>

        {/* Выбор типа данных */}
        <div className="space-y-4 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Выберите тип данных для выгрузки:
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
            <div className="p-4 bg-gray-50 rounded-lg space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Описание:</p>
                <p className="text-sm text-gray-600">
                  {dataTypeDescriptions[selectedType]}
                </p>
              </div>
              
              {/* Статус доступности данных */}
              {statusInfo && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Статус данных:</p>
                  <div className="text-xs">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full ${
                      statusInfo.loaded 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {statusInfo.loaded 
                        ? `✓ Данные доступны (${statusInfo.row_count || 0} записей)`
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
            <p className="text-xs text-yellow-600">
              Выгрузка недоступна: данные не загружены
            </p>
          </div>
        )}

        {/* Информация о подключении */}
        <div className="mt-4 text-xs text-gray-500 text-center">
          Подключение к: http://localhost:8000
        </div>
      </div>
    </div>
  );
}