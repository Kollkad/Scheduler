// frontend/client/components/modals/DataExchangeModal.tsx

import { useState, useRef, useEffect } from "react";
import { X, Download, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TabsContainer } from "@/components/TabsContainer";
import { apiClient } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";

interface ExchangeMetadata {
  exported_at?: string;
  exported_by?: string;
  data_version?: string;
  files?: Record<string, { rows: number; columns: number }>;
}

interface ExchangeInfo {
  success: boolean;
  metadata: ExchangeMetadata;
  overrides_metadata: ExchangeMetadata;
}

interface DataExchangeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DataExchangeModal({ isOpen, onClose }: DataExchangeModalProps) {
  const [activeTab, setActiveTab] = useState<"export" | "import">("import");
  const [checkboxes, setCheckboxes] = useState({
    analysisData: false,
    taskOverrides: false,
    myOverrides: false,
  });
  const [exchangeInfo, setExchangeInfo] = useState<ExchangeInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  // Загрузка информации о данных в папке обмена при открытии
  useEffect(() => {
    if (isOpen) {
      loadExchangeInfo();
    }
  }, [isOpen]);

  // Сброс чекбоксов при смене вкладки
  useEffect(() => {
    setCheckboxes({ analysisData: false, taskOverrides: false, myOverrides: false });
  }, [activeTab]);

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

  // Загружает информацию о доступных данных из папки обмена
  const loadExchangeInfo = async () => {
    try {
      const response = await apiClient.get<ExchangeInfo>(API_ENDPOINTS.EXCHANGE_INFO);
      if (response.success) {
        setExchangeInfo(response);
      }
    } catch (error) {
      console.error('Ошибка загрузки информации обмена:', error);
    }
  };

  // Обработчик изменения чекбокса
  const handleCheckboxChange = (name: keyof typeof checkboxes) => {
    setCheckboxes(prev => ({ ...prev, [name]: !prev[name] }));
  };

  // Выполняет экспорт или импорт в зависимости от вкладки
  const handleAction = async () => {
    if (!hasSelection) return;

    setIsLoading(true);
    try {
      if (activeTab === "export") {
        // Экспорт
        if (checkboxes.analysisData) {
          await apiClient.post(API_ENDPOINTS.EXCHANGE_EXPORT_ALL);
        }
        if (checkboxes.taskOverrides) {
          await apiClient.post(API_ENDPOINTS.EXCHANGE_EXPORT_OVERRIDES);
        }
        if (checkboxes.myOverrides) {
          await apiClient.post(API_ENDPOINTS.EXCHANGE_EXPORT_MY_OVERRIDES);
        }
      } else {
        // Импорт
        if (checkboxes.analysisData) {
          await apiClient.post(API_ENDPOINTS.EXCHANGE_IMPORT_ALL);
        }
        if (checkboxes.taskOverrides) {
          await apiClient.post(API_ENDPOINTS.EXCHANGE_IMPORT_OVERRIDES);
        }
      }
      onClose();
    } catch (error) {
      console.error('Ошибка операции обмена:', error);
      alert('Ошибка при выполнении операции. Проверьте консоль для подробностей.');
    } finally {
      setIsLoading(false);
    }
  };

  const hasSelection = checkboxes.analysisData || checkboxes.taskOverrides || checkboxes.myOverrides;
  const isExport = activeTab === "export";

  // Форматирование даты из ISO строки
  const formatDate = (isoString?: string) => {
    if (!isoString) return "—";
    const date = new Date(isoString);
    return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  };

  // Формирование контента вкладок
  const tabs = [
    {
      id: "import",
      label: "Загрузка",
      content: (
        <div className="space-y-6">
          {/* Чекбоксы */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={checkboxes.analysisData}
                onChange={() => handleCheckboxChange('analysisData')}
                className="w-4 h-4 text-blue focus:ring-blue rounded"
              />
              <span className="text-sm text-text-primary">Загрузить данные анализа</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={checkboxes.taskOverrides}
                onChange={() => handleCheckboxChange('taskOverrides')}
                className="w-4 h-4 text-blue focus:ring-blue rounded"
              />
              <span className="text-sm text-text-primary">Загрузить ответы на задачи</span>
            </label>
          </div>

          {/* Инфо-блок */}
          {exchangeInfo && (
            <div className="p-4 bg-bg-default-light-field rounded-lg space-y-3">
              {(exchangeInfo.metadata?.exported_at || exchangeInfo.overrides_metadata?.exported_at) && (
                <>
                  {exchangeInfo.metadata?.exported_at && (
                    <div>
                      <p className="text-sm font-medium text-text-primary">Общие данные анализа:</p>
                      <p className="text-sm text-text-primary mt-1">
                        Дата выгрузки анализов: {formatDate(exchangeInfo.metadata.exported_at)}
                      </p>
                      <p className="text-sm text-text-primary">
                        Автор: {exchangeInfo.metadata.exported_by || "—"}
                      </p>
                    </div>
                  )}
                  {exchangeInfo.overrides_metadata?.exported_at && (
                    <div className={exchangeInfo.metadata?.exported_at ? "pt-3 border-t border-border" : ""}>
                      <p className="text-sm font-medium text-text-primary">Ответы на задачи:</p>
                      <p className="text-sm text-text-primary mt-1">
                        Дата выгрузки ответов: {formatDate(exchangeInfo.overrides_metadata.exported_at)}
                      </p>
                      <p className="text-sm text-text-primary">
                        Автор: {exchangeInfo.overrides_metadata.exported_by || "—"}
                      </p>
                    </div>
                  )}
                </>
              )}
              {!exchangeInfo.metadata?.exported_at && !exchangeInfo.overrides_metadata?.exported_at && (
                <p className="text-sm text-text-secondary">Нет данных для загрузки</p>
              )}
            </div>
          )}
        </div>
      )
    },
    {
      id: "export",
      label: "Выгрузка",
      content: (
        <div className="space-y-6">
          {/* Чекбоксы */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={checkboxes.analysisData}
                onChange={() => handleCheckboxChange('analysisData')}
                className="w-4 h-4 text-blue focus:ring-blue rounded"
              />
              <span className="text-sm text-text-primary">Выгрузить данные анализа</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={checkboxes.taskOverrides}
                onChange={() => handleCheckboxChange('taskOverrides')}
                className="w-4 h-4 text-blue focus:ring-blue rounded"
              />
              <span className="text-sm text-text-primary">Выгрузить ответы на задачи</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={checkboxes.myOverrides}
                onChange={() => handleCheckboxChange('myOverrides')}
                className="w-4 h-4 text-blue focus:ring-blue rounded"
              />
              <span className="text-sm text-text-primary">Выгрузить мои ответы на задачи</span>
            </label>
          </div>

          {/* Инфо-блок */}
          {exchangeInfo && (
            <div className="p-4 bg-bg-default-light-field rounded-lg space-y-3">
              {(exchangeInfo.metadata?.exported_at || exchangeInfo.overrides_metadata?.exported_at) && (
                <>
                  {exchangeInfo.metadata?.exported_at && (
                    <div>
                      <p className="text-sm font-medium text-text-primary">Общие данные анализа:</p>
                      <p className="text-sm text-text-primary mt-1">
                        Дата выгрузки анализов: {formatDate(exchangeInfo.metadata.exported_at)}
                      </p>
                      <p className="text-sm text-text-primary">
                        Автор: {exchangeInfo.metadata.exported_by || "—"}
                      </p>
                    </div>
                  )}
                  {exchangeInfo.overrides_metadata?.exported_at && (
                    <div className={exchangeInfo.metadata?.exported_at ? "pt-3 border-t border-border" : ""}>
                      <p className="text-sm font-medium text-text-primary">Ответы на задачи:</p>
                      <p className="text-sm text-text-primary mt-1">
                        Дата выгрузки ответов: {formatDate(exchangeInfo.overrides_metadata.exported_at)}
                      </p>
                      <p className="text-sm text-text-primary">
                        Автор: {exchangeInfo.overrides_metadata.exported_by || "—"}
                      </p>
                    </div>
                  )}
                </>
              )}
              {!exchangeInfo.metadata?.exported_at && !exchangeInfo.overrides_metadata?.exported_at && (
                <p className="text-sm text-text-secondary">Нет данных о предыдущих выгрузках</p>
              )}
            </div>
          )}
        </div>
      )
    }
  ];

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
          disabled={isLoading}
        >
          <X className="h-5 w-5 text-dark-default" />
        </button>

        {/* Заголовок */}
        <h2 className="text-xl font-semibold text-text-primary mb-6 pr-8">
          Обновление данных локально или в сетевой папке
        </h2>

        {/* Вкладки */}
        <div className="mb-6">
          <TabsContainer 
            tabs={tabs} 
            defaultTab="import"
            onTabChange={(tabId) => setActiveTab(tabId as "export" | "import")}
          />
        </div>

        {/* Кнопка действия */}
        <div className="flex justify-center">
          <Button
            variant="green"
            size="rounded"
            onClick={handleAction}
            disabled={isLoading || !hasSelection}
            className="w-4/5 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                {isExport ? "Выгрузка..." : "Загрузка..."}
              </>
            ) : (
              <>
                {isExport ? (
                  <Upload className="h-4 w-4" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                {isExport ? "Обновить в сетевой папке" : "Обновить локально"}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}


