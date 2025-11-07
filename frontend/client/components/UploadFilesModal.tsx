// UploadFilesModal.tsx
import { useState, useEffect, useRef } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAnalysis } from "@/contexts/AnalysisContext";
import { API_ENDPOINTS } from "@/services/api/endpoints";
import { featureFlags } from '@/config/featureFlags';

type ModalKey = "currentReport" | "documentsReport" | "previousReport";

interface UploadFilesModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCalculate: () => void;
}

// Локальное состояние для отображения процесса загрузки, ошибок и имен файлов
type LocalFileState = Record<
  ModalKey,
  { name: string; loading: boolean; error: string | null }
>;

const initialLocalState: LocalFileState = {
  currentReport: { name: "", loading: false, error: null },
  documentsReport: { name: "", loading: false, error: null },
  previousReport: { name: "", loading: false, error: null }
};

// Соответствие ключей модального окна ключам бэкенда
const fileTypeToBackendKey: Record<ModalKey, string> = {
  currentReport: "current_detailed_report",
  documentsReport: "documents_report",
  previousReport: "previous_detailed_report"
};

export function UploadFilesModal({
  isOpen,
  onClose,
  onCalculate
}: UploadFilesModalProps) {
  const [localFiles, setLocalFiles] = useState<LocalFileState>(initialLocalState);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const modalRef = useRef<HTMLDivElement>(null);
  const { uploadedFiles, refreshFilesStatus } = useAnalysis();

  // Обновление статуса файлов при открытии модального окна
  useEffect(() => {
    if (isOpen) {
      refreshFilesStatus().catch(err => {
        console.warn('Не удалось обновить статус файлов при открытии модала:', err);
      });
    }
  }, [isOpen, refreshFilesStatus]);

  // Проверка загрузки обязательных файлов
  const requiredFilesUploaded =
    Boolean(uploadedFiles?.current_detailed_report?.loaded) &&
    Boolean(uploadedFiles?.documents_report?.loaded);

  // Функция получает путь к загруженному файлу
  const getUploadedFilePath = (fileType: ModalKey) => {
    const backendKey = fileTypeToBackendKey[fileType];
    return (uploadedFiles as any)?.[backendKey]?.filepath ?? "";
  };

  // Функция формирует отображаемое имя файла
  const getDisplayName = (fileType: ModalKey) => {
    const local = localFiles[fileType];
    if (local.name) return local.name;
    const path = getUploadedFilePath(fileType);
    if (path) {
      return path.split("/").pop() ?? path;
    }
    return "";
  };

  // Функция получает плейсхолдер для поля
  const getPlaceholder = (fileType: ModalKey) => {
    switch (fileType) {
      case "currentReport":
        return "Файл текущего детального отчета";
      case "documentsReport":
        return "Файл отчет по полученным и переданным документам";
      case "previousReport":
        return "Файл предыдущего детального отчета (опционально)";
    }
  };

  // Функция проверяет загружен ли файл
  const isUploaded = (fileType: ModalKey) => {
    const backendKey = fileTypeToBackendKey[fileType];
    return Boolean((uploadedFiles as any)?.[backendKey]?.loaded);
  };

  // Функция обрабатывает загрузку файла
  const handleFileUpload = async (fileType: ModalKey, event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Установка состояния загрузки
    setLocalFiles(prev => ({
      ...prev,
      [fileType]: { ...prev[fileType], name: file.name, loading: true, error: null }
    }));

    try {
      const backendFileType = fileTypeToBackendKey[fileType];
      const formData = new FormData();
      formData.append('file', file);

      const uploadUrl = `http://localhost:8000${API_ENDPOINTS.UPLOAD_FILE}?file_type=${backendFileType}`;
      const response = await fetch(uploadUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Ошибка загрузки: ${response.statusText}`);
      }

      await response.json();
      setLocalFiles(prev => ({
        ...prev,
        [fileType]: { ...prev[fileType], loading: false, error: null }
      }));
      await refreshFilesStatus();
    } catch (error) {
      console.error('Ошибка загрузки файла:', error);
      setLocalFiles(prev => ({
        ...prev,
        [fileType]: {
          ...prev[fileType],
          loading: false,
          error: error instanceof Error ? error.message : 'Неизвестная ошибка'
        }
      }));
    }
  };

  // Функция активирует скрытое поле ввода файла
  const triggerFileInput = (fileType: ModalKey) => {
    const input = document.getElementById(`file-input-${fileType}`) as HTMLInputElement;
    input?.click();
  };

  // Функция проверяет статус файлов на сервере
  const checkFilesStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/files-status');
      if (!response.ok) {
        throw new Error(`Ошибка проверки статуса: ${response.statusText}`);
      }
      const status = await response.json();
      return status;
    } catch (error) {
      console.error('Ошибка проверки статуса файлов:', error);
      throw error;
    }
  };

  // Функция запускает расчет после проверки файлов
  const handleCalculate = async () => {
    try {
      setUploadStatus('uploading');

      const status = await checkFilesStatus();

      if (status?.ready_for_analysis) {
        onClose();
        setTimeout(() => { onCalculate(); }, 100);
      } else {
        alert('Не все обязательные файлы загружены');
      }
    } catch (error) {
      alert('Ошибка при проверке статуса файлов');
    } finally {
      setUploadStatus('idle');
      await refreshFilesStatus();
    }
  };

  // Функция удаляет загруженный файл
  const handleRemove = async (fileType: ModalKey) => {
    try {
      const backendKey = fileTypeToBackendKey[fileType];
      const url = `http://localhost:8000/remove-file?file_type=${backendKey}`;
      const resp = await fetch(url, { method: 'DELETE' });
      if (!resp.ok) throw new Error('Ошибка удаления файла');

      setLocalFiles(prev => ({ ...prev, [fileType]: { name: '', loading: false, error: null } }));
      await refreshFilesStatus();
    } catch (err) {
      console.error('Ошибка удаления файла на сервере:', err);
    }
  };

  // Обработчики клика вне модального окна и нажатия Escape
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
        >
          <X className="h-5 w-5" style={{ color: '#1F1F1F' }} />
        </button>

        {/* Заголовок */}
        <h2 className="text-xl font-semibold text-gray-900 mb-6 pr-8">
          Загрузка файлов
        </h2>

        {/* Кнопки загрузки файлов */}
        <div className="space-y-6 mb-6">
          {/* Текущий отчет (обязательный) */}
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div 
                className={`flex-1 border-b border-gray-300 py-2 min-h-[40px] flex items-center
                  ${!isUploaded('currentReport') ? 
                    'cursor-pointer hover:border-green-500 transition-colors duration-200' : 
                    'cursor-default'}`}
                onClick={!isUploaded('currentReport') ? () => triggerFileInput('currentReport') : undefined}
              >
                {getDisplayName('currentReport') ? (
                  <span className="text-gray-900">✓ {getDisplayName('currentReport')}</span>
                ) : (
                  <span className="text-gray-400">{getPlaceholder('currentReport')}</span>
                )}
              </div>
              
              {!isUploaded('currentReport') ? (
                <Button
                  onClick={() => triggerFileInput('currentReport')}
                  variant="green"
                  size="rounded"
                  disabled={localFiles.currentReport.loading}
                >
                  {localFiles.currentReport.loading ? 'Загрузка...' : 'Загрузить'}
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button
                    onClick={() => triggerFileInput('currentReport')}
                    variant="grayOutline"
                    size="rounded"
                  >
                    Заменить
                  </Button>
                  <Button
                    onClick={async () => { await handleRemove('currentReport'); }}
                    variant="grayOutline"
                    size="rounded"
                  >
                    Удалить
                  </Button>
                </div>
              )}
              <input
                id="file-input-currentReport"
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={(e) => handleFileUpload('currentReport', e)}
              />
            </div>
            {localFiles.currentReport.error && (
              <p className="text-red-500 text-sm">Ошибка: {localFiles.currentReport.error}</p>
            )}
          </div>

          {/* Отчет по документам (обязательный) */}
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div 
                className={`flex-1 border-b border-gray-300 py-2 min-h-[40px] flex items-center
                  ${!isUploaded('documentsReport') ? 
                    'cursor-pointer hover:border-green-500 transition-colors duration-200' : 
                    'cursor-default'}`}
                onClick={!isUploaded('documentsReport') ? () => triggerFileInput('documentsReport') : undefined}
              >
                {getDisplayName('documentsReport') ? (
                  <span className="text-gray-900">✓ {getDisplayName('documentsReport')}</span>
                ) : (
                  <span className="text-gray-400">{getPlaceholder('documentsReport')}</span>
                )}
              </div>
              
              {!isUploaded('documentsReport') ? (
                <Button
                  onClick={() => triggerFileInput('documentsReport')}
                  variant="green"
                  size="rounded"
                  disabled={localFiles.documentsReport.loading}
                >
                  {localFiles.documentsReport.loading ? 'Загрузка...' : 'Загрузить'}
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button
                    onClick={() => triggerFileInput('documentsReport')}
                    variant="grayOutline"
                    size="rounded"
                  >
                    Заменить
                  </Button>
                  <Button
                    onClick={async () => { await handleRemove('documentsReport'); }}
                    variant="grayOutline"
                    size="rounded"
                  >
                    Удалить
                  </Button>
                </div>
              )}
              <input
                id="file-input-documentsReport"
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={(e) => handleFileUpload('documentsReport', e)}
              />
            </div>
            {localFiles.documentsReport.error && (
              <p className="text-red-500 text-sm">Ошибка: {localFiles.documentsReport.error}</p>
            )}
          </div>

          {/* Предыдущий отчет (опциональный) */}
          {featureFlags.enableComparison && (
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div 
                  className={`flex-1 border-b border-gray-300 py-2 min-h-[40px] flex items-center
                    ${!isUploaded('previousReport') ? 
                      'cursor-pointer hover:border-green-500 transition-colors duration-200' : 
                      'cursor-default'}`}
                  onClick={!isUploaded('previousReport') ? () => triggerFileInput('previousReport') : undefined}
                >
                  {getDisplayName('previousReport') ? (
                    <span className="text-gray-900">✓ {getDisplayName('previousReport')}</span>
                  ) : (
                    <span className="text-gray-400">{getPlaceholder('previousReport')}</span>
                  )}
                </div>
                
                {!isUploaded('previousReport') ? (
                  <Button
                    onClick={() => triggerFileInput('previousReport')}
                    variant="green"
                    size="rounded"
                    disabled={localFiles.previousReport.loading}
                  >
                    {localFiles.previousReport.loading ? 'Загрузка...' : 'Загрузить'}
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button
                      onClick={() => triggerFileInput('previousReport')}
                      variant="grayOutline"
                      size="rounded"
                    >
                      Заменить
                    </Button>
                    <Button
                      onClick={async () => { await handleRemove('previousReport'); }}
                      variant="grayOutline"
                      size="rounded"
                    >
                      Удалить
                    </Button>
                  </div>
                )}
                <input
                  id="file-input-previousReport"
                  type="file"
                  accept=".xlsx,.xls"
                  className="hidden"
                  onChange={(e) => handleFileUpload('previousReport', e)}
                />
              </div>
              {localFiles.previousReport.error && (
                <p className="text-red-500 text-sm">Ошибка: {localFiles.previousReport.error}</p>
              )}
            </div>
          )}
        </div>

        {/* Кнопка расчета */}
        {requiredFilesUploaded && (
          <div className="flex justify-center">
            <Button
              onClick={handleCalculate}
              variant="green"
              size="rounded"
              className="w-4/5"
            >
              Начать расчет
            </Button>
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